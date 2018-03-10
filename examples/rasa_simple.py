"""
This is an illustration of Rasa integration with the bot.
It is basically a template for Rasa integration.
You can find more sophisticated (standard) illustration in the corresponding example.

Rasa is used only for intent recognition (intent_ranking in Rasa).

Notice! Only rasa NLU (but not dialog) part is integrated.

author: Deniss Stepanovs
"""
from botium import Bot, Intent, Say
from botium.nlp import RasaNlp
from botium.ui import bot_ui, bot_cli

# dataset is about restaraunt (taken from Rasa)
# it has the following intents: ["greet", "goodbye", "affirm", "restaurant_search"]
# Important! default spacy 'en' model uses context-vectors.
# It is much better to use "semantic-" ones (lang="en_core_web_lg")
nlp = RasaNlp(r"./examples/data/rasa_dataset.md", lang='en')

# we need to create the corresponding intents, but setting scores to zero
class Greet(Intent):
    def score(self, message, **kwargs):
        return 0

    def __call__(self, *args, **kwargs):
        return Say(text="<%s>" % self._name)


class Goodbye(Intent):
    def score(self, message, **kwargs):
        return 0

    def __call__(self, *args, **kwargs):
        return Say(text="<%s>" % self._name)


class Affirm(Intent):
    def score(self, message, **kwargs):
        return 0

    def __call__(self, *args, **kwargs):
        return Say(text="<%s>" % self._name)


class RestaurantSearch(Intent):
    def score(self, message, **kwargs):
        return 0

    def __call__(self, *args, **kwargs):
        return Say(text="<%s>" % self._name)

# INTENT not present in the trainig dataset
# Let's define an intent that will control the behaviour of those in the dataset
#   - if confidence of the best intent is not that great, we tell that we are not certain
class Uncertain(Intent):
    def score(self, message, **kwargs):
        # besides user text, message contains entities and intents (ordered)
        confidence_level = 0.7
        return message._intents[0]['confidence'] < confidence_level

    def __call__(self, *args, **kwargs):
        return Say(text="<%s>" % self._name)


# defining the bot, providing all intents
class RasaRestaurantBot(Bot):
    intents = [Greet, Goodbye, Affirm, RestaurantSearch, Uncertain]


# creating the bot: don't forget to plug in the nlp-engine
bot = RasaRestaurantBot(nlp=nlp)

# in shell test:
bot.reply(text='i need food')
# assert bot.mouth[0].text == "<RestaurantSearch>."
bot.reply(text='What is the weather like in Heidelberg?')
# assert bot.mouth[1].text == "<Uncertain>."

# try it using CLI or UI
bot_cli(bot)
bot_ui(bot)
