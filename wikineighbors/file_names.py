

def make_cached_file_name(object_name, specs):
    return '{}_{}_{}_{}.pkl'.format(object_name,
                                    specs.vocab_size,
                                    specs.corpus_size,
                                    specs.cat)


def get_corpus_size_and_cat(file_name):
    tmp = file_name.lstrip('w2dfs_').rstrip('.pkl').rpartition('_')
    return tmp[0], tmp[2]


def to_w2dfs_file_name(corpus_size, cat):
    return 'w2dfs_{}_{}.pkl'.format(corpus_size, cat)