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