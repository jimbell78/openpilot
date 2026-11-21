#!/usr/bin/env python3
"""
Replay Jim's Staria CAN logs through the staria-tr-3x opendbc port:
  1. fingerprint + FW -> CarParams / CarParamsSP (must pick HYUNDAI_STARIA_4TH_GEN_NON_SCC, not dashcam)
  2. CarState (canValid, gear, speeds, buttons, cruise state, MADS lkas button events)
  3. CarController output (driven by an emulated MADS engagement using the factory LFA torque as the request)
  4. panda safety (libsafety, hyundaiCanfd + NON_SCC): rx checks valid, MADS engagement, every TX accepted
The logs were recorded with the relay CLOSED (bus 0 == bus 2), so for the safety replay the camera's own
LFA/LFAHDA frames (0x12A/0x1E0) are removed from bus 0, which is what the panda sees with the harness relay open.
"""
import os
import pickle
import collections
import numpy as np
from opendbc.car import structs, gen_empty_fingerprint
from opendbc.car.car_helpers import interfaces
from opendbc.car.fw_versions import match_fw_to_car
from opendbc.car.hyundai.hyundaicanfd import hkg_can_fd_checksum
from opendbc.car.hyundai.values import CarControllerParams
from opendbc.safety.tests.libsafety import libsafety_py

CAMERA_FW = b'\xf1\x00US4 MFC  AT EUR LHD 1.00 1.04 99211-CG000 210819'
EPS_FW = None  # not needed for the match
DT = 0.01


def inject_lda(frames, press):
  if not press:
    return frames
  out = []
  for a, d, s in frames:
    if a == 0x1aa:
      d = bytearray(d)
      d[4] |= 0x80  # LDA_BTN (bit 39)
      c = hkg_can_fd_checksum(a, None, d)
      d[0], d[1] = c & 0xff, c >> 8
      d = bytes(d)
    out.append((a, d, s))
  return out


