import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from sklearn.decomposition import TruncatedSVD
from collections import Counter
from multiprocessing import Pool
from cached_property import cached_property
from scipy.sparse import csr_matrix

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
        del sim_mat

    @staticmethod
    def _make_term_by_window_mat_chunk(w2dfs_path, vocab):
        print('Starting worker', flush=True)

        with w2dfs_path.open('rb') as f:
            w2dfs = pickle.load(f)
        print('Worker loaded {}'.format(w2dfs_path))

        chunk = np.zeros((len(vocab), len(w2dfs)), dtype=np.int16)
        for col_id, w2df in enumerate(w2dfs):
            chunk[:, col_id] = [w2df[w] for w in vocab]
        print('Worker made matrix with shape {}'.format(chunk.shape), flush=True)
        return chunk

    def _make_term_by_doc_mat(self, vocab):
        self.check_memory()

        print('Making term-by-doc matrix...')
        num_workers = 2  # do not use more than 2 if not more than 32GB memory is available
        pool = Pool(num_workers)
        chunks = pool.starmap(self._make_term_by_window_mat_chunk,
                              zip(self.w2dfs_paths, [vocab] * len(self.w2dfs_paths)))

        res = np.hstack(chunks)  # TODO test
        print('Term-by-doc matrix has shape {}'.format(res.shape))
        return res

    @staticmethod
    def _make_sim_mat(term_doc_mat):
        # convert to sparse format
        num_nonzeros = np.count_nonzero(term_doc_mat)
        print('Percentage of non-zeros in term-by-doc matrix: {}%'.format(num_nonzeros / term_doc_mat.size * 100))

        # reduce dimensionality
        reducer = TruncatedSVD(n_components=config.Sims.num_svd_dimensions)
        sparse_mat = csr_matrix(term_doc_mat)
        reduced_mat = reducer.fit_transform(sparse_mat)

        # cosine
        res = cosine_similarity(reduced_mat)

        return res

    def _make_vocab(self, w2cf):
        print('Making vocab with size={} and cat={}'.format(
            self.specs.vocab_size, self.specs.cat))
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
        for param_name in self.corpus.param_names[:config.Sims.num_w2df_chunks]:
            param_path = to_param_path(param_name)
            w2df_path = param_path / to_w2dfs_file_name(self.specs.corpus_size, self.specs.cat)
            if not w2df_path.exists():
                raise WikiNeighborsMissingW2Dfs(w2df_path)
            else:
                print('Will load {}'.format(w2df_path))
                res.append(w2df_path)
        return res

    def _build(self):
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
            del w2dfs  # otherwise twice as much memory is used
        print('Loaded {} w2dfs from disk'.format(n))

        # make vocab
        vocab = self._make_vocab(w2cf)
        del w2cf

        # make term-doc mat
        term_by_doc_mat = self._make_term_by_doc_mat(vocab)

        # make sim mat
        sim_mat = self._make_sim_mat(term_by_doc_mat)

        return vocab, sim_mat

    def check_memory(self):
        # check that memory is sufficient
        shape = (self.specs.vocab_size, self.specs.corpus_size)
        try:
            init_mat = np.zeros(shape, dtype=np.int16)
            num_mbs = init_mat.nbytes / 1e6
            print('Successfully initialized matrix with shape={} requiring {} megabytes'.format(shape, num_mbs))
        except MemoryError:
            raise WikiNeighborsNoMemory(shape)
        else:
            del init_mat

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
