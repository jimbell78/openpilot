# Dump CAN batches (+ a few aux signals) from Jim's logs to pickle so opendbc (which has its own car.capnp) can load them without schema clashes
import pickle, sys
sys.path.insert(0, '/workspace/staria/tools')
from logcan import events
for src, dst in [('13786d6fed35676a6bafef677ed85b586b0be323e45b2ddccf05f25600bff4d1.bz2', 'drive'),
                 ('ae2ecb8426b8897433951765701848a508e9762fd93280af64ba00d318c9d0ce.bin', 'parked')]:
  can, aux = [], {'llk': [], 'gyro': [], 'liveParameters': []}
  for e in events('/workspace/staria/' + src):
    w = e.which()
    if w == 'can':
      can.append((e.logMonoTime, [(m.address, bytes(m.dat), m.src) for m in e.can]))
    elif w == 'liveLocationKalmanDEPRECATED':
      l = e.liveLocationKalmanDEPRECATED
      aux['llk'].append((e.logMonoTime, list(l.angularVelocityCalibrated.value), l.angularVelocityCalibrated.valid, list(l.velocityCalibrated.value)))
    elif w == 'livePose':
      l = e.livePose
      aux['llk'].append((e.logMonoTime, [l.angularVelocityDevice.x, l.angularVelocityDevice.y, l.angularVelocityDevice.z], l.angularVelocityDevice.valid, [l.velocityDevice.x, l.velocityDevice.y, l.velocityDevice.z]))
    elif w == 'liveParameters':
      p = e.liveParameters
      aux['liveParameters'].append((e.logMonoTime, p.steerRatio, p.stiffnessFactor, p.angleOffsetDeg, p.valid))
  pickle.dump({'can': can, 'aux': aux}, open(f'/workspace/staria/tools/{dst}.pkl', 'wb'))
  print(dst, len(can), {k: len(v) for k, v in aux.items()})
