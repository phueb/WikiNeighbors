import sys

if sys.platform == 'dawrwin':
    mnt_point = '/Volumes'
elif 'linux' == sys.platform:
    mnt_point = '/media'
else:
    raise SystemExit('Ludwig is not supported on this platform')


__version__ = '1.0.0'