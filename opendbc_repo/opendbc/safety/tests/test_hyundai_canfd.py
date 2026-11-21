#!/usr/bin/env python3
from opendbc.testing import parameterized_class
import unittest

from opendbc.car.hyundai.values import HyundaiSafetyFlags
from opendbc.sunnypilot.car.hyundai.values import HyundaiSafetyFlagsSP
from opendbc.car.structs import CarParams
import opendbc.safety.tests.common as common
from opendbc.safety.tests.libsafety import libsafety_py
from opendbc.safety.tests.hyundai_common import HyundaiButtonBase, HyundaiLongitudinalBase, Buttons, PREV_BUTTON_SAMPLES

# All combinations of radar/camera-SCC and gas/hybrid/EV cars
ALL_GAS_EV_HYBRID_COMBOS = [
  # Radar SCC
  {"GAS_MSG": ("ACCELERATOR_BRAKE_ALT", "ACCELERATOR_PEDAL_PRESSED"), "SCC_BUS": 0, "EXTRA_SAFETY_PARAM": 0},
  {"GAS_MSG": ("ACCELERATOR", "ACCELERATOR_PEDAL"), "SCC_BUS": 0, "EXTRA_SAFETY_PARAM": HyundaiSafetyFlags.EV_GAS},
  {"GAS_MSG": ("ACCELERATOR_ALT", "ACCELERATOR_PEDAL"), "SCC_BUS": 0, "EXTRA_SAFETY_PARAM": HyundaiSafetyFlags.HYBRID_GAS},
  # Camera SCC
  {"GAS_MSG": ("ACCELERATOR_BRAKE_ALT", "ACCELERATOR_PEDAL_PRESSED"), "SCC_BUS": 2, "EXTRA_SAFETY_PARAM": HyundaiSafetyFlags.CAMERA_SCC},
  {"GAS_MSG": ("ACCELERATOR", "ACCELERATOR_PEDAL"), "SCC_BUS": 2, "EXTRA_SAFETY_PARAM": HyundaiSafetyFlags.EV_GAS | HyundaiSafetyFlags.CAMERA_SCC},
  {"GAS_MSG": ("ACCELERATOR_ALT", "ACCELERATOR_PEDAL"), "SCC_BUS": 2, "EXTRA_SAFETY_PARAM": HyundaiSafetyFlags.HYBRID_GAS | HyundaiSafetyFlags.CAMERA_SCC},
]


class TestHyundaiCanfdBase(HyundaiButtonBase, common.CarSafetyTest, common.DriverTorqueSteeringSafetyTest, common.SteerRequestCutSafetyTest):

  DBC = "hyundai_canfd_generated"
  SAFETY_MODEL = CarParams.SafetyModel.hyundaiCanfd

  TX_MSGS = [[0x50, 0], [0x1CF, 1], [0x2A4, 0]]
  STANDSTILL_THRESHOLD = 12  # 0.375 kph
  FWD_BLACKLISTED_ADDRS = {2: [0x50, 0x2a4]}

  MAX_RATE_UP = 2
  MAX_RATE_DOWN = 3
  MAX_TORQUE_LOOKUP = [0], [270]

  MAX_RT_DELTA = 112

  DRIVER_TORQUE_ALLOWANCE = 250
  DRIVER_TORQUE_FACTOR = 2

  # Safety around steering req bit
  MIN_VALID_STEERING_FRAMES = 89
  MAX_INVALID_STEERING_FRAMES = 2

  PT_BUS = 0
  SCC_BUS = 2
  STEER_BUS = 0
  STEER_MSG = ""
  GAS_MSG = ("", "")
  BUTTONS_TX_BUS = 1

  def _torque_driver_msg(self, torque):
    values = {"MDPS_StrTqSnsrVal": torque}
    return self.packer.make_can_msg_safety("MDPS", self.PT_BUS, values)

  def _torque_cmd_msg(self, torque, steer_req=1):
    values = {"StrTqReqVal": torque, "ActToiSta": steer_req}
    return self.packer.make_can_msg_safety(self.STEER_MSG, self.STEER_BUS, values)

  def _speed_msg(self, speed):
    values = {f"WHL_Spd{pos}Val": speed * 0.03125 for pos in ["FL", "FR", "RL", "RR"]}
    return self.packer.make_can_msg_safety("WHEEL_SPEEDS", self.PT_BUS, values)

  def _user_brake_msg(self, brake):
    values = {"DriverBraking": brake}
    return self.packer.make_can_msg_safety("TCS", self.PT_BUS, values)

  def _user_gas_msg(self, gas):
    values = {self.GAS_MSG[1]: gas}
    return self.packer.make_can_msg_safety(self.GAS_MSG[0], self.PT_BUS, values)

  def _pcm_status_msg(self, enable):
    values = {"ACCMode": 1 if enable else 0}
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.SCC_BUS, values)

  def _button_msg(self, buttons, main_button=0, bus=None):
    if bus is None:
      bus = self.PT_BUS
    values = {
      "CRUISE_BUTTONS": buttons,
      "ADAPTIVE_CRUISE_MAIN_BTN": main_button,
    }
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS", bus, values)

  def _acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable}
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.SCC_BUS, values)

  def _lkas_button_msg(self, enabled):
    values = {"LDA_BTN": enabled}
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS", self.PT_BUS, values)

  def _main_cruise_button_msg(self, enabled):
    return self._button_msg(0, enabled)
