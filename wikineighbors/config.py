from pathlib import Path
import os

from wikineighbors import mnt_point


class RemoteDirs:
    research_data = Path(mnt_point) / 'research_data'
    if not os.path.ismount(research_data):
        raise OSError('{} not mounted.'.format(research_data))

    runs = research_data / 'CreateWikiCorpus' /'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'wikineighbors'
    static = root / 'static'
    templates = root / 'templates'


class Default:
    header = 'Corpus ID'
    order = 'descending'
    text = 'Type a word here'


class Time:
    format = '%H:%M %B %d'


class Max:
    num_words = 10000
    num_docs = 10000
    num_neighbors = 10