from cached_property import cached_property
import pickle

from wikineighbors.params import Specs

from wikineighbors.exceptions import WikiNeighborsNoVocabFound
from wikineighbors.exceptions import WikiNeighborsNoSpecs
from wikineighbors.file_names import make_cached_file_name
from wikineighbors import config


class Responder:
    """
    responds to user requests for neighbors
    """

    def __init__(self, corpus, specs):
        self.corpus = corpus
        self.cache_path = config.LocalDirs.cache / corpus.name
        self.specs = specs
        self.vocab_file_name = make_cached_file_name('vocab', specs)
        self.sim_mat_file_name = make_cached_file_name('sim_mat', specs)

    @classmethod
    def load_from_session(cls, session, corpus):
        try:
            vocab_name = session.get(corpus.name)
        except KeyError:  # user has not previously selected specs for corpus
            raise WikiNeighborsNoSpecs(corpus.name)
        specs = Specs(*vocab_name.split(corpus.separator))
        return cls(corpus, specs)

    @cached_property
    def w2id(self):
        return {w: i for i, w in enumerate(self.vocab)}

    def get_sims(self, word, other_words):
        other_ids = [self.w2id[w] for w in other_words]
        res = self.sim_mat[self.w2id[word], other_ids]
        return res

    def get_neighbors(self, word):
        if not self.corpus.cached_vocab_names:
            raise WikiNeighborsNoVocabFound(self.corpus.name)

        print('Computing neighbors...')
        sims = self.sim_mat[self.w2id[word]]
        res = [(w, s) for w, s in sorted(zip(self.vocab, sims), key=lambda i: i[1])
               if w != word]
        return zip(*res)  # unpack [(w, s), ...(w, s)] to [w, ...w], [s, ..., s]

    def load_vocab(self):
        with (self.cache_path / self.vocab_file_name).open('rb') as f:
            res = pickle.load(f)
        return res

    @cached_property
    def vocab(self):
        if not self.corpus.cached_vocab_names:
            raise WikiNeighborsNoVocabFound(self.corpus.name)
        else:
            return self.load_vocab()

    def load_sim_mat(self):
        with (self.cache_path / self.sim_mat_file_name).open('rb') as f:
            res = pickle.load(f)
        return res

    @cached_property
    def sim_mat(self):
        if not self.corpus.cached_vocab_names:
            raise WikiNeighborsNoVocabFound(self.corpus.name)
        else:
            return self.load_sim_mat()