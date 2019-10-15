class WikiNeighborsNoArticlesFound(Exception):
    def __init__(self, param_p, status_code=500):
        Exception.__init__(self)
        self.message = 'WikiNeighbors: Did not find any Wiki articles in {}'.format(param_p)
        if status_code is not None:
            self.status_code = status_code


class WikiNeighborsNoVocabFound(Exception):
    def __init__(self, corpus_name, status_code=500):
        Exception.__init__(self)
        self.message = 'WikiNeighbors: Did not find a cached vocabulary for {}'.format(corpus_name)
        if status_code is not None:
            self.status_code = status_code


class WikiNeighborsNoMemory(Exception):
    def __init__(self, shape, status_code=500):
        Exception.__init__(self)
        self.message = 'WikiNeighbors: Not enough memory for matrix of shape {}'.format(shape)
        if status_code is not None:
            self.status_code = status_code