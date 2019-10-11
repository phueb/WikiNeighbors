class LudwigVizNoArticlesFound(Exception):
    def __init__(self, param_p, status_code=500):
        Exception.__init__(self)
        self.message = 'LudwigViz: Did not find any Wiki articles in {}'.format(param_p)
        if status_code is not None:
            self.status_code = status_code