def main(name, inject_press_at=None, mads_brake_mode=(False, False)):
  log = pickle.load(open(os.path.join(os.environ.get('STARIA_PKL_DIR', '.'), f'{name}.pkl'), 'rb'))['can']
  t0 = log[0][0]

  # --- fingerprint (first 1 s like card.py) + FW match ---
  fingerprint = gen_empty_fingerprint()
  for t, frames in log:
    if t - t0 > 1e9:
      break
    for a, d, s in frames:
      if s < 4 and a < 0x800:
        fingerprint[s][a] = len(d)
  car_fw = [structs.CarParams.CarFw(ecu="fwdCamera", fwVersion=CAMERA_FW, address=0x7c4, subAddress=0, brand="hyundai")]
  exact, matches = match_fw_to_car(car_fw, "0" * 17, allow_fuzzy=False)  # VIN redacted (not used by Hyundai matching)
  assert matches == {"HYUNDAI_STARIA_4TH_GEN_NON_SCC"}, matches
  candidate = "HYUNDAI_STARIA_4TH_GEN_NON_SCC"
  CI = interfaces[candidate]
  CP = CI.get_params(candidate, fingerprint, car_fw, False, False, False)
  CP_SP = CI.get_params_sp(CP, candidate, fingerprint, car_fw, False, False, False)
  ci = CI(CP, CP_SP)
  sc = CP.safetyConfigs[-1]
  print(" ".join([
    f"== {name}: candidate={CP.carFingerprint} dashcamOnly={CP.dashcamOnly} long={CP.openpilotLongitudinalControl}",
    f"pcmCruise={CP.pcmCruise} radarUnavailable={CP.radarUnavailable} steerRatio={CP.steerRatio}",
    f"safety={sc.safetyModel} param={sc.safetyParam} spParam={CP_SP.safetyParam} spFlags={CP_SP.flags}",
    f"lateralTuning={CP.lateralTuning.which()}",
  ]))

  # --- panda safety ---
  safety = libsafety_py.libsafety
  safety.set_current_safety_param_sp(CP_SP.safetyParam)
  assert str(sc.safetyModel) == "hyundaiCanfd", sc.safetyModel
  assert safety.set_safety_hooks(structs.CarParams.SafetyModel.hyundaiCanfd, sc.safetyParam) == 0
  safety.init_tests()
  safety.set_mads_params(True, *mads_brake_mode)
  safety.set_heartbeat_engaged_mads(True)

  stats = collections.Counter()
  can_invalid_frames, first_invalid = 0, None
  mads_enabled = False
  lat_hist = []
  stock_torque = 0
  rx_invalid_ticks = 0
  last_tick = t0
  for i, (t, frames) in enumerate(log):
    press = inject_press_at is not None and inject_press_at <= (t - t0) / 1e9 < inject_press_at + 0.1
    frames = inject_lda(frames, press)
    for a, d, s in frames:
      if a == 0x12a and s == 2:
        stock_torque = (((d[6] & 0xF) << 7) | (d[5] >> 1)) - 1024
    # car state
    CS, CS_SP = ci.update([(t, frames)])
    if not CS.canValid:
      can_invalid_frames += 1
      if first_invalid is None and i > 100:
        first_invalid = (t - t0) / 1e9
    for be in CS.buttonEvents:
      stats[f"buttonEvent.{be.type}.{'pressed' if be.pressed else 'released'}"] += 1
      if be.type == structs.CarState.ButtonEvent.Type.lkas and be.pressed:
        mads_enabled = not mads_enabled  # sunnypilot MADS: allow_always for CAN-FD hyundai
    stats[f"cruise.available={CS.cruiseState.available}"] += 1
    stats[f"cruise.enabled={CS.cruiseState.enabled}"] += 1
    stats[f"gear={CS.gearShifter}"] += 1
    stats[f"accFaulted={CS.accFaulted}"] += 1
    if CS.brakePressed:
      stats["brakePressed"] += 1
    if CS.gasPressed:
      stats["gasPressed"] += 1

    # panda rx (relay open emulation)
    safety.set_timer(int((t - t0) / 1e3) & 0xFFFFFFFF)
    for a, d, s in frames:
      if s == 0 and a in (0x12a, 0x1e0):
        continue
      if s in (0, 2):
        if not safety.safety_rx_hook(libsafety_py.make_CANPacket(a, s, d)):
          stats[f"safety.rx_invalid.{hex(a)}.bus{s}"] += 1
    if t - last_tick > 1e9:
      allowed_lat = safety.get_controls_allowed_lateral()
      safety.set_controls_allowed(True)
      safety.safety_tick()
      if not safety.get_controls_allowed():
        rx_invalid_ticks += 1
      safety.set_controls_allowed(False)
      last_tick = t
      stats["safety_ticks"] += 1
      assert safety.get_controls_allowed_lateral() == allowed_lat or not allowed_lat

    panda_lat = safety.get_controls_allowed_lateral()
    # emulated selfdrived: MADS lateral active when enabled, moving forward in D, panda agrees
    lat_active = mads_enabled and panda_lat and CS.vEgo > CP.minSteerSpeed and str(CS.gearShifter) == "drive"
    lat_hist.append(lat_active)

    CC = structs.CarControl()
    CC.enabled = False
    CC.latActive = lat_active
    CC.actuators.torque = float(np.clip(stock_torque / CarControllerParams(CP).STEER_MAX, -1, 1)) if lat_active else 0.
    CC_SP = structs.CarControlSP()
    CC_SP.mads.available = True
    CC_SP.mads.enabled = mads_enabled
    _, sends = ci.apply(CC.as_reader(), CC_SP, t)
    for a, d, s in sends:
      ok = safety.safety_tx_hook(libsafety_py.make_CANPacket(a, s, d))
      stats[f"tx.{hex(a)}.bus{s}.{'ok' if ok else 'BLOCKED'}" + (".lat" if lat_active else "")] += 1

  print(f"frames={len(log)} canValid false frames={can_invalid_frames} (first after warmup at {first_invalid}s)")
  print("  ".join([
    f"safety rx-check invalid ticks={rx_invalid_ticks}/{stats['safety_ticks']}",
    f"lat_active frames={sum(lat_hist)}",
    f"final panda lat={safety.get_controls_allowed_lateral()} controls_allowed(full)={safety.get_controls_allowed()}"
    + f" relay_malfunction={safety.get_relay_malfunction()}",
  ]))
  for k in sorted(stats):
    print(f"  {k}: {stats[k]}")
  return stats


if __name__ == "__main__":
  main("parked")
  main("drive", inject_press_at=20.0)
  main("drive", inject_press_at=20.0, mads_brake_mode=(True, False))
