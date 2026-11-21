# Minimal rlog CAN reader for Jim's 0.9.7/0.9.8 logs (cereal schema from openpilot v0.9.8)
import bz2
import io
import os
import capnp
import zstandard
capnp.remove_import_hook()
# path to an openpilot v0.9.8 checkout's cereal/ directory (the logs use that schema)
_CEREAL = os.environ.get('STARIA_CEREAL_DIR', 'cereal')
_log = capnp.load(os.path.join(_CEREAL, 'log.capnp'), imports=[_CEREAL, os.path.join(_CEREAL, 'include')])

def _raw(path):
  d = open(path, 'rb').read()
  if d[:3] == b'BZh':
    d = bz2.decompress(d)
  elif d[:4] == b'\x28\xb5\x2f\xfd':
    d = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(d)).read()
  return d

def events(path):
  return _log.Event.read_multiple_bytes(_raw(path), traversal_limit_in_words=2**63 - 1)

def can_batches(path, buses=(0, 1, 2)):
  """yields (logMonoTime, [(addr, bytes, src), ...]) per can event"""
  for e in events(path):
    if e.which() == 'can':
      yield e.logMonoTime, [(m.address, bytes(m.dat), m.src) for m in e.can if m.src in buses]
