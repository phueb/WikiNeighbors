import yaml

from wikineighbors import config
from wikineighbors.utils import get_id_as_int, get_time_modified, count_replications


class Params:

    def __init__(self, params_path):

        with (params_path / 'param2val.yaml').open('r') as f:
            param2val = yaml.load(f, Loader=yaml.FullLoader)

        self.param_name = param2val.pop('param_name')
        self.job_name = param2val.pop('job_name')

        self.param2val = param2val

        self.stripped_param2val = self.make_stripped()

    def make_stripped(self):
        """
        return self.param2val but with "part" removed
        """
        res = self.param2val.copy()
        res.pop('part')
        return res

    def __getattr__(self, name):
        if name in self.param2val:
            return self.param2val[name]
        else:
            raise AttributeError('No such attribute')

    def __str__(self):
        res = ''
        for k, v in sorted(self.stripped_param2val.items()):
            res += '<p style="margin-bottom: 0px">{}={}</p>'.format(k, v)
        return res


def make_corpus_headers_and_rows():
    """
    make a row for each corpus - an abstraction over possibly many parameter configurations
    because a corpus is typically created in parallel on multiple machines, producing multiple bodies.txt files.
    a row is assigned to any new parameter configuration
    (comparison is performed AFTER 'part' is removed from param2val).
    to achieve this, param_name folders must be iterated over in order (param_1, param2, ...)
    """
    stripped_param2vals = []
    headers = ['Corpus ID', 'Last modified']
    rows = []
    all_param_paths = config.RemoteDirs.runs.glob('param*')
    for p in sorted(all_param_paths, key=lambda p: get_id_as_int(p.name)):
        params = Params(p)
        # do not assign a row to a configuration which has already been assigned a row
        # this has a filtering effect because 'part' information is first removed
        if params.stripped_param2val not in stripped_param2vals:  # lets through only a new corpus
            param_id = get_id_as_int(p.name)
            corpus_name = 'Corpus-{}'.format(param_id)
            row = {headers[0]: param_id,
                   headers[1]: get_time_modified(p),
                   # used, but not displayed in table
                   'corpus_name': corpus_name,
                   'tooltip': params,
                   }
            assert count_replications(p.name) == 1
            rows.append(row)

        stripped_param2vals.append(params.stripped_param2val)

    return headers, rows


