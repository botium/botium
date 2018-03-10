"""
This example demonstrates the usage of Trigger-s.
Trigger-s a conditional actions. They can be conditioned on user or bot behavior, on statistics, time etc.

author: Deniss Stepanovs
"""
from botium import Bot, Say, SetTrigger, Trigger, Event
from botium.conditions import CountCondition, TextCondition
from botium.signals import Message
from botium.ui import bot_ui, bot_cli
from botium.intents import Echo

import re

# we are going to set up a couple of triggers and see how they behave
# lets set the first trigger on user's message counts: bot will comment on the second message received
# by setting n=2, we tell the bot to react on a second message (from current number)
# notice, Event is set on a class (not instance) of Messages
trigger_counts = Trigger(condition=CountCondition(event=Event(signal=Message), n=2),
                         actions=Say(text='[2nd message received]'))

# next trigger will be set on users text (it is a bit similar to Intents)
# let's tell the user that he or she input number (and we repeat reminding 2 times
#
trigger_text = Trigger(
    # condition is always set on event
    condition=TextCondition(event=Event(signal=Message),
                            # several options on text (similar to action Ask)
                            options=['one', 'two', 'three', re.compile(r'(\d+)')]),
    # keep the trigger for two times
    n=2,
    actions=Say(text='[number received]'))

# defining the bot that just echos everything
class EchoBot(Bot):
    intents = [Echo]

# creating the bot
bot = EchoBot()

# setting up the triggers using corresponding action
bot.do(actions=[SetTrigger(trigger=trigger_counts.copy()),
                SetTrigger(trigger=trigger_text.copy())])

# lets explore how triggers are set
# in the bot's state (it is json dict)
bot.state['Triggers']
# directly in Trigger area
bot.triggers

# trying the bot using CLI or UI
# try to input text and numbers
bot_cli(bot)
# if you want to run the bot using UI
bot_ui(bot)
