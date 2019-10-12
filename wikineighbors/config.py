from pathlib import Path
import os
from appdirs import AppDirs

import wikineighbors

dirs = AppDirs(wikineighbors.__name__, wikineighbors.__author__, wikineighbors.__version__)


class RemoteDirs:
    if wikineighbors.s76:
        research_data = Path('/') / 'mnt' / 'md0' / 'research_data'
    else:
        research_data = Path(wikineighbors.mnt_point) / 'research_data'
        if not os.path.ismount(research_data):
            raise OSError('{} not mounted.'.format(research_data))

    runs = research_data / 'CreateWikiCorpus' / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'wikineighbors'
    static = root / 'static'
    cache = Path(dirs.user_cache_dir)  # TODO use for caching wiki data


class Default:
    header = 'Corpus ID'
    order = 'descending'
    word = ''
    num_fields = 3


class Time:
    format = '%H:%M %B %d'


class Max:
    num_words = 10000
    num_docs = 10000
    num_neighbors = 10


class Corpus:
    worker_count = 4
    vocab_sizes = [100,
                   1000,
                   10000]