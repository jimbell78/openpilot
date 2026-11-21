# staria-pilot

**Steering-only sunnypilot port for the 2023 Hyundai Staria (Turkish/European market, no radar, no BSM, no factory smart cruise).**

> ## ⚠️ Safety warning: read before use
> This is an **experimental, unofficial** port that has passed simulation and log replay but has **not yet been driven** with openpilot steering. It is a driver-assistance system, not self-driving.
> - **You must stay fully attentive with your hands on the wheel at all times** and be ready to take over instantly.
> - It **only steers**. It never brakes, accelerates, or slows for curves, cars, or anything else. Speed is entirely yours (pedals or the car's own cruise control).
> - Do not disable, bypass, or raise any panda safety check or torque limit, and do not defeat driver monitoring.
> - You are responsible for the vehicle and for complying with local law. Use at your own risk.

## What this is
- A fork of [sunnypilot](https://github.com/sunnypilot/sunnypilot) (master `a4f7d05`), which is itself based on [openpilot](https://github.com/commaai/openpilot) by comma.ai.
- Adds the car `HYUNDAI_STARIA_4TH_GEN_NON_SCC` ("Hyundai Staria Non-SCC 2023") and a new **non-SCC CAN-FD panda safety configuration**. Details: [PORT_NOTES.md](PORT_NOTES.md).
- **Lateral (steering) control only, no longitudinal control.** Engage/disengage steering with the steering-wheel lane-assist (LDA) button via sunnypilot MADS.
- Lateral tune: steerRatio **17.5** (measured from a real drive), torque values substituted from the Korean/SCC `HYUNDAI_STARIA_4TH_GEN`. Both are learned online by paramsd/torqued.
- Self-contained: `opendbc_repo/` is vendored as plain files (it contains the car port and the panda safety code). The other submodules point to public upstream repositories.

Branch: **`staria-tr-3x`**

## Hardware
- **comma 3X** (built-in panda)
- **Hyundai K harness**
- 2023 Staria with factory LFA/LKA camera `99211-CG000` (`US4 MFC AT EUR LHD 1.00 1.04`). Other variants (SCC, LKA-steering, CCNC) are detected and kept in **dashcam mode**.

## Panda safety summary
- Transmits only **0x12A (LFA)** and **0x1E0 (LFA/HDA cluster)**. Cruise/button/SCC messages (0x1A0, 0x1CF, 0x1AA, 0x160) are explicitly blocked.
- Longitudinal is forced off. Lateral is allowed only by the LDA button (button message checked for counter **and** checksum).
- Steering torque limits, driver override, brake/gas disengage, and relay checks are **identical** to sunnypilot's existing CAN-FD LFA mode. Nothing is relaxed.

## Install (comma 3X)
The comma "Custom Software" URL **cannot** install this repo: the web installers only clone repos named `openpilot` (`installer.comma.ai/<user>/<branch>`) or `sunnypilot` (`install.sunnypilot.ai/fork/<user>/<branch>`). Install over SSH instead:

```bash
ssh comma@<device-ip>
cd /data && mv openpilot openpilot.bak
git clone --recurse-submodules --depth=1 -b staria-tr-3x https://github.com/jimbell78/staria-pilot.git openpilot
cd openpilot && git lfs pull && sudo reboot
```
The first boot compiles for 10–20+ minutes. Full steps (enabling SSH, GitHub keys, rollback, settings): **[INSTALL.md](INSTALL.md)**.

## First drive (summary)
Full list: **[FIRST_DRIVE_CHECKLIST.md](FIRST_DRIVE_CHECKLIST.md)**.
1. **Practice disengaging first:** LDA button, brake (set "steering mode on brake" to *Disengage*), firm steering override; unplugging the device restores stock.
2. **Parked:** the device must show *Hyundai Staria Non-SCC 2023* (not dashcam/unsupported), with no CAN errors and no new cluster warnings. Upload that segment for review.
3. **Low speed (10–30 km/h, quiet road, daylight):** engage with LDA, check smooth steering, test every disengage method. Keep it short.
4. **Normal roads:** only after 2–3 are clean. Increase speed gradually; expect the tune to settle over the first 30–60 min.
5. **Stop and upload logs** on any unexpected steering, oscillation, EPS/LFA/FCA/ESC fault, or CAN error.

## Test results
9,821 panda safety tests pass (474 new non-SCC tests), plus opendbc/sunnypilot car tests, MISRA, and lint. A replay of two real drives showed 0 rx-check failures and 21,768/21,768 TX frames accepted. See **[TEST_RESULTS.md](TEST_RESULTS.md)**.

## Credits and license
- Built on **sunnypilot** by Haibin Wen / SUNNYPILOT LLC and contributors, and on **openpilot** and **opendbc** by comma.ai and contributors. The original sunnypilot README is kept as [README.sunnypilot.md](README.sunnypilot.md).
- Licensing is unchanged from upstream: [LICENSE](LICENSE) (MIT, comma.ai) and [LICENSE.md](LICENSE.md) (sunnypilot custom MIT); vendored opendbc keeps `opendbc_repo/LICENSE*`.
- As required by sunnypilot's license: *"This software is licensed under a custom license requiring permission for use."* *"This project uses software from Haibin Wen and SUNNYPILOT LLC and is licensed under a custom license requiring permission for use."*
- This is a personal, non-commercial port. It is not affiliated with or endorsed by comma.ai, sunnypilot, or Hyundai.

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. NO WARRANTY EXPRESSED OR IMPLIED.
