import attr


@attr.s
class Specs(object):
    vocab_size = attr.ib(converter=int)
    corpus_size = attr.ib(converter=int)
    cat = attr.ib(factory=str)