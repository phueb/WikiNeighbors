from wtforms.validators import ValidationError
from wtforms import Form, StringField

from wikineighbors import config


def make_form(request, corpus):

    # page is first loaded without any user input
    if not request.args:
        valid_set = []  # no need to do expensive validation if no request
        message = ''

    # request.args only if first attempt did not result in validation
    else:
        valid_set = corpus.vocab
        message = 'Not in vocabulary'

    def validator(_, field):
        if config.Default.text in field.data:
            raise ValidationError(message)
        if not field.data:
            raise ValidationError('Input required')
        elif any(map(lambda x: x not in valid_set, field.data.split())):
            raise ValidationError(message)
        else:
            print('Form validated: "{}"'.format(field.data))

    class WordInputForm(Form):
        field = StringField(validators=[validator])

    form = WordInputForm(request.args, field=config.Default.text)
    return form
