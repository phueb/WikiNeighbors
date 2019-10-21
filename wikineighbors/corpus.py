from cached_property import cached_property
import yaml

from wikineighbors.exceptions import WikiNeighborsNoArticlesFound
from wikineighbors.utils import gen_100_param_names, to_param_path
from wikineighbors.file_names import to_w2dfs_file_name
from wikineighbors import config


class Corpus:
    """
    an abstraction.
    contains info about text file locations on shared drive.
    """

    def __init__(self, name):
        self.name = name
        self.cache_path = config.LocalDirs.cache / name
        self.separator = '-'

    @cached_property
    def cached_vocab_names(self):

        if not self.cache_path.exists():
            return []

        names = []
        for p in self.cache_path.glob('vocab_*_*.pkl'):
            names.append(p.stem.lstrip('vocab_').replace('_', self.separator))
        return sorted(names)

    @cached_property
    def num_param_names(self):
        return len(self.param_names)

    @cached_property
    def param_names(self):
        param_names = []
        parts = set()  # a param_name is only valid if its attribute "parts" was not previously collected
        for param_name in gen_100_param_names(self.name):
            param_path = to_param_path(param_name)

            # make sure path exists
            if not param_path.exists():
                break  # this break is required, else infinite loop

            # make sure that param_name is valid (that it really is part of the corpus)
            with (param_path / 'param2val.yaml').open('r') as f:
                param2val = yaml.load(f, Loader=yaml.FullLoader)
            if param2val['part'] in parts:
                continue  # this happens because param_names are generated by returning all possible param_names

            # collect
            parts.add(param2val['part'])
            param_names.append(param_name)
        return param_names

    @cached_property
    def txt_paths(self):
        res = []
        for param_name in self.param_names:
            param_path = to_param_path(param_name)
            # check that articles are available (bodies.txt files)
            body_paths = [p for p in param_path.glob('**/bodies.txt')]
            num_bodies = len(body_paths)
            if num_bodies == 0:
                raise WikiNeighborsNoArticlesFound(param_path)
            elif num_bodies > 1:
                raise SystemError('Found more than 1 bodies.txt files in {}'.format(param_name))
            else:
                res.append(body_paths[0])
        return res

    @cached_property
    def w2dfs_names(self):
        first_param_path = to_param_path(self.param_names[0])
        pattern = to_w2dfs_file_name('*', '*')
        return [p.name for p in first_param_path.glob(pattern)]