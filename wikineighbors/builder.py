import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from scipy import sparse
from scipy.sparse import linalg as slinalg
from collections import Counter
from cached_property import cached_property

from wikineighbors.exceptions import WikiNeighborsNoMemory
from wikineighbors.exceptions import WikiNeighborsMissingW2Dfs
from wikineighbors.file_names import make_cached_file_name
from wikineighbors.file_names import to_w2dfs_file_name
from wikineighbors.utils import to_param_path
from wikineighbors import config


class SimMatBuilder:
    """
    methods for counting words and constructing a similarity matrix.
    """

    def __init__(self, corpus, specs):
        self.corpus = corpus
        self.cache_path = config.LocalDirs.cache / corpus.name
        self.specs = specs
        self.vocab_file_name = make_cached_file_name('vocab', specs)
        self.sim_mat_file_name = make_cached_file_name('sim_mat', specs)

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
        print('Percentage of non-zeros in term-by-doc matrix: {}%'.format(num_nonzeros / init_mat.size * 100))
        sparse_mat = sparse.csr_matrix(init_mat).asfptype()

        # svd
        u, s, v = slinalg.svds(sparse_mat, k=config.Sims.num_svd_dimensions)
        reduced_mat = u[:, :config.Sims.num_svd_dimensions]

        # cosine
        res = cosine_similarity(reduced_mat)

        return res

    def make_vocab(self, w2cf):
        print('Making vocab...')
        vocab = set()
        num_too_big = 0
        for w, f in sorted(w2cf.items(), key=lambda i: i[1], reverse=True):

            if len(w) > config.Sims.max_word_size:
                num_too_big += 1
                continue

            vocab.add(w.lower())

            if len(vocab) == self.specs.vocab_size:
                break
        else:  # vocab is not big enough
            raise RuntimeError('Vocab is too small. Increase config.Corpus.max_word_size')

        print('Final vocab size={}'.format(len(vocab)))
        print('Excluded {} words that had more than {} characters'.format(num_too_big, config.Sims.max_word_size))

        return list(vocab)

    @cached_property
    def w2dfs_paths(self):
        res = []
        for param_name in self.corpus.param_names:
            param_path = to_param_path(param_name)
            w2df_path = param_path / to_w2dfs_file_name(self.specs.corpus_size, self.specs.cat)
            if not w2df_path.exists():
                raise WikiNeighborsMissingW2Dfs(w2df_path)
            else:
                print('Will load {}'.format(w2df_path))
                res.append(w2df_path)
        return res

    def _build(self):
        # check that memory is sufficient
        shape = (self.specs.vocab_size, self.specs.corpus_size)
        try:
            init_mat = np.zeros(shape, dtype=np.int16)
            num_mbs = init_mat.nbytes / 1e6
            print('Successfully initialized matrix with shape={} requiring {} megabytes'.format(shape, num_mbs))
        except MemoryError:
            raise WikiNeighborsNoMemory(shape)

        # make w2cf (word 2 corpus-frequency)
        w2cf = Counter()
        n = 0
        for w2dfs_path in self.w2dfs_paths:
            with w2dfs_path.open('rb') as f:
                w2dfs = pickle.load(f)
            print('Loaded {}'.format(w2dfs_path))
            for w2df in w2dfs:
                w2cf.update(w2df)
                n += 1
        print('Loaded {} w2dfs from disk'.format(n))

        # make vocab
        print('Making vocab with size={} and cat={}'.format(self.specs.vocab_size, self.specs.cat))
        vocab = self.make_vocab(w2cf)
        del w2cf

        # make sim mat
        sim_mat = self.make_sim_mat(w2dfs, vocab, init_mat)  # TODO in a multiprocesing loop, populate term-doc-mat

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
