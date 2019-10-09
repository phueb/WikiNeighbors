from pathlib import Path
import os

from wikineighbors import dummy_data, mnt_point


class RemoteDirs:

    if dummy_data is None:
        research_data = Path(mnt_point) / 'research_data'
        if not os.path.ismount(str(research_data)):
            print('WARNING: {} not mounted.'
                  'Using dummy directory for development'.format(research_data))
            research_data = Path(mnt_point) / 'dummy_data'
    # use dummy
    else:
        research_data = Path(dummy_data)


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'wikineighbors'
    static = root / 'static'
    templates = root / 'templates'


class Default:
    header = 'Corpus ID'
    order = 'descending'


class Time:
    format = '%H:%M %B %d'