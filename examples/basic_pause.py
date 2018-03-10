"""
This example demonstrates the usage of Pause action.
Pause help you to created something like tutorial where pause all actions until some condition is met.

author: Deniss Stepanovs
"""
from botium import Bot, Say, Intent, Pause, Event
from botium.conditions import EventCondition
from botium.ui import bot_ui, bot_cli
from botium.intents import Echo


# let's define a simple intent, so we demonstrate trigger on "intent completed"
class Pronouns(Intent):
    def score(self, message, **kwargs):
        # true if any pronoun is present in the text
        return message.text.lower() in {'i', 'you', 'he', 'she', 'it', 'they', 'we'}

    def __call__(self, *args, **kwargs):
        # just saying that pronoun is there
        return Say(text='[pronoun is present]')


# let's define a tutorial
class Tutorial(Intent):
    # must define scoring function
    def score(self, message, **kwargs):
        return message.text.lower() in {'tutorial'}

    # must define calling function
    def __call__(self, *args, **kwargs):
        return [
            Say(text="welcome to tutorial"),
            Say(text="1. please type you favorite pronoun"),
            # now pausing until the intent is done
            Pause(condition=EventCondition(event=Event(signal=Pronouns,
                                                       type='done'))),
            Say(text='nice!'),
            Say(text='type your less favorite pronoun'),
            Pause(condition=EventCondition(event=Event(signal=Pronouns,
                                                       type='done'))),
            Say(text='Great! The tutorial is finished'),
        ]


class PauseBot(Bot):
    intents = [Pronouns, Echo, Tutorial]


# creating the bot
bot = PauseBot()

# trying the bot using CLI or UI
# don't forget to start the tutorial (type "tutorial")
bot_cli(bot)
# if you want to run the bot using UI
bot_ui(bot)

# notice, memory is empty as there where no actions
bot.memory
# however, you can see that tutorial is done here
bot.events['counts']['Intent']['Tutorial']
# {'done': 1, 'n': 1}
