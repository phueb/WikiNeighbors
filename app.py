from flask import Flask, redirect, url_for, jsonify, session
from flask import render_template
from flask import request
import argparse
import socket
from timeit import default_timer as timer

import wikineighbors
from wikineighbors.exceptions import LudwigVizNoArticlesFound
from wikineighbors.exceptions import LudwigVizNoVocabFound
from wikineighbors import config
from wikineighbors.io import make_corpus_headers_and_rows
from wikineighbors.utils import sort_rows
from wikineighbors.utils import human_format
from wikineighbors.form import make_form
from wikineighbors.corpus import Corpus

hostname = socket.gethostname()

app = Flask(__name__)


# ------------------------------------------------ views

@app.route('/', methods=['GET', 'POST'])
def home():
    headers, rows = make_corpus_headers_and_rows()  # returns 1 row per corpus not per param_name
    # sort
    if rows:
        header = request.args.get('header') or config.Default.header
        order = request.args.get('order') or config.Default.order
        rows = sort_rows(rows, header, order)

    buttons = ['query', 'info', 'vocab']  # careful, these must also be names of URLS

    return render_template('home.html',
                           topbar_dict=topbar_dict,
                           title='Wikipedia Corpora',
                           rows=rows,
                           buttons=buttons,
                           headers=headers)


@app.route('/neighbors/<string:corpus_name>', methods=['GET', 'POST'])
def neighbors(corpus_name):
    start = timer()
    corpus = Corpus(corpus_name)

    results = []
    for word in session['words']:
        sorted_neighbors = corpus.get_neighbors(word)
        top_neighbors = sorted_neighbors[-config.Max.num_neighbors:]
        results.append('<b>{}:</b> {}'.format(word, ', '.join(top_neighbors)))

    elapsed = timer() - start
    return render_template('neighbors.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           results=results,
                           num_words=human_format(config.Max.num_words),
                           num_docs=human_format(config.Max.num_docs),
                           elapsed=elapsed
                           )


@app.route('/info/<string:corpus_name>', methods=['GET', 'POST'])
def info(corpus_name):
    corpus = Corpus(corpus_name)

    return render_template('info.html',
                           topbar_dict=topbar_dict,
                           param_names=corpus.param_names,
                           corpus_name=corpus_name,
                           num_param_names=corpus.num_param_names,
                           paths_to_txt_files=corpus.txt_paths
                           )


# ----------------------------------------------- views with actions

@app.route('/autocomplete/<string:corpus_name>', methods=['GET'])
def autocomplete(corpus_name):
    corpus = Corpus(corpus_name)

    # TODO or load all vocabs in when app starts?

    return jsonify(json_list=corpus.vocab)


@app.route('/query/<string:corpus_name>', methods=['GET', 'POST'])
def query(corpus_name):
    corpus = Corpus(corpus_name)

    if not corpus.cached_vocab_sizes:
        return redirect(url_for('e'))

    # form
    form = make_form(request, corpus)

    # TODO to use autocomplete AND query multiple words, add a
    #  button which adds another form that user can click (multiple times)

    # TODO is running app on server faster?

    # calculate neighbors or return back here
    if form.validate():
        words = form.field.data.split()  # TODO only allow a single word per form - string, not list
        session['words'] = words
        return redirect(url_for('neighbors', corpus_name=corpus_name))
    else:
        return render_template('query.html',
                               topbar_dict=topbar_dict,
                               corpus_name=corpus_name,
                               form=form,
                               )


@app.route('/cache_vocab/<string:corpus_name>', methods=['GET', 'POST'])
def cache_vocab(corpus_name):
    corpus = Corpus(corpus_name)

    sizes = request.args.getlist('size')
    if not sizes:
        return redirect(url_for('vocab', corpus_name=corpus_name))

    for size in sizes:
        vocab_size = int(size)
        corpus.save_vocab_to_disk(vocab_size)

    return redirect(url_for('vocab', corpus_name=corpus_name))


@app.route('/vocab/<string:corpus_name>', methods=['GET', 'POST'])
def vocab(corpus_name):
    corpus = Corpus(corpus_name)

    uncached_vocab_sizes = [s for s in config.Corpus.vocab_sizes
                            if s not in corpus.cached_vocab_sizes]
    return render_template('vocab.html',
                           topbar_dict=topbar_dict,
                           param_names=corpus.param_names,
                           corpus_name=corpus_name,
                           uncached_vocab_sizes=uncached_vocab_sizes,
                           cached_vocab_sizes=corpus.cached_vocab_sizes,
                           )

# -------------------------------------------- error handling


@app.errorhandler(LudwigVizNoArticlesFound)
def handler(exception):
    return render_template('error.html',
                           message=exception.message,
                           status_code=500,
                           topbar_dict=topbar_dict)


@app.errorhandler(LudwigVizNoVocabFound)
def handler(exception):
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
    namespace = parser.parse_args()

    topbar_dict = {'listing': config.RemoteDirs.research_data,
                   'hostname': hostname,
                   'version': wikineighbors.__version__,
                   'title': wikineighbors.__package__.capitalize()
                   }

    app.secret_key = 'ja0f09'
    app.run(port=5000, debug=namespace.debug, host='0.0.0.0')