class TestHyundaiCanfdLFASteeringBase(TestHyundaiCanfdBase):

  TX_MSGS = [[0x12A, 0], [0x1A0, 1], [0x1CF, 0], [0x1E0, 0]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x12A, 0x1E0)}  # LFA, LFAHDA_CLUSTER
  FWD_BLACKLISTED_ADDRS = {2: [0x12A, 0x1E0]}

  STEER_MSG = "LFA"
  BUTTONS_TX_BUS = 2
  EXTRA_SAFETY_PARAM: int

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ in ("TestHyundaiCanfdLFASteering", "TestHyundaiCanfdLFASteeringAltButtons"):
      cls.packer = None
      raise unittest.SkipTest

  @property
  def SAFETY_PARAM(self):
    return self.EXTRA_SAFETY_PARAM
@parameterized_class(ALL_GAS_EV_HYBRID_COMBOS)
class TestHyundaiCanfdLFASteering(TestHyundaiCanfdLFASteeringBase):
  pass
class TestHyundaiCanfdLFASteeringAltButtonsBase(TestHyundaiCanfdLFASteeringBase):

  EXTRA_SAFETY_PARAM: int

  @property
  def SAFETY_PARAM(self):
    return HyundaiSafetyFlags.CANFD_ALT_BUTTONS | self.EXTRA_SAFETY_PARAM

  def _button_msg(self, buttons, main_button=0, bus=1):
    values = {
      "CRUISE_BUTTONS": buttons,
      "ADAPTIVE_CRUISE_MAIN_BTN": main_button,
    }
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", self.PT_BUS, values)

  def _lkas_button_msg(self, enabled):
    values = {"LDA_BTN": enabled}
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", self.PT_BUS, values)

  def _acc_cancel_msg(self, cancel, accel=0):
    values = {"ACCMode": 4 if cancel else 0, "aReqRaw": accel, "aReqValue": accel}
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.PT_BUS, values)

  def test_button_sends(self):
    """
      No button send allowed with alt buttons.
    """
    for enabled in (True, False):
      for btn in range(8):
        self.safety.set_controls_allowed(enabled)
        self.assertFalse(self._tx(self._button_msg(btn)))

  def test_acc_cancel(self):
    # FIXME: the CANFD_ALT_BUTTONS cars are the only ones that use SCC_CONTROL to cancel, why can't we use buttons?
    for enabled in (True, False):
      self.safety.set_controls_allowed(enabled)
      self.assertTrue(self._tx(self._acc_cancel_msg(True)))
      self.assertFalse(self._tx(self._acc_cancel_msg(True, accel=1)))
      self.assertFalse(self._tx(self._acc_cancel_msg(False)))
