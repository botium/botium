"""
Bot simple UI.

author: Deniss Stepanovs
"""
from flask import Flask, request, jsonify, render_template

import sys
import traceback

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/', methods=['GET'])
def index():
    return render_template('chat.html')


@app.route('/api', methods=['POST'])
def gate_in():
    try:
        data_in = request.get_json()
        text = data_in.get('text')

        app.bot.reply(text=text)
        messages = app.bot.mouth.pop_dicts()
        messages = {'messages': messages}

    except:
        traceback.print_exc(file=sys.stdout)
        messages = {"messages": [{'text': "Unfortunately, API suddenly terminated it's existence"}]}

    return jsonify(**messages)
