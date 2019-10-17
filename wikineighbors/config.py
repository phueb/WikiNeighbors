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

    wiki_runs = research_data / 'CreateWikiCorpus' / 'runs'


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
    format = '%H:%M %B %d'


class Max:
    num_fields = 50
    num_neighbors = 10


class Sims:
    max_word_size = 8
    vocab_sizes = [1000, 2000, 3000, 4000, 5000, 10000]
    num_svd_dimensions = 300
