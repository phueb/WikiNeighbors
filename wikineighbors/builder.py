import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import tempfile
from joblib import load, dump, Parallel, delayed
from pathlib import Path
from sklearn.decomposition import TruncatedSVD
from collections import Counter
from cached_property import cached_property
from scipy.sparse import csr_matrix
import shutil

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

        # TODO test
        self.mmap_path = Path(tempfile.mkdtemp()) / 'term_doc_mat.mmap'
        if self.mmap_path.exists():
            shutil.rmtree(str(self.mmap_path.parent))

    def build_and_save(self):
        vocab, sim_mat = self._build()
        self._save_to_disk(vocab, sim_mat)
        del vocab
        del sim_mat

    def _build(self):
        # make w2cf (word 2 corpus-frequency)
        w2cf = Counter()
        chunk_sizes = []
        for w2dfs_path in self.w2dfs_paths:
            with w2dfs_path.open('rb') as f:
                w2dfs = pickle.load(f)
            chunk_size = len(w2dfs)
            print(f'Loaded {chunk_size} w2dfs from {w2dfs_path}')
            for w2df in w2dfs:
                w2cf.update(w2df)
            chunk_sizes.append(chunk_size)
            del w2dfs  # otherwise twice as much memory is used
        print(f'Loaded {sum(chunk_sizes)} w2dfs from disk')

        # make vocab
        vocab = self._make_vocab(w2cf)
        del w2cf

        # make term-doc mat
        term_by_doc_mat = self._make_term_by_doc_mat(vocab, chunk_sizes)

        # make sim mat
        sim_mat = self._make_sim_mat(term_by_doc_mat)

        return vocab, sim_mat

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

        print(f'Final vocab size={len(vocab)}')
        print(f'Excluded {num_too_big} words that had more than {config.Sims.max_word_size} characters')

        return list(vocab)

    def _make_term_by_doc_mat(self, vocab, chunk_sizes):
        init_mat = self.init_term_doc_mat()
        print('Dumping initialized matrix to disk')
        dump(init_mat, self.mmap_path)  # dump large array to file for mem-mapping
        print('Deleting in-memory object')
        del init_mat  # in-memory object can be deleted

        # If data are opened using the w+ or r+ mode in the main program,
        # the worker will get r+ mode access.
        # Thus the worker will be able to write its results directly to the original data,
        # alleviating the need of the serialization to send back the results to the parent process.
        print('Loading mem-mapped object')
        res = load(self.mmap_path, 'r+')

        print('Making term-by-doc matrix...')
        memmap_chunks = np.hsplit(res, np.cumsum(chunk_sizes[:-1]))

        # TODO last chunk is abnormally small
        for c in memmap_chunks:
            print(c.shape)
        print(len(memmap_chunks), len(self.w2dfs_paths))

        num_workers = 2  # do not use more than 2 if not more than 32GB memory is available
        Parallel(n_jobs=num_workers, max_nbytes=None)(
            delayed(_make_term_by_window_mat_chunk)(memmap_chunk, w2dfs_path, vocab)
            for memmap_chunk, w2dfs_path in zip(memmap_chunks, self.w2dfs_paths)
        )

        print(f'Term-by-doc matrix sum={res.sum}')
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

    def init_term_doc_mat(self):
        # check that memory is sufficient
        shape = (self.specs.vocab_size, self.specs.corpus_size)
        try:
            init_mat = np.zeros(shape, dtype=np.int16)
            num_mbs = init_mat.nbytes / 1e6
            print('Successfully initialized matrix with shape={} requiring {} megabytes'.format(shape, num_mbs))
        except MemoryError:
            raise WikiNeighborsNoMemory(shape)
        else:
            return init_mat

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


def _make_term_by_window_mat_chunk(memmap_chunk, w2dfs_path, vocab):
    print('Starting worker', flush=True)

    with w2dfs_path.open('rb') as f:
        w2dfs = pickle.load(f)
    print('Worker loaded {}'.format(w2dfs_path))

    for col_id, w2df in enumerate(w2dfs):
        memmap_chunk[:, col_id] = [w2df.get(w, 0) for w in vocab]
    print('Worker populated memmap chunk with shape {}'.format(memmap_chunk.shape), flush=True)