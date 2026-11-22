# staria-pilot (jimbell78/openpilot, branch `staria-tr-3x`)

**Steering-only sunnypilot port for the 2023 Hyundai Staria (Turkish/European market, no radar, no BSM, no factory smart cruise), for the comma 3X.**

> ## ⚠️ Safety
> This is **driver assistance only, not self-driving.** The driver must stay fully attentive, hands on the wheel, ready to take over instantly. It **only steers**: it never brakes or accelerates. Do not disable or relax any panda safety check, torque limit, or driver monitoring. Experimental and unofficial; use at your own risk.

## Install (no SSH needed)
On the comma 3X setup screen choose **Custom Software** and enter:
```
installer.comma.ai/jimbell78/staria-tr-3x
```
To pin the first working build instead of the latest branch, use the tag: `installer.comma.ai/jimbell78/v0.1-staria-tr-3x`.

What to expect:
- Download is about 1 GB. Use good Wi-Fi and keep the device powered.
- The branch is **source code, not a prebuilt image**: the first boot compiles openpilot on the device (spinning sunnypilot logo with a progress bar, 10–30+ minutes). This is normal; don't unplug it.
- tinygrad is vendored as plain files, so the installer **no longer clones the ~1.7 GB tinygrad history** that caused the old freeze at 92%.

## Prerequisite: comma OS (AGNOS) 19.9
This branch targets **AGNOS 19.9**, like all current sunnypilot branches. A 3X that came on, or was reflashed to, AGNOS 20.6 will loop on the logo with a `GuiTextAlignment` error. Roll it back to 19.9 over SSH (Settings → Developer → Enable SSH, add your GitHub key), in a `tmux` session so it survives a dropped connection:
```
/data/openpilot/openpilot/common/hardware/comma/agnos.py --swap /data/openpilot/openpilot/system/hardware/comma/agnos.json
```
Wait for `Verification succeeded. Swapping to slot ...`, then `sudo reboot`.
If you had edited `AGNOS_VERSION` in `launch_env.sh`, put it back to 19.9 first: `cp /data/launch_env.sh.bak /data/openpilot/launch_env.sh`. (Editing it to 20.6 is **not** a safe fix.)

## Recovery: stuck on the logo after an interrupted install
1. Try power-cycling once and wait a full 30 minutes; the first build is slow.
2. If it still won't start, reflash comma OS over USB from a computer using Chrome at [flash.comma.ai](https://flash.comma.ai) and follow its steps. This **erases the device's data** and installs the latest comma OS (currently 20.6), so do the 19.9 rollback above before installing this branch again.

## What this is
- A fork of [sunnypilot](https://github.com/sunnypilot/sunnypilot), based on [openpilot](https://github.com/commaai/openpilot) by comma.ai. Adds the car "Hyundai Staria Non-SCC 2023" (`HYUNDAI_STARIA_4TH_GEN_NON_SCC`) and a non-SCC CAN-FD panda safety mode. Details: [PORT_NOTES.md](PORT_NOTES.md).
- Hardware: comma 3X + Hyundai K harness; Staria camera `99211-CG000`. Other variants are kept in dashcam mode.
- Steering is engaged with the wheel's lane-assist (LDA) button (sunnypilot MADS). Panda transmits only steering/cluster messages; cruise, button and SCC messages are blocked; torque limits are unchanged from sunnypilot.
- More: [INSTALL.md](INSTALL.md), [FIRST_DRIVE_CHECKLIST.md](FIRST_DRIVE_CHECKLIST.md), [TEST_RESULTS.md](TEST_RESULTS.md).

## Credits and license
- Built on **sunnypilot** by Haibin Wen / SUNNYPILOT LLC and contributors, and on **openpilot** and **opendbc** by comma.ai and contributors. The original sunnypilot README is kept as [README.sunnypilot.md](README.sunnypilot.md).
- Licensing is unchanged from upstream: [LICENSE](LICENSE) (MIT, comma.ai) and [LICENSE.md](LICENSE.md) (sunnypilot custom MIT); vendored opendbc keeps `opendbc_repo/LICENSE*`.
- As required by sunnypilot's license: *"This software is licensed under a custom license requiring permission for use."* *"This project uses software from Haibin Wen and SUNNYPILOT LLC and is licensed under a custom license requiring permission for use."*
- Personal, non-commercial port; not affiliated with or endorsed by comma.ai, sunnypilot, or Hyundai.

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. NO WARRANTY EXPRESSED OR IMPLIED.
