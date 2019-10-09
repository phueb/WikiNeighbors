from flask import Flask, redirect, url_for
from flask import render_template
from flask import request
import argparse
import socket

import wikineighbors

hostname = socket.gethostname()

app = Flask(__name__)


# ------------------------------------------------ views

@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect(url_for('corpora', project_name='CreateWikiCorpus'))


@app.route('/<string:project_name>', methods=['GET', 'POST'])
def corpora(project_name):
    headers, rows = make_corpus_headers_and_rows(project_name)  # returns 1 row per corpus not per param_name
    # sort
    if rows:
        header = request.args.get('header') or config.Default.header
        order = request.args.get('order') or config.Default.order
        rows = sort_rows(rows, header, order)

    return render_template('corpora.html',
                           topbar_dict=topbar_dict,
                           project_name=project_name,
                           rows=rows,
                           headers=headers)


@app.route('/<string:project_name>/<string:corpus_name>', methods=['GET', 'POST'])
def neighbors(project_name, corpus_name):
    param_names = []
    parts = set()
    for param_name in gen_param_names_to_100(corpus_name):  # careful with infinite loop
        param_path = to_param_path(project_name, param_name)

        # make sure path exists
        if not param_path.exists():
            break  # this break is required, else infinite loop

        # make sure that param_name is valid (that it really is part of the corpus)
        params = Params(param_path)
        if params.part in parts:
            continue  # this happens because param_names are generated by returning all 8 possible param_names
        parts.add(params.part)

        # check that articles are available (bodies.txt files)
        body_paths = [p for p in param_path.rglob('bodies.txt')]
        num_bodies = len(body_paths)
        if num_bodies == 0:
            raise LudwigVizNoArticlesFound(param_path)
        elif num_bodies > 1:
            raise SystemError('Found more than 1 bodies.txt files in {}'.format(param_name))

        param_names.append(param_name)

    return render_template('neighbors.html',
                           topbar_dict=topbar_dict,
                           project_name=project_name,
                           param_names=param_names,
                           corpus_name=corpus_name,
                           num_param_names=len(param_names)
                           )


# ----------------------------------------------- ajax

@app.route('/which_hidden_btns/', methods=['GET'])
def which_hidden_btns():
    """
    count how many checkboxes clicked on corpora.html to determine which buttons are legal
    """
    num_checkboxes_clicked = int(request.args.get('num_checkboxes_clicked'))
    if num_checkboxes_clicked == 2:
        result = 'both'
    elif num_checkboxes_clicked > 0:
        result = 'any'
    else:
        result = 'none'
    return result


# -------------------------------------------- error handling

class LudwigVizNoArticlesFound(Exception):
    def __init__(self, param_p, status_code=500):
        Exception.__init__(self)
        self.message = 'LudwigViz: Did not find any Wiki articles in {}'.format(param_p)
        if status_code is not None:
            self.status_code = status_code


@app.errorhandler(LudwigVizNoArticlesFound)
def handle_not_found_error(exception):
    return render_template('error.html',
                           message=exception.message,
                           status_code=500,
                           topbar_dict=topbar_dict)


@app.errorhandler(500)
def handle_app_error(exception):
    return render_template('error.html',
                           message=exception,
                           status_code=500,
                           topbar_dict=topbar_dict)


@app.errorhandler(404)
def page_not_found(exception):
    return render_template('error.html',
                           message=exception,
                           status_code=404,
                           topbar_dict=topbar_dict)


# -------------------------------------------- start app from CL


if __name__ == "__main__":  # pycharm does not use this
    parser = argparse.ArgumentParser()
    parser.add_argument('--no_debug', action="store_false", default=True, dest='debug',
                        help='Use this for deployment.')
    parser.add_argument('--dummy', action="store_true", default=False, dest='dummy',
                        help='Use a dummy directory - in case mounting does not work')
    namespace = parser.parse_args()

    if namespace.dummy:
        wikineighbors.dummy_data = 'dummy_data'
        print('Using dummy data')

    # import after specifying path to data
    from wikineighbors import config
    from wikineighbors.io import make_corpus_headers_and_rows
    from wikineighbors.io import gen_param_names_to_100
    from wikineighbors.io import Params
    from wikineighbors.utils import sort_rows
    from wikineighbors.utils import to_param_path

    topbar_dict = {'listing': config.RemoteDirs.research_data,
                   'hostname': hostname,
                   'version': wikineighbors.__version__,
                   'title': wikineighbors.__package__.capitalize()
                   }

    app.secret_key = 'ja0f09'
    app.run(port=5000, debug=namespace.debug, host='0.0.0.0')
