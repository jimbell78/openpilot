# Installing staria-pilot on a comma 3X (2023 Hyundai Staria, Turkish/European market, no radar / no BSM / no factory SCC)

> **Safety first.** This is an experimental, unofficial, steering-only port. It never brakes or accelerates. Stay attentive with your hands on the wheel at all times and be ready to take over instantly. Do not disable, bypass or raise any panda safety limit.

## What you need
- comma 3X (built-in panda; no separate panda needed)
- Hyundai **K** harness (same connector as the factory LFA camera behind the mirror)
- The car: 2023 Staria with factory LFA/LKA camera `99211-CG000` (`US4 MFC AT EUR LHD 1.00 1.04`), **no** radar, **no** BSM, **no** smart cruise
- A computer with an SSH client and a GitHub account that has an SSH public key added (https://github.com/settings/keys)

## Why there is no "custom software" URL
The comma setup screen's **Custom Software** URL cannot install this repository directly. Both web installers hard-code the repository *name*:

| Address typed on the device | Repository it actually clones (verified) |
|---|---|
| `installer.comma.ai/<user>/<branch>` | `https://github.com/<user>/openpilot.git` |
| `install.sunnypilot.ai/fork/<user>/<branch>` | `https://github.com/<user>/sunnypilot.git` (URL read from the installer binary the server returns) |
| `install.sunnypilot.ai/<user>/<branch>` | `https://github.com/sunnypilot/sunnypilot.git` (`<user>` ignored) |

This repository is `jimbell78/staria-pilot`, so none of these work, and `jimbell78/openpilot` / `jimbell78/sunnypilot` are unrelated older forks: **do not use** `installer.comma.ai/jimbell78/...` or `install.sunnypilot.ai/fork/jimbell78/...`; they would install a different codebase.

## Install (SSH + git clone)
1. Make sure the device already runs openpilot or sunnypilot (if it is on the setup screen, choose **openpilot**). Connect it to Wi-Fi.
2. On the device enable SSH and add your GitHub username under **SSH Keys** (Settings → Network → Advanced, or Settings → Developer, depending on the version). The device downloads your GitHub public keys.
3. Note the device's IP address (Settings → Network → Advanced, or your router).
4. From your computer:
   ```bash
   ssh comma@<device-ip>
   cd /data
   mv openpilot openpilot.bak            # keep the old install so you can roll back
   git clone --recurse-submodules --depth=1 -b staria-tr-3x https://github.com/jimbell78/staria-pilot.git openpilot
   cd openpilot && git lfs pull          # model/asset files are stored with Git LFS (public, via .lfsconfig)
   sudo reboot
   ```
5. The first boot compiles everything (can take 10–20+ minutes; the screen shows progress). If the device asks to update AGNOS (the OS), accept it.
6. When it starts, check **Settings → Vehicle**: it should show **Hyundai Staria Non-SCC 2023** after you turn the car on, not "dashcam" or "unsupported vehicle".

Roll back at any time:
```bash
ssh comma@<device-ip>
cd /data && rm -rf openpilot && mv openpilot.bak openpilot && sudo reboot
```

## Settings to use for the first drives
- **MADS** (Modular Assistive Driving System): on (default). The steering-wheel **lane-assist (LDA) button** engages/disengages steering. There is no cruise-based engagement on this car.
- **Steering mode on brake: Disengage** (recommended while testing).
- Leave **Experimental / openpilot longitudinal** off; it is unavailable on this car anyway (no SCC).
- Keep driver monitoring as is.

Then follow [FIRST_DRIVE_CHECKLIST.md](FIRST_DRIVE_CHECKLIST.md) step by step.

## Updating
```bash
ssh comma@<device-ip>
cd /data/openpilot && git pull && git submodule update --init --recursive && git lfs pull && sudo reboot
```
(If the branch history is ever rewritten, re-clone as in step 4 instead.)
