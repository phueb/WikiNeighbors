from flask import Flask, redirect, url_for
from flask import render_template
from flask import request, session
import argparse
import socket

import wikineighbors

hostname = socket.gethostname()

app = Flask(__name__)


# ------------------------------------------------ views

@app.route('/', methods=['GET', 'POST'])
def home():

    return redirect(url_for('project', project_name='CreateWikiCorpus'))


@app.route('/<string:project_name>', methods=['GET', 'POST'])
def project(project_name):
    headers, rows = make_params_headers_and_rows(project_name)

    # sort
    if rows:
        header = request.args.get('header') or config.Default.header
        order = request.args.get('order') or config.Default.order
        rows = sort_rows(rows, header, order)

    return render_template('project.html',
                           topbar_dict=topbar_dict,
                           project_name=project_name,
                           rows=rows,
                           headers=headers)


@app.route('/<string:project_name>/plot', methods=['GET', 'POST'])
def corpus_stats(project_name):
    """
    is requested in two ways:
    1. directly clicking on row in project.html
    2. by selecting multiple runs and clicking on "plot" button

    in case 1, param_names is retrieved from request object.
    in case 2, param_names is retrieved from session object (because of redirect)

    check request object first, and only then check session
    """

    param_names = request.args.getlist('param_name') or session.get('param_names')

    assert len(param_names) == 1  # TODO only allow 1
    first_param_path = to_param_path(project_name, param_names[0])

    # check that articles are available (bodies.txt files)
    bodies_paths = [p for p in first_param_path.rglob('bodies.txt')]
    num_bodies = len(bodies_paths)
    if not num_bodies:
        raise LudwigVizNoArticlesFound(first_param_path)

    with bodies_paths[0].open('r') as f:
        first_line = '<p>{}</p>'.format(f.readline())

    # get number of reps for each param_name
    param_name2n = {param_name: count_replications(project_name, param_name)
                    for param_name in param_names}
    return render_template('corpus_stats.html',
                           topbar_dict=topbar_dict,
                           project_name=project_name,
                           param_names=param_names,
                           param_name2n=param_name2n,
                           first_line=first_line
                           )


# ----------------------------------------------- ajax

@app.route('/which_hidden_btns/', methods=['GET'])
def which_hidden_btns():
    """
    count how many checkboxes clicked on project.html to determine which buttons are legal
    """
    num_checkboxes_clicked = int(request.args.get('num_checkboxes_clicked'))
    if num_checkboxes_clicked == 2:
        result = 'both'
    elif num_checkboxes_clicked > 0:
        result = 'any'
    else:
        result = 'none'
    return result


# -------------------------------------------- actions


@app.route('/delete_many/<string:project_name>', methods=['GET', 'POST'])
def delete_many(project_name):
    if request.args.get('delete_many') is not None:

        print(request.args)

        param_names = request.args.getlist('param_name')

        for param_name in param_names:
            delete_path = config.RemoteDirs.research_data / project_name / 'runs' / param_name
            print('Deleting {}'.format(delete_path))

            # TODO actually implement it

    return redirect(url_for('project'))


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
    from wikineighbors.io import make_params_headers_and_rows
    from wikineighbors.utils import sort_rows
    from wikineighbors.utils import to_param_path
    from wikineighbors.io import count_replications
    from wikineighbors.io import Params

    topbar_dict = {'listing': config.RemoteDirs.research_data,
                   'hostname': hostname,
                   'version': wikineighbors.__version__,
                   'title': wikineighbors.__package__.capitalize()
                   }

    app.secret_key = 'ja0f09'
    app.run(port=5000, debug=namespace.debug, host='0.0.0.0')
