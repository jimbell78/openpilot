# Test results: HYUNDAI_STARIA_4TH_GEN_NON_SCC (steering-only)

All tests were run on 2026-11-21 (Europe/Istanbul) against the code in this repository (`opendbc_repo/` = opendbc `68e48ca` on sunnypilot/opendbc `eaca1a8`). They were **not** run on a device or in the car. See "Not tested" below.

## Unit / safety tests

| Suite | Command (from `opendbc_repo/`) | Result |
|---|---|---|
| Full panda safety suite | `python -m unittest discover opendbc/safety/tests` | **9,821 ran, OK** (1,018 skipped) |
| Hyundai CAN-FD safety only | `python -m unittest opendbc.safety.tests.test_hyundai_canfd` | 3,083 OK |
| New non-SCC safety classes (`TestHyundaiCanfdLFASteeringNonSCC*`, 6 gas/EV/hybrid × bus variants) | | 474 OK |
| opendbc car tests | `python -m unittest discover opendbc/car` | 842 ran, OK (353 skipped) |
| sunnypilot car tests | `python -m unittest discover opendbc/sunnypilot` | 24 OK (after regenerating `car_list.json`) |
| MISRA C:2012 / cppcheck | `opendbc/safety/tests/misra/test_misra.sh` | Success (checker list unchanged) |
| Lint / types | ruff, ty, codespell (repo config), cpplint | pass |

What the new safety tests check:
- only 0x12A (LFA) and 0x1E0 (LFAHDA_CLUSTER) can be sent; 0x1A0, 0x1CF, 0x1AA and 0x160 are rejected even if added to the TX list
- 0x1AA buttons need a valid counter **and** checksum; 0x1A0 (SCC_CONTROL) is never parsed, even if spoofed
- lateral is allowed only by the MADS (LDA) button rising edge; `controls_allowed` (longitudinal) never becomes true
- longitudinal flag is forced off; unsupported combinations (non-SCC + LKA steering or + standard buttons) block all TX
- the standard steering torque limits, driver-torque override, brake/gas disengage and relay-malfunction checks are identical to the existing CAN-FD LFA mode (all inherited tests pass)

## Replay of Jim's two drives (2023 TR Staria, factory LFA camera)

Tool: `staria/tools/replay_staria.py`; full output in `staria/replay_staria_output.txt`. Raw logs are not included (they contain the VIN).

| Check | Parked log (61 s) | Drive log (60 s, 17–79 km/h) |
|---|---|---|
| Fingerprint / FW match | `HYUNDAI_STARIA_4TH_GEN_NON_SCC`, not dashcam; safety param 40 (CAMERA_SCC \| ALT_BUTTONS), SP param 8 (NON_SCC), longitudinal off | same |
| CarState `canValid` | false only in the first 2 warm-up frames | false only in the first 6 warm-up frames |
| LDA button | 2 real presses → 2 `lkas` button events | – |
| Cruise state | never available / enabled | never available / enabled |
| Brake / gas plausibility | – | brake ↔ −0.61 m/s² decel, gas ↔ +0.22 m/s², never both |

Panda safety (relay-open emulation, both logs):
- **0 rx-check failures** (counter / checksum / timing) over 179 safety ticks
- real LDA press → `controls_allowed_lateral`; `controls_allowed` never true; no relay malfunction
- CarController driven by MADS with the factory LFA torque as request: **21,768 / 21,768 TX frames accepted, 0 blocked** (0x12A and 0x1E0 only; 3,999 lateral-active frames in the drive)
- with "disengage on brake", lateral drops at the first brake press

## Re-run after vendoring tinygrad (2026-11-21, fresh clone of the branch)
Same results on a fresh `git clone --depth=1 --recurse-submodules` of this branch: opendbc car 842 OK, sunnypilot car 24 OK, safety 9,821 OK (non-SCC 474 OK), MISRA Success, ruff (root and opendbc) and ty clean, `compileall` OK, log replay output byte-identical, `scons -n` (PC) OK. `opendbc_repo/` and panda are unchanged by that commit.

Installer clone (same command as `installer.comma.ai`, simulated on a fast connection): before, the tinygrad submodule alone downloaded 1.66 GiB of history (checkout 3.6 GB, ~118 s, most of it at "90–92%"); after, the whole checkout is ~1.9 GB (of which ~0.9 GB are LFS model files) and took ~23 s.

## Not tested
- On-device build of this branch and any driving with openpilot steering. The EPS accepting openpilot's 0x12A is inferred from the factory frames and from other CAN-FD LFA cars.
- openpilot `process_replay` (needs a full device build and CI reference logs that don't exist for this car).
- steerRatio 17.5 (estimated from one 60 s segment) and the torque tune (substituted from the SCC Staria, not measured).
