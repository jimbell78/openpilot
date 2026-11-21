# Installing on a comma 3X (2023 Hyundai Staria, Turkish/European market, no radar / no BSM / no factory SCC)

> **Safety first.** This is an experimental, unofficial, steering-only port. It never brakes or accelerates. Stay attentive with your hands on the wheel at all times and be ready to take over instantly. Do not disable, bypass or raise any panda safety limit.

Repository: `jimbell78/openpilot`, branch **`staria-tr-3x`**

## What you need
- comma 3X (built-in panda; no separate panda needed)
- Hyundai **K** harness (same connector as the factory LFA camera behind the mirror)
- The car: 2023 Staria with factory LFA/LKA camera `99211-CG000` (`US4 MFC AT EUR LHD 1.00 1.04`), **no** radar, **no** BSM, **no** smart cruise
- Good Wi-Fi (the download is roughly 1 GB, mostly model files) and constant power for the device

## Option A: Custom Software URL (setup screen)
1. If other software is installed: **Settings → Software → Uninstall** (this wipes `/data`, including old drives). The device returns to the setup screen.
2. Choose **Custom Software** and enter exactly:
   ```
   installer.comma.ai/jimbell78/staria-tr-3x
   ```
   This clones `https://github.com/jimbell78/openpilot.git`, branch `staria-tr-3x`. Do **not** use `install.sunnypilot.ai/fork/jimbell78/...` (that points at a different, older repository).
3. Wait. The percentage only moves while git prints progress; it can sit at 9x% for several minutes while large files download. A failed or interrupted install restarts the download from zero.
4. After "Finishing install…", the first boot **compiles everything on the device** (spinner with a progress bar, 10–30+ minutes; the models compile near the end). If the device asks to update AGNOS (the OS; this branch expects AGNOS 19.9), accept it.

## Option B: SSH (bypasses the web installer and shows real errors)
Use this if Option A hangs.
1. The device needs a working install to show the SSH settings: **Settings → Developer → Enable SSH**, then **SSH Keys → Add** your GitHub username (your GitHub account needs an SSH public key: https://github.com/settings/keys).
   (On a device sitting on the setup screen with nothing installed, comma documents a setup-only key; see https://docs.comma.ai/how-to/connect-to-comma/. In that case you must also create `/data/continue.sh`, step 3.)
2. From your computer (find the IP under Settings → Network → Advanced):
   ```bash
   ssh comma@<device-ip>
   df -h /data                     # need at least ~4 GB free
   cd /data && rm -rf openpilot
   git clone -b staria-tr-3x --depth 1 --recurse-submodules https://github.com/jimbell78/openpilot.git openpilot
   cd openpilot && git lfs pull    # no-op if the clone already fetched the model files
   ```
3. Only if the device had nothing installed (setup screen):
   ```bash
   printf '#!/usr/bin/env bash\ncd /data/openpilot\nexec ./launch_openpilot.sh\n' > /data/continue.sh && chmod +x /data/continue.sh
   ```
4. `sudo reboot`. The first boot compiles as in Option A.

## Check after boot
- Turn the car on. **Settings → Vehicle** should show **Hyundai Staria Non-SCC 2023**, not "dashcam" or "unsupported vehicle".

## Settings to use for the first drives
- **MADS**: on (default). The steering-wheel **lane-assist (LDA) button** engages/disengages steering. There is no cruise-based engagement on this car.
- **Steering mode on brake: Disengage** (recommended while testing).
- Leave **Experimental / openpilot longitudinal** off; it is unavailable on this car anyway (no SCC).
- Keep driver monitoring as is.

Then follow [FIRST_DRIVE_CHECKLIST.md](FIRST_DRIVE_CHECKLIST.md) step by step.

## Updating (SSH)
```bash
ssh comma@<device-ip>
cd /data/openpilot && git pull && git submodule update --init --recursive && git lfs pull && sudo reboot
```
If the branch history is ever rewritten, re-clone as in Option B.

## Recovery
- **Settings → Software → Uninstall** or tapping the screen repeatedly during boot resets the software (wipes `/data`).
- If the device does not boot at all, reflash the OS with https://flash.comma.ai (this also wipes `/data`), then install again.
