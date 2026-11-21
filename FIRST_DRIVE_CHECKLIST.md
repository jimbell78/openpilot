# First-drive checklist: Staria Non-SCC steering-only port (comma 3X)

**Safety:** this is an experimental, unofficial port. Keep your hands on the wheel and your eyes on the road the whole time, and be ready to take over immediately. openpilot only steers. It never brakes or accelerates. Your cruise control and pedals are your own.

## How to disengage (practice these first)
- Press the **lane-assist (LDA) button** on the steering wheel (toggles MADS steering on/off).
- **Press the brake.** With "steering mode on brake = Disengage" (recommended for testing), steering turns off.
- **Steer firmly.** Driver torque above the limit overrides openpilot, and the panda caps openpilot's torque (max 270, rate-limited).
- Last resort: unplug the device. The car returns fully to stock behaviour.

## A. Parked (engine on, P, parking brake on)
1. The device boots without errors and shows **Hyundai Staria Non-SCC 2023**, not "dashcam" or "unsupported vehicle". No "CAN error", "Controls unresponsive" or "Car unrecognized" alerts.
2. The cluster shows no new warnings (LFA/LKA/FCA/ESC/airbag). Take a photo of the cluster before and after installing to compare.
3. Press the LDA button. In P, sunnypilot should show the lateral state but not steer (wrong gear). There should be no fault alert.
4. Press and release the brake and the gas, and turn the wheel by hand. There should be no faults.
5. Shift to R, then D, with the brake held. There should be no faults. The camera's own LFA/LKA alerts may change; note what you see.
6. Upload this parked segment (rlogs) so it can be checked before you drive.

## B. Low speed (empty car park or quiet road, about 10–30 km/h, daylight, good lane lines)
1. Hold the wheel normally with both hands. Press the LDA button to engage.
2. Check that the steering effort is gentle and follows the lane. There should be no jerks or oscillation.
3. Test each disengage: LDA button, brake, firm steering override. Each one must stop steering immediately.
4. Watch for "Steering temporarily unavailable" or EPS fault messages. If you see one, stop and upload the logs.
5. Keep the first session short, about 5–10 min.

## C. Normal roads (only after A and B are clean)
1. Increase speed gradually (50 → 80 km/h). Gentle curves only at first; no sharp bends, roundabouts or construction zones.
2. Keep your hands on the wheel. Expect the car to understeer or cut corners while the steerRatio and torque tune are still being learned (about the first 30–60 min of driving).
3. Use your own cruise control or the pedals for speed. openpilot will not slow down for curves, cars or anything else.

## Stop immediately and report (upload rlogs) if:
- the car steers without being engaged, or keeps steering after you pressed the LDA button or the brake
- you see oscillation, jerks, or a pull toward the lane edge
- any cluster fault appears (EPS/MDPS, LFA, FCA/AEB, ESC)
- the factory forward-collision warning or AEB looks disabled. It should still work, because only the camera's steering/cluster-icon messages are replaced. Do **not** test AEB deliberately.
- sunnypilot shows CAN errors or "controls mismatch"

Do not tape over or disable driver monitoring. Do not add weights to the wheel. Do not use any tool or setting to raise the panda's torque limits.
