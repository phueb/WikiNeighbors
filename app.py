from flask import Flask, redirect, url_for, jsonify, session
from flask import render_template
from flask import request
import argparse
import pygal
import socket
from timeit import default_timer as timer
from wtforms import Form, StringField

import wikineighbors
from wikineighbors.exceptions import WikiNeighborsNoArticlesFound
from wikineighbors.exceptions import WikiNeighborsNoVocabFound
from wikineighbors.exceptions import WikiNeighborsNoMemory

hostname = socket.gethostname()

app = Flask(__name__)


# ------------------------------------------------ views

@app.route('/', methods=['GET', 'POST'])
def home():
    headers, rows, buttons = make_home_data()  # returns 1 row per corpus not per param_name
    # sort
    if rows:
        header = request.args.get('header') or config.Default.header
        order = request.args.get('order') or config.Default.order
        rows = sort_rows(rows, header, order)

    return render_template('home.html',
                           topbar_dict=topbar_dict,
                           title='Wikipedia Corpora',
                           rows=rows,
                           buttons=buttons,
                           headers=headers)


@app.route('/info/<string:corpus_name>', methods=['GET', 'POST'])
def info(corpus_name):
    corpus = Corpus(corpus_name)

    return render_template('info.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           num_param_names=corpus.num_param_names,
                           paths_to_txt_files=corpus.txt_paths
                           )


@app.route('/query/<string:corpus_name>', methods=['GET', 'POST'])
def query(corpus_name):

    if request.args.get('reset'):
        session.clear()  # don't autofill fields with user's previous words

    if not session.get('error_messages', []):
        error_message = ''
        fields = [(config.Default.word, error_message)
                  for _ in range(config.Max.num_fields)]
    else:
        fields = [(word, error_message)
                  for word, error_message in zip(session['words'], session['error_messages'])]

    return render_template('query.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           fields=fields,
                           )


@app.route('/vocab/<string:corpus_name>', methods=['GET', 'POST'])
def vocab(corpus_name):
    corpus = Corpus(corpus_name)

    return render_template('vocab.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           cats=config.Corpus.cats,
                           vocab_sizes=config.Corpus.vocab_sizes,
                           cached_vocab_names=corpus.cached_vocab_names,
                           )


@app.route('/neighbors/<string:corpus_name>', methods=['GET', 'POST'])
def neighbors(corpus_name):
    start = timer()
    corpus = Corpus(corpus_name)

    results = []
    for word in session['validated_words']:
        sorted_neighbors, sorted_sims = corpus.get_neighbors(word)
        top_neighbors = sorted_neighbors[-config.Max.num_neighbors:][::-1]
        top_sims = sorted_sims[-config.Max.num_neighbors:][::-1]
        # chart - will be converted to table
        chart = pygal.Bar()
        chart.add('cosine', [s.round(2) for s in top_sims])
        chart.x_labels = ['{:<20}'.format(n) for n in top_neighbors]
        table = chart.render_table(style=False)
        res = (word, table)
        results.append(res)

    elapsed = timer() - start
    return render_template('neighbors.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           words=session['validated_words'],
                           results=results,
                           num_words=human_format(corpus.cached_vocab_sizes[-1]),
                           num_docs=human_format(config.Max.num_docs),
                           elapsed=elapsed
                           )

# ----------------------------------------------- non-views


@app.route('/autocomplete/<string:corpus_name>', methods=['GET'])
def autocomplete(corpus_name):
    corpus = Corpus(corpus_name)
    return jsonify(json_list=corpus.vocab)


@app.route('/validate/<string:corpus_name>', methods=['GET', 'POST'])
def validate(corpus_name):
    corpus = Corpus(corpus_name)
    err_message = 'Not in vocab'

    words = session['words'] = request.args.getlist('word')
    session['validated_words'] = []
    session['error_messages'] = []
    for n, word in enumerate(words):
        if word == config.Default.word:
            session['error_messages'].append('')
        elif word not in corpus.vocab:
            session['error_messages'].append(err_message)
        else:
            session['error_messages'].append('')
            session['validated_words'].append(word)

    if err_message in session['error_messages']:
        return redirect(url_for('query', corpus_name=corpus_name))
    else:
        return redirect(url_for('neighbors', corpus_name=corpus_name))


@app.route('/cache_vocab/<string:corpus_name>', methods=['GET', 'POST'])
def cache_vocab(corpus_name):
    corpus = Corpus(corpus_name)

    cat = request.args.get('cat') or config.Default.cat  # use words that are only in chosen POS category
    sizes = request.args.getlist('size')
    if not sizes:
        return render_template('error.html',
                               message='No vocabulary size selected',
                               status_code=500,
                               topbar_dict=topbar_dict)

    for size in sizes:
        vocab_size = int(size)
        corpus.save_to_disk(vocab_size, cat)  # saves vocab + sim mat
    return redirect(url_for('vocab', corpus_name=corpus_name))

# -------------------------------------------- error handling


@app.errorhandler(WikiNeighborsNoArticlesFound)
def handler(exception):
    return render_template('error.html',
                           message=exception.message,
                           status_code=500,
                           topbar_dict=topbar_dict)


@app.errorhandler(WikiNeighborsNoVocabFound)
def handler(exception):
    return render_template('error.html',
                           message=exception.message,
                           status_code=500,
                           topbar_dict=topbar_dict)


@app.errorhandler(WikiNeighborsNoMemory)
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
    parser.add_argument('--no-debug', action="store_false", default=True, dest='debug',
                        help='Use this for deployment.')
    parser.add_argument('--s76', action="store_true", default=False, dest='s76',
                        help='If running app on server where Wiki data is stored.')
    namespace = parser.parse_args()

    if namespace.s76:
        wikineighbors.s76 = True
        print('Changing path to shared drive because --s76')

    # import after setting s76

    from wikineighbors import config
    from wikineighbors.io import make_home_data
    from wikineighbors.utils import sort_rows
    from wikineighbors.utils import human_format
    from wikineighbors.corpus import Corpus

    class WordInputForm(Form):
        word = StringField()
        msg = ''

    topbar_dict = {'listing': config.RemoteDirs.research_data,
                   'hostname': hostname,
                   'version': wikineighbors.__version__,
                   'title': wikineighbors.__package__.capitalize()
                   }

    app.secret_key = 'ja0f09'
    app.run(port=5000, debug=namespace.debug, host='0.0.0.0')
