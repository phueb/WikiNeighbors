import datetime
import re
from math import log, floor


from wikineighbors import config

regex_digit = re.compile(r'[0-9]+')


def human_format(number):
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    magnitude = int(floor(log(number, k)))
    return '%.2f%s' % (number / k**magnitude, units[magnitude])


def to_param_path(param_name):
    return config.RemoteDirs.runs / param_name


def sort_rows(rows, header, order):

    assert header in rows[0]  # make sure that the header is actually in use

    if header == 'Last Modified':
        print('Sorting using datetime')
        res = sorted(rows,
                     key=lambda row: datetime.datetime.strptime(row[header], config.Time.format),
                     reverse=True if order == 'descending' else False)
    else:
        res = sorted(rows,
                     key=lambda row: row[header],
                     reverse=True if order == 'descending' else False)
    return res


def get_id_as_int(param_name):
    return int(regex_digit.search(param_name).group())


def get_time_modified(p):
    return datetime.datetime.fromtimestamp(
        p.lstat().st_mtime).strftime(config.Time.format)


def gen_100_param_names(corpus_name):
    """
    assumptions:
    1. assume that param_ids were assigned in order.
    2. each corpus was generated with no more than 100 Ludwig workers.
    count up 100 and let downstream logic stop the generator."""
    first_param_id = get_id_as_int(corpus_name)
    for param_id in range(first_param_id, first_param_id + 100):
        yield 'param_{}'.format(param_id)


def count_replications(param_name):
    """
    do not count files like .DS_Store and param2val.yaml
    """
    return len(list(to_param_path(param_name).glob('[!.]*[!.yaml]')))