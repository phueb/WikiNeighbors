import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from scipy import sparse
from scipy.sparse import linalg as slinalg
from collections import Counter

from wikineighbors.exceptions import WikiNeighborsNoMemory
from wikineighbors.exceptions import WikiNeighborsNoSpecs
from wikineighbors.params import Specs
from wikineighbors import config


class SimMatBuilder:
    """
    methods for counting words and constructing a similarity matrix.
    """

    def __init__(self, corpus, specs):
        self.corpus = corpus
        self.cache_path = config.LocalDirs.cache / corpus.name
        self.specs = specs
        self.vocab_file_name = 'vocab_{}_{}_{}.pkl'.format(self.specs.vocab_size,
                                                           self.specs.corpus_size,
                                                           self.specs.cat)
        self.sim_mat_file_name = 'sim_mat_{}_{}_{}.pkl'.format(self.specs.vocab_size,
                                                               self.specs.corpus_size,
                                                               self.specs.cat)

    @classmethod
    def load_from_session(cls, session, corpus):
        try:
            kwargs = session['corpus_name']
        except KeyError:  # user has not previously selected specs for corpus
            raise WikiNeighborsNoSpecs
        specs = Specs(**kwargs)
        return cls(corpus, specs)

    def build_and_save(self):
        vocab, sim_mat = self._build()
        self._save_to_disk(vocab, sim_mat)
        del vocab
        del sim_mat  # TODO how to make sure it is deleted - weakref?

    @staticmethod
    def make_sim_mat(w2dfs, vocab, init_mat):  # this is slow
        print('Making term-by-doc matrix...')
        for col_id, w2df in enumerate(w2dfs):
            try:
                init_mat[:, col_id] = [w2df[w] for w in vocab]
            except IndexError:
                print(col_id)

        # convert to sparse format
        num_nonzeros = np.count_nonzero(init_mat)
        print('Percentage of non-zeros in term-by-doc matrix: {}'.format(num_nonzeros / init_mat.size))
        sparse_mat = sparse.csr_matrix(init_mat).asfptype()

        # svd
        u, s, v = slinalg.svds(sparse_mat, k=config.Corpus.num_svd_dimensions)
        reduced_mat = u[:, :config.Corpus.num_svd_dimensions]

        # cosine
        res = cosine_similarity(reduced_mat)

        return res

    def make_vocab(self, w2cf):
        print('Making vocab...')
        vocab = set()
        num_too_big = 0
        for w, f in sorted(w2cf.items(), key=lambda i: i[1], reverse=True):

            if len(w) > config.Corpus.max_word_size:
                num_too_big += 1
                continue

            vocab.add(w.lower())

            if len(vocab) == self.specs.vocab_size:
                break
        else:  # vocab is not big enough
            raise RuntimeError('Vocab is too small. Increase config.Corpus.max_word_size')

        print('Final vocab size={}'.format(len(vocab)))
        print('Excluded {} words that had more than {} characters'.format(num_too_big, config.Corpus.max_word_size))

        return list(vocab)

    def _build(self):
        # check that memory is sufficient
        shape = (self.specs.vocab_size, self.specs.corpus_size)
        try:
            init_mat = np.zeros(shape, dtype=np.int16)
            num_mbs = init_mat.nbytes / 1e6
            print('Successfully initialized matrix with shape={} requiring {} megabytes'.format(shape, num_mbs))
        except MemoryError:
            raise WikiNeighborsNoMemory(shape)

        # make vocab
        print('Making vocab with size={} and cat={}'.format(self.specs.vocab_size, self.specs.cat))


        # TODO load w2dfs from WikiOrder
        #  and in a multiprocesing loop, update w2cf and populate term-doc-mat
        w2cf = Counter()
        param_path = config.RemoteDirs.wiki_runs / self.corpus.first_param_name
        for w2df_path in param_path.glob(
                'w2dfs_{}_{}_part*of*.pkl'.format(self.specs.corpus_size,
                                                  self.specs.cat)):
            print(w2df_path.name)

            with w2df_path.open('rb') as f:
                w2dfs = pickle.load(f)

            for w2df in w2dfs:
                w2cf.update(w2df)

        vocab = self.make_vocab(w2cf)
        del w2cf

        # make sim mat
        sim_mat = self.make_sim_mat(w2dfs, vocab, init_mat)

        return vocab, sim_mat

    def _save_to_disk(self, vocab, sim_mat):
        # make dir + save to disk
        if not self.cache_path.is_dir():
            self.cache_path.mkdir(parents=True)

        with (self.cache_path / self.vocab_file_name).open('wb') as f:
            pickle.dump(vocab, f)
        print('Saved vocab to {}'.format(config.LocalDirs.cache))

        with (self.cache_path / self.sim_mat_file_name).open('wb') as f:
            pickle.dump(sim_mat, f)
        print('Saved sim_mat to {}'.format(config.LocalDirs.cache))
