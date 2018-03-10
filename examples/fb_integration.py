"""
This is an illustration how to get a bot running on Facebook.
Notice! This is development version, and is not recommended for production.

Keep in mind, a bot is not stateless, it has memory. Therefore we need to be able to store and restore bot's state.
Also, a bot should have a state per user.
We will use sqlite (again, it is only for illustration, but not for production).
We will use a Flask as a server.

author: Deniss Stepanovs
"""
import json
import requests
import sqlite3
from flask import Flask, request
from threading import Thread

from botium import Bot
from botium.intents import Echo, Grapher, NonText


# defining the bot: echos everything exept "start"
# text="start" initializes the Graph (statemachine) intent
# if voice/video/image is sent, it says "nice image"
class EchoBot(Bot):
    intents = [Echo, Grapher, NonText]


# !!!!!!!!!!!!!!!!!!
# PUT OUR STUFF HERE
ACCESS_TOKEN = None
VERIFY_TOKEN = None
# tune this if necessary
BASE_URL = 'https://graph.facebook.com/v2.11'
POST_URL = BASE_URL + '/me/messages?access_token=%s' % ACCESS_TOKEN
# !!!!!!!!!!!!!!!!!!

# creating a table if run for the first time
db = sqlite3.connect('db.sqlite3')
cursor = db.cursor()
# creating a table and index (if they doesn't exist)
cursor.execute("CREATE TABLE IF NOT EXISTS states (user_id TEXT, state TEXT);")
cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_id ON states (user_id);")
# cursor.execute("DROP TABLE states;")
db.commit()
db.close()


# main message for replying
def reply(sender_id, message_text):
    # connecting to the database (where states are stored)
    db = sqlite3.connect('db.sqlite3')
    cursor = db.cursor()

    # getting bot's state for a given user
    cursor.execute('SELECT state FROM states WHERE user_id="%s";' % sender_id)
    rows = cursor.fetchall()
    # restoring bot's state from Text
    state = json.loads(rows[0][0]) if rows else {}

    # creating a bot with a given initial state
    bot = EchoBot(state=state)
    # bot replies
    bot.reply(message_text)
    # popping all replies
    responses = bot.mouth.pop_dicts()
    # dumping bot's state
    bot_state_json = json.dumps(bot.state)
    cursor.execute('INSERT OR REPLACE INTO states VALUES(?,?)', (sender_id, bot_state_json))
    db.commit()
    db.close()

    # posting bot replies to FB
    for response in responses:
        # options -> quick_replies
        if 'options' in response:
            response['quick_replies'] = [{"content_type": "text", 'title': opt, "payload": opt} for opt in
                                         response.pop('options')]
        # serializing
        message = dict(message={k: v for k, v in response.items() if k in {'text', 'quick_replies'}},
                       recipient={'id': sender_id},
                       messaging_type="RESPONSE")

        r = requests.post(POST_URL, json=message)


app = Flask(__name__)


@app.route('/api', methods=['GET'])
def verify_token():
    # needed for verification (make sure you provided VERIFY_TOKEN)
    data_in = request.args
    if data_in.get('hub.verify_token') == VERIFY_TOKEN:
        return data_in.get('hub.challenge')
    else:
        return 'Error, invalid token'


@app.route('/api', methods=['POST'])
def gate_in():
    # getting post-data from FB
    data_in = request.json

    for j, entry in enumerate(data_in['entry']):
        if 'messaging' in entry:
            for i, message in enumerate(entry['messaging']):
                if 'message' in message:
                    if message['message'].get('is_echo'):
                        continue

                    sender_id = message['sender'].get('id')
                    message_text = message['message'].get('text')

                    if sender_id and message_text:
                        # running the bot in separate thread ( so facebook is always happy)
                        t = Thread(target=reply, args=(sender_id, message_text,))
                        t.start()

    return 'all good'


if __name__ == '__main__':
    app.run(port=8000, debug=True)
