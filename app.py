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
from wikineighbors.exceptions import WikiNeighborsNoSpecs


class WordInputForm(Form):
    word = StringField()
    msg = ''


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

    if not session.get(corpus_name):
        raise WikiNeighborsNoSpecs(corpus_name)

    if request.args.get('reset'):
        session['error_messages'] = []
        session['words'] = []  # don't autofill fields with user's previous words

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
                           corpus_sizes=config.Corpus.corpus_sizes,
                           cached_vocab_names=corpus.cached_vocab_names,
                           )


@app.route('/neighbors/<string:corpus_name>', methods=['GET', 'POST'])
def neighbors(corpus_name):
    start = timer()
    corpus = Corpus(corpus_name)
    responder = Responder.load_from_session(session, corpus)

    valid_words = session['validated_words']

    results = []
    for word in valid_words:
        sorted_neighbors, sorted_sims = responder.get_neighbors(word)
        top_neighbors = sorted_neighbors[-config.Max.num_neighbors:][::-1]
        top_sims = sorted_sims[-config.Max.num_neighbors:][::-1]
        # chart - will be converted to table
        chart = pygal.Bar()
        chart.add('cosine', [s.round(2) for s in top_sims])
        chart.x_labels = ['{:<20}'.format(n) for n in top_neighbors]
        table = chart.render_table(style=False)
        res = (word, table)
        results.append(res)

    # filtered sim table (sims between all word pairs)
    chart = pygal.Bar()
    for word in valid_words:
        sims = responder.get_sims(word, valid_words)
        chart.add(word, [s.round(2) for s in sims])
    chart.x_labels = ['{:<20}'.format(w) for w in valid_words]
    filtered_sim_table = chart.render_table(style=True)

    elapsed = timer() - start
    return render_template('neighbors.html',
                           topbar_dict=topbar_dict,
                           corpus_name=corpus_name,
                           words=valid_words,
                           results=results,
                           filtered_sim_table=filtered_sim_table,
                           num_svd_dims=config.Corpus.num_svd_dimensions,
                           num_words=human_format(responder.specs.vocab_size),
                           num_docs=human_format(responder.specs.corpus_size),
                           elapsed=elapsed
                           )

# ----------------------------------------------- non-views


@app.route('/autocomplete/<string:corpus_name>', methods=['GET'])
def autocomplete(corpus_name):
    corpus = Corpus(corpus_name)
    responder = Responder.load_from_session(session, corpus)
    return jsonify(json_list=responder.vocab)


@app.route('/validate/<string:corpus_name>', methods=['GET', 'POST'])
def validate(corpus_name):
    corpus = Corpus(corpus_name)
    responder = Responder.load_from_session(session, corpus)
    err_message = 'Not in vocab'

    words = session['words'] = request.args.getlist('word')
    session['validated_words'] = []
    session['error_messages'] = []
    for n, word in enumerate(words):
        if word == config.Default.word:
            session['error_messages'].append('')
        elif word not in responder.vocab:
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

    # specs for builder
    vocab_size = request.args.get('vocab_size')
    corpus_size = request.args.get('corpus_size')  # number of articles
    cat = request.args.get('cat')  # use words that are only in chosen POS category

    # validation
    if not vocab_size or not corpus_size or not cat:
        return render_template('error.html',
                               message='Incomplete submission',
                               status_code=500,
                               topbar_dict=topbar_dict)

    specs = Specs(vocab_size, corpus_size, cat)
    builder = SimMatBuilder(corpus, specs)
    builder.build_and_save()  # saves vocab + sim mat

    return redirect(url_for('vocab', corpus_name=corpus_name))


@app.route('/load_vocab/<string:corpus_name>', methods=['GET', 'POST'])
def load_vocab(corpus_name):

    vocab_name = request.args.get('vocab_name')
    if not vocab_name:
        return render_template('error.html',
                               message='Incomplete submission',
                               status_code=500,
                               topbar_dict=topbar_dict)

    session[corpus_name] = vocab_name
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


@app.errorhandler(WikiNeighborsNoSpecs)
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

    # import after setting s76 flag

    from wikineighbors import config
    from wikineighbors.io import make_home_data
    from wikineighbors.utils import sort_rows
    from wikineighbors.utils import human_format
    from wikineighbors.corpus import Corpus
    from wikineighbors.responder import Responder
    from wikineighbors.builder import SimMatBuilder
    from wikineighbors.params import Specs

    topbar_dict = {'listing': config.RemoteDirs.research_data,
                   'hostname': hostname,
                   'version': wikineighbors.__version__,
                   'title': wikineighbors.__package__.capitalize()
                   }

    app.secret_key = 'ja0f09'
    app.run(port=5000, debug=namespace.debug, host='0.0.0.0')
