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


class Corpus:
    max_word_size = 8
    no_cat = 'ALL'
    cats = ['PROPN', 'VERB', 'ADP', 'NOUN', 'SYM', 'NUM', no_cat]
    batch_size = 1000  # does not have a noticeable effect on speed
    vocab_sizes = [1000, 2000, 3000, 4000, 5000]
    corpus_sizes = [10 * 1000, 100 * 1000, 1000 * 1000, 2000000, 3000000, 4000000, 5000000]
    num_svd_dimensions = 300
