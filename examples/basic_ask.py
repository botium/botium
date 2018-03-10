"""
This is an illustration of how to use Ask action.
Ask is one of the central actions of the bot - many things are customizable.

author: Deniss Stepanovs
"""
from botium import Bot, Say, Ask
from botium.ui import bot_ui, bot_cli
from botium.intents import Echo

import re


# defining the bot that just echos everything
class EchoBot(Bot):
    intents = [Echo]


# creating the bot
bot = EchoBot()

ask = Ask(
    # quite self-explanatory question
    text='what is your favorite number?',
    # defining different options for answer
    options=[
        # int is fine
        int,
        # some strings are fine to
        'one', 'two', 'three',
        # regular expression is o
        re.compile(r'is ([\d]+)')],
    # when answered, we want to store some additional data
    store={'question_type': 'best number'},
    # by default it is stored as in 'general', we want to rename it
    rename={'where': 'faq'},
    # let's encourage the user saying that his number (repeating the number!) is great
    # to do that use \0 for text and \1 for match
    actions=Say(text=r'number \1 is the best')
)
# telling the bot to do the action and do it several time
bot.do(actions=[ask.copy(), ask.copy(), ask.copy(), ask.copy()])

# trying the bot using CLI or UI
# try: "1", "one", "... is 5", "thre" (with spelling mistake)
bot_cli(bot)
# if you want to run the bot using UI
# bot_ui(bot)

# checking the memory (stored in 'faq')
bot.memory
