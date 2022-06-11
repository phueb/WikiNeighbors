from pathlib import Path
import os
from appdirs import AppDirs

import wikineighbors

dirs = AppDirs(wikineighbors.__name__, wikineighbors.__author__, wikineighbors.__version__)


class RemoteDirs:
    if wikineighbors.s76:
        ludwig_data = Path('/') / 'mnt' / 'md0' / 'ludwig_data'
    else:
        ludwig_data = Path(wikineighbors.mnt_point) / 'ludwig_data'
        if not os.path.ismount(ludwig_data):
            raise OSError('{} not mounted.'.format(ludwig_data))

    wiki_runs = ludwig_data / 'CreateWikiCorpus' / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'wikineighbors'
    static = root / 'static'
    cache = Path(dirs.user_cache_dir)


class Default:
    header = 'Corpus ID'
    order = 'descending'
    word = ''


class Time:
    format = '%B %d %Y'


class Max:
    num_fields = 50
    num_neighbors = 10


class Sims:
    num_jobs = 6
    max_word_size = 8
    vocab_sizes = [1000, 2000, 3000, 4000, 5000, 10000]
    num_svd_dimensions = 30  # keep this low to prevent memory error
    must_include_f_name = 'agents.txt'
