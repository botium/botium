"""
Contains bot CLI and UI.

author: Deniss Stepanovs
"""
try:
    import flask
    from .app import app
except:
    print('For UI support you need to have flask (just run "pip install flask")')


def bot_cli(bot):
    def prepare_text(message):
        text = message.get('text', '')
        if message.get('options'):
            text += ' ["%s"]' % ('", "'.join(message['options']))
        return text

    print('type your text ("/exit" or /q when done)')
    # last bot's message if present
    messages = bot.mouth.pop_dicts()
    if messages:
        print("bot >?", prepare_text(messages[-1]))

    while True:
        user_text = input('you ')
        if user_text.lower() in {'/exit', '/quit'} or user_text.startswith('/q'):
            break
        bot.reply(text=user_text)
        for message in bot.mouth.pop_dicts():
            print("bot >?", prepare_text(message))


def bot_ui(bot, host="127.0.0.1", port=8008):
    app.bot = bot
    app.run(debug=False, host=host, port=port)
