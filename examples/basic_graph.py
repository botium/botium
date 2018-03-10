"""
This is an illustration Graph action usage.
You will see how to define a bot's state machine.

author: Deniss Stepanovs
"""
from botium import Bot, Intent, Say, Graph, Ask
from botium.ui import bot_ui, bot_cli


# Intent to initiate graph-like (state-machine-like) behavior
class GraphIntent(Intent):
    def score(self, message, **kwargs):
        return message.text in {'start'}

    def __call__(self, *args, **kwargs):
        # creating a Graph object
        graph = Graph(
            # providing initial state
            state='start',
            # providing final state [optional]
            final='no_worries',
            # transitions using ask options (keys point to state, values to what to match)
            # text of the Ask action will be uttered when bot gets to the state
            transitions=dict(start=Ask(text='Do you have problems in your life?',
                                       options=dict(yes_problem=['yes'],
                                                    no_worries=['no'])),
                             yes_problem=Ask(text='Can you do something about it?',
                                             options=dict(no_worries=['no', 'yes'])),
                             no_worries=Ask(text="Then don't worry",
                                            options=dict()),
                             ))

        return graph


# default intent that will be activized if other (GraphIntent) is not.
class Default(Intent):
    def score(self, message, **kwargs):
        # default low score
        return 0.01

    def __call__(self, *args, **kwargs):
        # just hint what to do
        return Say(text='type "start" to... start!')


# defining the bot, providing all intents
class GraphBot(Bot):
    intents = [GraphIntent, Default]


# creating the bot
bot = GraphBot()

# trying the bot using CLI or UI
# type: start
bot_cli(bot)

# for UI
# bot_ui(bot)
