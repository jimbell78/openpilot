# Staria Non-SCC (TR, 2023) – steering-only sunnypilot port: design, tests, open items

Prepared 2026-11-21 (Europe/Istanbul).

## What is in this repository

| Part | Based on | Port changes |
|---|---|---|
| repository root | sunnypilot/sunnypilot master @ `a4f7d05` | no code changes in sunnypilot itself; opendbc is vendored; docs added; upstream `.github/workflows` removed so sunnypilot's CI does not run on this fork |
| `tinygrad_repo/` (vendored, plain files, not a submodule) | sunnypilot/tinygrad @ `92b742f` (the commit sunnypilot `a4f7d05` pins) | none; vendored so installs don't download tinygrad's ~1.7 GB history. Excluded from LFS in `.gitattributes` |
| `opendbc_repo/` (vendored, plain files, not a submodule) | sunnypilot/opendbc @ `eaca1a8` | opendbc commits `1437597` (fingerprint + platform) and `68e48ca` (safety mode + lateral-only port), exported with `git archive 68e48ca` |

The other submodules (panda, msgq, rednose, teleoprtc, neural_network_data) are unchanged and point to their public upstream repositories at the commits sunnypilot `a4f7d05` pins. Panda firmware safety code is compiled from `opendbc_repo/opendbc/safety`, so the safety changes below are what the device flashes.

Tools in `staria/tools/` (`logcan.py`, `dump_can.py`, `replay_staria.py`) were used for the log replay; their output is in `staria/replay_staria_output.txt`. Jim's raw logs are not included (they contain the VIN).

Files changed in opendbc (`68e48ca`):
- `opendbc/safety/modes/hyundai_canfd.h` – new non-SCC config (see below)
- `opendbc/safety/modes/hyundai_common.h` – CRC16 final XOR for 16-byte CAN-FD frames (0x041D)
- `opendbc/safety/tests/test_hyundai_canfd.py` – `TestHyundaiCanfdLFASteeringNonSCC` (6 gas/EV/hybrid × camera/radar-bus variants)
- `opendbc/car/hyundai/values.py` – `HYUNDAI_STARIA_4TH_GEN_NON_SCC` gets `sp_flags=HyundaiFlagsSP.NON_SCC`, `steerRatio=17.5`
- `opendbc/car/hyundai/interface.py` – dashcamOnly removed; long off; NON_SCC SP safety param; `radarUnavailable`; fail-safe to dashcam if the bus does not look like Jim's car
- `opendbc/car/hyundai/carstate.py`, `opendbc/sunnypilot/car/hyundai/mads.py` – no SCC_CONTROL reads; cruise unavailable/disengaged
- `opendbc/car/hyundai/carcontroller.py` – no SCC cancel / button sends for NON_SCC
- `opendbc/car/hyundai/tests/test_hyundai.py` – params/fail-safe test, NON_SCC exclusions
- `opendbc/sunnypilot/car/car_list.json` – regenerated (car now selectable/listed)

## Safety design (panda, `hyundaiCanfd` + SP param `NON_SCC`=8)

Modeled on sunnypilot's CAN non-SCC handling (sunnypilot/opendbc#221: same `HYUNDAI_PARAM_SP_NON_SCC` bit, which the CAN-FD mode previously ignored).

| Aspect | Existing CAN-FD LFA, camera-SCC, stock long (closest existing mode) | New non-SCC mode |
|---|---|---|
| RX checks (counter + CRC16) | 0x35/0x100/0x105 (gas), 0x175 (brake), 0xA0 (speed), 0xEA (driver torque); 0x1AA counter only (**checksum ignored**); 0x1A0 SCC_CONTROL | same gas/brake/speed/torque checks; **0x1AA counter + checksum**; no 0x1A0 (does not exist on the car) |
| How controls get allowed | cruise state from 0x1A0 (+ recent button), MADS button, acc_main | **only** MADS button rising edge (LDA_BTN, bit 39 of 0x1AA) with MADS enabled; `controls_allowed` is never set (no cruise source); 0x1A0 is never parsed even if spoofed |
| TX allowlist | 0x1CF (bus 2), 0x12A, 0x1E0, 0x1A0 (cancel), 0x160 | **0x12A LFA + 0x1E0 LFAHDA_CLUSTER only** (both relay-checked) |
| Explicit TX blocks | – | 0x1A0, 0x1CF, 0x1AA, 0x160 rejected in the tx hook even if the list changed |
| Longitudinal | possible with LONG flag (debug builds) | LONG flag forced off; no accel message can pass |
| Unsupported combos | – | NON_SCC + LKA steering or + standard buttons → **all TX blocked** |
| Steering limits | max 270, rt delta 112, up 2 / down 3, driver allowance 250 ×2, steer-req cut 89/2 frames, 810 ms | **identical** (same tx-hook code path) |
| Brake/gas/driver override | generic + MADS (brake → disengage/pause per setting, lag/rx-invalid exits, heartbeat mismatch) | identical |

Why it is no less strict: every check of the existing path still runs; the only removed element is the SCC_CONTROL rx check, whose sole purpose is to provide cruise state for engagement – and the new mode has *no* cruise-based engagement at all (engagement surface is a strict subset: MADS button only). The button message that now gates engagement got a stronger check (checksum added). TX surface shrinks from 5 to 2 messages. The 16-byte checksum XOR is only used by the new 0x1AA check (every other 16-byte rx check in hyundaiCanfd has `ignore_checksum`), so no existing mode changes behaviour.