@parameterized_class(ALL_GAS_EV_HYBRID_COMBOS)
class TestHyundaiCanfdLFASteeringAltButtons(TestHyundaiCanfdLFASteeringAltButtonsBase):
  pass

@parameterized_class(ALL_GAS_EV_HYBRID_COMBOS)
class TestHyundaiCanfdLFASteeringNonSCC(TestHyundaiCanfdLFASteeringAltButtonsBase):
  """
    Non-SCC CAN-FD LFA steering (e.g. radarless Hyundai Staria US4, no SCC_CONTROL 0x1A0 on any bus).
    - lateral only: never sends SCC_CONTROL, cruise buttons or ADRV messages
    - SCC_CONTROL is not required (not rx-checked) and is ignored if it ever shows up
    - controls_allowed is never set from cruise state; lateral is engaged only through MADS (LDA button)
    - all steering limits, driver torque, steer-req, rx counter/checksum and relay checks are inherited
  """

  TX_MSGS = [[0x12A, 0], [0x1E0, 0]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x12A, 0x1E0)}  # LFA, LFAHDA_CLUSTER
  FWD_BLACKLISTED_ADDRS = {2: [0x12A, 0x1E0]}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ == "TestHyundaiCanfdLFASteeringNonSCC":
      cls.packer = None
      raise unittest.SkipTest

  def setUp(self):
    libsafety_py.libsafety.set_current_safety_param_sp(HyundaiSafetyFlagsSP.NON_SCC)
    super().setUp()

  def tearDown(self):
    self.safety.set_current_safety_param_sp(0)

  def _acc_state_msg(self, enable):
    # no SCC_CONTROL / no main cruise state on non-SCC cars
    raise NotImplementedError

  def _scc_control_msg(self, bus, acc_mode=1, main_mode=1):
    values = {"ACCMode": acc_mode, "MainMode_ACC": main_mode}
    return self.packer.make_can_msg_safety("SCC_CONTROL", bus, values)

  def _accel_like_msg(self, accel):
    return self.packer.make_can_msg_safety("SCC_CONTROL", 0, {"aReqRaw": accel, "aReqValue": accel, "ACCMode": 1})

  def _init_non_scc(self, param, param_sp=HyundaiSafetyFlagsSP.NON_SCC):
    self.safety.set_current_safety_param_sp(param_sp)
    self.safety.set_safety_hooks(CarParams.SafetyModel.hyundaiCanfd, param)
    self.safety.init_tests()

  # *** cruise state: never sourced from SCC_CONTROL ***

  def test_enable_control_allowed_from_cruise(self):
    for main_button in (0, 1):
      for btn in range(8):
        for bus in (0, 1, 2):
          self.safety.set_controls_allowed(False)
          self._rx(self._button_msg(btn, main_button=main_button))
          self._rx(self._scc_control_msg(bus, acc_mode=0))
          self._rx(self._scc_control_msg(bus, acc_mode=1))
          self.assertFalse(self.safety.get_controls_allowed())
          self.assertFalse(self.safety.get_cruise_engaged_prev())

  def test_disable_control_allowed_from_cruise(self):
    # SCC_CONTROL is ignored entirely (it does not exist on these cars): it can neither enable nor disable
    self.safety.set_controls_allowed(True)
    self._rx(self._scc_control_msg(self.SCC_BUS, acc_mode=0))
    self.assertTrue(self.safety.get_controls_allowed())

  def test_sampling_cruise_buttons(self):
    self._rx(self._button_msg(Buttons.SET))
    for _ in range(2 * PREV_BUTTON_SAMPLES):
      self._rx(self._scc_control_msg(self.SCC_BUS, acc_mode=1))
      self.assertFalse(self.safety.get_controls_allowed())
      self._rx(self._button_msg(Buttons.NONE))

  def test_cruise_engaged_prev(self):
    for engaged in (True, False):
      self._rx(self._scc_control_msg(self.SCC_BUS, acc_mode=1 if engaged else 0))
      self.assertFalse(self.safety.get_cruise_engaged_prev())

  def test_scc_control_not_required_and_ignored(self):
    # the rx check list does not contain 0x1A0: the safety mode is fully valid without it,
    # and an SCC_CONTROL frame (even with MainMode_ACC set) changes no state
    for bus in (0, 1, 2):
      self._rx(self._scc_control_msg(bus))
    self.assertFalse(self.safety.get_acc_main_on())
    self.assertFalse(self.safety.get_cruise_engaged_prev())
    self.safety.set_unseen_rx_checks_valid()
    self.safety.set_controls_allowed(True)
    self.safety.safety_tick()
    self.assertTrue(self.safety.get_controls_allowed())

  # *** TX: lateral only ***

  def test_acc_cancel(self):
    for enabled in (True, False):
      for engaged in (True, False):
        self.safety.set_controls_allowed(enabled)
        self.safety.set_cruise_engaged_prev(engaged)
        for bus in (0, 1, 2):
          self.assertFalse(self._tx(self._acc_cancel_msg(True)))
          self.assertFalse(self._tx(self._scc_control_msg(bus, acc_mode=4, main_mode=0)))
          self.assertFalse(self._tx(self._scc_control_msg(bus)))

  def test_button_sends(self):
    for enabled in (True, False):
      for engaged in (True, False):
        self.safety.set_controls_allowed(enabled)
        self.safety.set_cruise_engaged_prev(engaged)
        for btn in range(8):
          for bus in (0, 1, 2):
            self.assertFalse(self._tx(self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", bus, {"CRUISE_BUTTONS": btn})))
            self.assertFalse(self._tx(self.packer.make_can_msg_safety("CRUISE_BUTTONS", bus, {"CRUISE_BUTTONS": btn})))

  def test_no_adrv_or_diagnostic_tx(self):
    self.safety.set_controls_allowed(True)
    for bus in (0, 1, 2):
      self.assertFalse(self._tx(self.packer.make_can_msg_safety("ADRV_0x160", bus, {})))
      self.assertFalse(self._tx(libsafety_py.make_CANPacket(0x7D0, bus, b"\x02\x3E\x80\x00\x00\x00\x00\x00")))

  def test_longitudinal_flag_ignored(self):
    # even if the LONG flag were set, the non-SCC mode never allows longitudinal or SCC_CONTROL
    self._init_non_scc(self.SAFETY_PARAM | HyundaiSafetyFlags.LONG)
    self.safety.set_controls_allowed(True)
    self.assertFalse(self._tx(self._accel_like_msg(0)))
    self.assertFalse(self._tx(self._accel_like_msg(1)))
    for btn in range(8):
      self.assertFalse(self._tx(self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", 1, {"CRUISE_BUTTONS": btn})))
    self.assertTrue(self._tx(self._torque_cmd_msg(0, steer_req=0)))

  def test_unsupported_configs_block_all_tx(self):
    for param in (self.SAFETY_PARAM & ~HyundaiSafetyFlags.CANFD_ALT_BUTTONS,
                  self.SAFETY_PARAM | HyundaiSafetyFlags.CANFD_LKA_STEER_MSG):
      with self.subTest(param=param):
        self._init_non_scc(param)
        self.safety.set_controls_allowed(True)
        self.safety.set_mads_params(True, False, False)
        self.safety.set_controls_allowed_lateral(True)
        self.assertFalse(self._tx(self._torque_cmd_msg(0, steer_req=0)))
        self.assertFalse(self._tx(self.packer.make_can_msg_safety("LFAHDA_CLUSTER", 0, {})))
        self.assertFalse(self._tx(self.packer.make_can_msg_safety("LKAS", 0, {})))

  # *** engagement: lateral only through MADS ***

  def test_lateral_only_via_mads_button(self):
    for enable_mads in (True, False):
      with self.subTest(enable_mads=enable_mads):
        self._init_non_scc(self.SAFETY_PARAM)
        self.safety.set_mads_params(enable_mads, False, False)
        self.safety.set_heartbeat_engaged_mads(True)
        self._rx(self._lkas_button_msg(False))
        self._rx(self._lkas_button_msg(True))
        self._rx(self._lkas_button_msg(False))
        self.assertEqual(enable_mads, self.safety.get_controls_allowed_lateral())
        self.assertFalse(self.safety.get_controls_allowed())
        self.assertFalse(self.safety.get_longitudinal_allowed())
        # steering is only allowed while lateral is engaged, and is still rate limited
        self.safety.set_desired_torque_last(0)
        self.safety.set_rt_torque_last(0)
        self.assertEqual(enable_mads, self._tx(self._torque_cmd_msg(self.MAX_RATE_UP, steer_req=1)))
        self.assertFalse(self._tx(self._torque_cmd_msg(self.MAX_RATE_UP * 4, steer_req=1)))

  def test_main_cruise_button_does_not_engage(self):
    self.safety.set_mads_params(True, False, False)
    for _ in range(3):
      self._rx(self._button_msg(0, main_button=1))
      self._rx(self._button_msg(0, main_button=0))
    for btn in range(8):
      self._rx(self._button_msg(btn))
    self.assertFalse(self.safety.get_acc_main_on())
    self.assertFalse(self.safety.get_controls_allowed())
    self.assertFalse(self.safety.get_controls_allowed_lateral())

  def test_mads_disengage_on_brake_while_moving(self):
    self.safety.set_mads_params(True, True, False)  # MADS with "pause lateral on brake"
    self._rx(self._lkas_button_msg(True))
    self._rx(self._lkas_button_msg(False))
    self.assertTrue(self.safety.get_controls_allowed_lateral())
    self._rx(self._speed_msg(10))
    self._rx(self._user_brake_msg(True))
    self.assertFalse(self.safety.get_controls_allowed_lateral())
    self.assertFalse(self._tx(self._torque_cmd_msg(1, steer_req=1)))

  # *** rx checks: the MADS button message is counter AND checksum checked ***

  def test_buttons_checksum_checked(self):
    self.assertTrue(self._rx(self._lkas_button_msg(True)))
    bad = self._lkas_button_msg(True)
    bad[0].data[0] ^= 0xFF
    self.assertFalse(self._rx(bad))

  def test_buttons_bad_checksum_does_not_engage(self):
    self.safety.set_mads_params(True, False, False)
    self._rx(self._lkas_button_msg(False))
    for _ in range(3):
      bad = self._lkas_button_msg(True)
      bad[0].data[0] ^= 0xFF
      self._rx(bad)
    self.assertFalse(self.safety.get_controls_allowed_lateral())


class TestHyundaiCanfdLKASteeringEV(TestHyundaiCanfdBase):

  SAFETY_PARAM = HyundaiSafetyFlags.CANFD_LKA_STEER_MSG | HyundaiSafetyFlags.EV_GAS

  TX_MSGS = [[0x50, 0], [0x1CF, 1], [0x2A4, 0]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x50, 0x2a4)}  # LKAS, CAM_0x2A4
  FWD_BLACKLISTED_ADDRS = {2: [0x50, 0x2a4]}

  PT_BUS = 1
  SCC_BUS = 1
  STEER_MSG = "LKAS"
  GAS_MSG = ("ACCELERATOR", "ACCELERATOR_PEDAL")
# TODO: Handle ICE and HEV configurations once we see cars that use the new messages
class TestHyundaiCanfdLKASteeringAltEV(TestHyundaiCanfdBase):

  SAFETY_PARAM = HyundaiSafetyFlags.CANFD_LKA_STEER_MSG | HyundaiSafetyFlags.EV_GAS | HyundaiSafetyFlags.CANFD_LKA_STEER_MSG_ALT

  TX_MSGS = [[0x110, 0], [0x1CF, 1], [0x362, 0]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x110, 0x362)}  # LKAS_ALT, CAM_0x362
  FWD_BLACKLISTED_ADDRS = {2: [0x110, 0x362]}

  PT_BUS = 1
  SCC_BUS = 1
  STEER_MSG = "LKAS_ALT"
  GAS_MSG = ("ACCELERATOR", "ACCELERATOR_PEDAL")
class HyundaiCanfdLKASteeringAltButtonsMixin:
  def _button_msg(self, buttons, main_button=0, bus=None):
    values = {
      "CRUISE_BUTTONS": buttons,
      "ADAPTIVE_CRUISE_MAIN_BTN": main_button,
    }
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", self.PT_BUS if bus is None else bus, values)

  def _lkas_button_msg(self, enabled):
    values = {"LDA_BTN": enabled}
    return self.packer.make_can_msg_safety("CRUISE_BUTTONS_ALT", self.PT_BUS, values)
class TestHyundaiCanfdLKASteeringAltButtonsHybrid(HyundaiCanfdLKASteeringAltButtonsMixin, TestHyundaiCanfdLKASteeringEV):

  SAFETY_PARAM = HyundaiSafetyFlags.CANFD_LKA_STEER_MSG | HyundaiSafetyFlags.HYBRID_GAS | HyundaiSafetyFlags.CANFD_ALT_BUTTONS

  TX_MSGS = [[0x50, 0], [0x1CF, 1], [0x2A4, 0], [0x1AA, 1]]
  GAS_MSG = ("ACCELERATOR_ALT", "ACCELERATOR_PEDAL")
class TestHyundaiCanfdLKASteeringAltAltButtonsHybrid(HyundaiCanfdLKASteeringAltButtonsMixin, TestHyundaiCanfdLKASteeringAltEV):

  SAFETY_PARAM = HyundaiSafetyFlags.CANFD_LKA_STEER_MSG | HyundaiSafetyFlags.HYBRID_GAS | HyundaiSafetyFlags.CANFD_LKA_STEER_MSG_ALT | \
                 HyundaiSafetyFlags.CANFD_ALT_BUTTONS

  TX_MSGS = [[0x110, 0], [0x1CF, 1], [0x362, 0], [0x1AA, 1]]
  GAS_MSG = ("ACCELERATOR_ALT", "ACCELERATOR_PEDAL")
class TestHyundaiCanfdLKASteeringLongEV(HyundaiLongitudinalBase, TestHyundaiCanfdLKASteeringEV):

  SAFETY_PARAM = HyundaiSafetyFlags.CANFD_LKA_STEER_MSG | HyundaiSafetyFlags.LONG | HyundaiSafetyFlags.EV_GAS

  TX_MSGS = [[0x50, 0], [0x1CF, 1], [0x2A4, 0], [0x51, 0], [0x730, 1], [0x12a, 1], [0x160, 1],
             [0x1e0, 1], [0x1a0, 1], [0x1ea, 1], [0x200, 1], [0x345, 1], [0x1da, 1]]

  RELAY_MALFUNCTION_ADDRS = {0: (0x50, 0x2a4), 1: (0x1a0,)}  # LKAS, CAM_0x2A4, SCC_CONTROL

  DISABLED_ECU_UDS_MSG = (0x730, 1)
  DISABLED_ECU_ACTUATION_MSG = (0x1a0, 1)

  STEER_MSG = "LFA"
  GAS_MSG = ("ACCELERATOR", "ACCELERATOR_PEDAL")
  STEER_BUS = 1

  def _accel_msg(self, accel, aeb_req=False, aeb_decel=0):
    values = {
      "aReqRaw": accel,
      "aReqValue": accel,
    }
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.PT_BUS, values)

  def _tx_acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable}
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.PT_BUS, values)
# Tests longitudinal for ICE, hybrid, EV cars with LFA steering
class TestHyundaiCanfdLFASteeringLongBase(HyundaiLongitudinalBase, TestHyundaiCanfdLFASteeringBase):

  FWD_BLACKLISTED_ADDRS = {2: [0x12a, 0x1e0, 0x1a0, 0x160]}

  RELAY_MALFUNCTION_ADDRS = {0: (0x12A, 0x1E0, 0x1a0, 0x160)}  # LFA, LFAHDA_CLUSTER, SCC_CONTROL, ADRV_0x160

  DISABLED_ECU_UDS_MSG = (0x7D0, 0)
  DISABLED_ECU_ACTUATION_MSG = (0x1a0, 0)

  @property
  def SAFETY_PARAM(self):
    return HyundaiSafetyFlags.LONG | self.EXTRA_SAFETY_PARAM

  def _accel_msg(self, accel, aeb_req=False, aeb_decel=0):
    values = {
      "aReqRaw": accel,
      "aReqValue": accel,
    }
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.PT_BUS, values)

  def _tx_acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable}
    return self.packer.make_can_msg_safety("SCC_CONTROL", self.PT_BUS, values)

  def test_tester_present_allowed(self, ecu_disable: bool = True):
    super().test_tester_present_allowed(ecu_disable=not self.EXTRA_SAFETY_PARAM & HyundaiSafetyFlags.CAMERA_SCC)
