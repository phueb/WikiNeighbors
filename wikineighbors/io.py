from wikineighbors import config
from wikineighbors.params import Params
from wikineighbors.utils import get_id_as_int, get_time_modified, count_replications
from wikineighbors.corpus import Corpus


def make_home_data():
    """
    make a row for each corpus - an abstraction over possibly many parameter configurations
    because a corpus is typically created in parallel on multiple machines, producing multiple bodies.txt files.
    a row is assigned to any new parameter configuration
    (comparison is performed AFTER 'part' is removed from param2val).
    to achieve this, param_name folders must be iterated over in order (param_1, param2, ...)
    """
    stripped_param2vals = []
    _buttons = ['info', 'vocab', 'query']  # careful, these must also be names of URLS
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
            corpus = Corpus(corpus_name)
            buttons = _buttons[:] if corpus.cached_vocab_sizes else _buttons[:-1]
            row = {headers[0]: param_id,
                   headers[1]: get_time_modified(p),
                   # used, but not displayed in table
                   'corpus_name': corpus_name,
                   'tooltip': params,
                   #
                   'buttons': buttons
                   }

            assert count_replications(p.name) == 1
            rows.append(row)

        stripped_param2vals.append(params.stripped_param2val)

    return headers, rows, _buttons