The CRC XOR (0x041D) matches the opendbc packer (`hkg_can_fd_checksum`) and **all** 0x1AA/0x12A/0x1E0/0x125/0x160/0x11A frames in both of Jim's logs (0 failures, ~12k frames).

## openpilot/sunnypilot side
- Engagement: sunnypilot MADS (`Mads` param, default on). `allow_always` is already true for CAN-FD Hyundai, so the steering-wheel lane-assist (LDA) button toggles lateral without main cruise. `cruiseState.available/enabled` are always False (consistent with the panda, which never sees acc_main_on) → no automatic engage on startup, no SCC cancel spam, no cruise speed.
- Long: `openpilotLongitudinalControl=False`, `alphaLongitudinalAvailable=False`, LONG safety bit cleared, `radarUnavailable=True` (otherwise the radar ext would wait for SCC_CONTROL and raise radar faults).
- Fail-safe gating: `HYUNDAI_STARIA_4TH_GEN_NON_SCC` only exact-FW-matches the TR camera `US4 MFC AT EUR LHD 1.00 1.04 99211-CG000 210819` (CAN-FD non-EV cars are excluded from fuzzy fingerprinting). If that car shows 0x1A0 (an SCC Staria sharing the camera FW), LKA steering (0x50/0x110 from camera), CCNC, or the standard 0x1CF buttons, it is forced to **dashcam**.

## steerRatio decision: 17.5
- Upstream `HYUNDAI_STARIA_4TH_GEN` uses 11.94, which is the spec sheet's turning circle (11.94 m), not a ratio.
- From Jim's factory-LFA drive rlog (60 s, 17–79 km/h): STEERING_SENSORS angle vs. IMU yaw rate (0x4A) / wheel speed, wheelbase 3.273 m, |a_y| < 2.5 m/s², steady state: 18.4–19.6 (pure Ackermann) and 16.7–18.0 with an understeer term (K ≈ 0.0013–0.002 s²/m²).
- Spec sheet cross-check: 3.41 turns lock-to-lock and an 11.94 m turning circle give ≈ 18.5.
- I picked 17.5: openpilot's vehicle model handles understeer separately, so the geometric ratio fits it. paramsd learns the real value online. The value is still an estimate from one 60 s segment.
- Torque params (latAccelFactor/friction) come from the `substitute.toml` mapping to `HYUNDAI_STARIA_4TH_GEN` (SCC Staria). **Flagged: substitute data, not measured on this car**; torqued learns online.

## Test results (all local, 2026-11-21)
- opendbc car tests: `unittest discover opendbc/car` → **842 ran, OK** (353 skipped)
- sunnypilot car tests: `unittest discover opendbc/sunnypilot` → **24 OK** (after regenerating car_list.json)
- safety: full `opendbc/safety/tests` → **9821 ran, OK** (1018 skipped); `test_hyundai_canfd` alone 3083 OK; new non-SCC classes 474 OK
- MISRA C:2012 / cppcheck (`test_misra.sh`, exhaustive, checkers list unchanged): **Success**
- ruff, ty (type check), codespell (repo config), cpplint: pass
- Log replay (`staria/tools/replay_staria.py`, output in `staria/replay_staria_output.txt`):
  - fingerprint + FW → `HYUNDAI_STARIA_4TH_GEN_NON_SCC`, not dashcam, hyundaiCanfd param 40 (CAMERA_SCC|ALT_BUTTONS), SP param 8 (NON_SCC), long off
  - CarState: canValid true after the 2–6 warm-up frames, for the whole parked (61 s) and drive (60 s) segments; gear P/D, brake and gas plausible (brake ↔ decel −0.61 m/s², gas ↔ +0.22 m/s², never both); real LDA presses → 2 `lkas` button events; cruise never available/enabled; accFaulted never
  - panda (relay-open emulation): 0 rx-check failures (counters/checksums/timing) over 179 safety ticks; real LDA press → `controls_allowed_lateral`; `controls_allowed` never true; no relay malfunction
  - CarController driven by MADS + the factory LFA torque as request: **21,768/21,768 TX frames accepted, 0 blocked** by the panda across the 3 replays (0x12A + 0x1E0 only; 3999 lateral-active frames in the drive); with "disengage on brake", lateral drops at the first brake press
- Not run: openpilot process_replay (needs a full device build and CI reference logs for this car, which don't exist); on-device test.

## What remains unverified
1. **Real steering on the car.** The MDPS accepting openpilot's 0x12A (with the camera's frame blocked) is only inferred from the factory LFA frames and from other CAN-FD LFA cars. The EPS fault behaviour (e.g., the 89-frame steer-req cut) has not been seen on this car.
2. Camera/cluster reaction to losing its 0x12A/0x1E0 frames (LFA warnings, FCA/AEB still from the camera, since its other messages are forwarded) has not been seen.
3. steerRatio (17.5) and the substitute torque tune.
4. Regular-cruise status/buttons: never used in the logs. The car's own cruise keeps working (it is not touched), but openpilot shows no set speed.
5. LDA_BTN semantics while driving (only seen parked). Whether the factory lane-assist toggling interferes with MADS is unknown.
6. A European/other-market *SCC* Staria with the same camera FW: guarded to dashcam by the 0x1A0 check, but this has not been tested on such a car.
7. Whether the device builds cleanly from this master-based branch (not prebuilt). The opendbc/panda code was tested, but the full sunnypilot build was not run here.
8. Install via `installer.comma.ai/jimbell78/staria-tr-3x` or SSH + git clone (see INSTALL.md); neither has been run on a device yet.
