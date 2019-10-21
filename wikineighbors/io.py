from wikineighbors import config
import yaml
from wikineighbors.utils import get_id_as_int, get_time_modified, count_replications


def make_home_data():
    """
    make a row for each corpus - an abstraction over possibly many parameter configurations
    because a corpus is typically created in parallel on multiple machines, producing multiple bodies.txt files.
    a row is assigned to any new parameter configuration
    (comparison is performed AFTER 'part' is removed from param2val).
    to achieve this, param_name folders must be iterated over in order (param_1, param2, ...)
    """
    reduced_param2vals = []
    buttons = ['info', 'vocab', 'query']  # careful, these must also be names of URLS
    headers = ['Corpus ID', 'Last modified']
    rows = []
    all_param_paths = config.RemoteDirs.wiki_runs.glob('param*')
    for p in sorted(all_param_paths, key=lambda p: get_id_as_int(p.name)):

        # make param2val_no_part
        with (p / 'param2val.yaml').open('r') as f:
            param2val = yaml.load(f, Loader=yaml.FullLoader)
        reduced_param2val = param2val
        del reduced_param2val['job_name']
        del reduced_param2val['param_name']
        del reduced_param2val['part']

        # do not assign a row to a configuration which has already been assigned a row
        # this has a filtering effect because 'part' information is first removed
        if reduced_param2val not in reduced_param2vals:  # lets through only a new corpus
            param_id = get_id_as_int(p.name)
            corpus_name = 'Corpus-{}'.format(param_id)
            tooltip = ''
            for k, v in sorted(reduced_param2val.items()):
                tooltip += f'<p style="margin-bottom: 0px">{k}={v}</p>'
            row = {headers[0]: param_id,
                   headers[1]: get_time_modified(p),
                   # used, but not displayed in table
                   'corpus_name': corpus_name,
                   'tooltip': tooltip,
                   #
                   'buttons': buttons
                   }

            assert count_replications(p.name) == 1
            rows.append(row)

        reduced_param2vals.append(reduced_param2val)

    return headers, rows, buttons


