import attr
import yaml


class CorpusParams:

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


@attr.s
class Specs(object):
    vocab_size = attr.ib(converter=int)
    corpus_size = attr.ib(converter=int)
    cat = attr.ib(factory=str)