@parameterized_class(ALL_GAS_EV_HYBRID_COMBOS)
class TestHyundaiCanfdLFASteeringLong(TestHyundaiCanfdLFASteeringLongBase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ == "TestHyundaiCanfdLFASteeringLong":
      raise unittest.SkipTest
@parameterized_class(ALL_GAS_EV_HYBRID_COMBOS)
class TestHyundaiCanfdLFASteeringLongAltButtons(TestHyundaiCanfdLFASteeringLongBase, TestHyundaiCanfdLFASteeringAltButtonsBase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ == "TestHyundaiCanfdLFASteeringLongAltButtons":
      raise unittest.SkipTest

  @property
  def SAFETY_PARAM(self):
    return HyundaiSafetyFlags.LONG | HyundaiSafetyFlags.CANFD_ALT_BUTTONS | self.EXTRA_SAFETY_PARAM

  def test_acc_cancel(self):
    # Alt buttons does not use SCC_CONTROL to cancel if longitudinal
    pass


CAMERA_SCC_COMBOS = [c for c in ALL_GAS_EV_HYBRID_COMBOS if c["EXTRA_SAFETY_PARAM"] & HyundaiSafetyFlags.CAMERA_SCC]


@parameterized_class(CAMERA_SCC_COMBOS)
class TestHyundaiCanfdLFASteeringCCNC(TestHyundaiCanfdLFASteeringBase):

  TX_MSGS = [[0x12A, 0], [0x1E0, 0], [0x1CF, 2], [0x161, 0], [0x162, 0], [0xEA, 2]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x12A, 0x1E0, 0x161, 0x162), 2: (0xEA,)}
  FWD_BLACKLISTED_ADDRS = {0: [0xEA], 2: [0x12A, 0x1E0, 0x161, 0x162]}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ == "TestHyundaiCanfdLFASteeringCCNC":
      cls.packer = None
      raise unittest.SkipTest

  def setUp(self):
    libsafety_py.libsafety.set_current_safety_param_sp(HyundaiSafetyFlagsSP.CCNC)
    super().setUp()

  def tearDown(self):
    self.safety.set_current_safety_param_sp(0)

  def test_ccnc_tx_msgs(self):
    for msg, bus in (("CCNC_0x161", 0), ("CCNC_0x162", 0), ("MDPS", 2)):
      self.assertTrue(self._tx(self.packer.make_can_msg_safety(msg, bus, {})))


@parameterized_class(CAMERA_SCC_COMBOS)
class TestHyundaiCanfdLFASteeringCCNCLong(TestHyundaiCanfdLFASteeringLongBase, TestHyundaiCanfdLFASteeringCCNC):

  TX_MSGS = [[0x12A, 0], [0x1E0, 0], [0x1CF, 2], [0x1A0, 0], [0x161, 0], [0x162, 0], [0xEA, 2]]
  RELAY_MALFUNCTION_ADDRS = {0: (0x12A, 0x1E0, 0x1A0, 0x161, 0x162), 2: (0x1CF, 0xEA)}
  FWD_BLACKLISTED_ADDRS = {0: [0x1CF, 0xEA], 2: [0x12A, 0x1E0, 0x1A0, 0x161, 0x162]}

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    if cls.__name__ == "TestHyundaiCanfdLFASteeringCCNCLong":
      cls.packer = None
      raise unittest.SkipTest

  def test_button_sends(self):
    for btn in range(8):
      for main_btn in (0, 1):
        self.assertTrue(self._tx(self._button_msg(btn, main_button=main_btn, bus=self.BUTTONS_TX_BUS)))


if __name__ == "__main__":
  unittest.main()
