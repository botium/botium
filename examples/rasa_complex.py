"""
This is an illustration of Rasa integration with the bot.
This is a more complex example, for a simple Rasa integration see corresponding example.

Rasa is used for entity and intent (intent_ranking in Rasa) recognition.

Notice! Only rasa NLU (but not dialog) part is integrated.

author: Deniss Stepanovs
"""
from botium import Bot, Intent, Action
from botium.actions import Say, Ask, Attend
from botium.signals import NamedEntity
from botium.intents import Stop
from botium.nlp import RasaNlp
from botium.ui import bot_ui, bot_cli
from botium.config import config

# dataset is about restaraunt (taken from Rasa)
# it has the following intents: ["greet", "goodbye", "affirm", "restaurant_search"]
# Important! default spacy 'en' model uses context-vectors.
# It is much better to use "semantic-" ones (lang="en_core_web_lg")
nlp = RasaNlp(r"./examples/data/rasa_dataset.md", lang='en')


# we need to create the corresponding intents, but setting scores to zero
# we don't create Affirm as we will use bot's action for that

# function our bot should call to get food location
def food_api(cuisine, location):
    return 'Restaurant "Mr. %s %s" is in front of you' % (cuisine.title(), location.title())


# we define a new action our bot can do
class Food(Action):
    # what action expects when created
    _structure = {'location', 'cuisine'}
    # what type action is expecting [optional]
    _prototype = dict(location=str, cuisine=str)

    # what bot does
    def __call__(self, *args, **kwargs):
        # calling some api
        # Notice! cuisine and location are attributes of the action
        text = food_api(self.cuisine, self.location)
        # saying it to the user
        return Say(text=text)


# a bit changes here
class Greet(Intent):
    def score(self, message, **kwargs):
        # we can easily add more matching words
        return message.text.lower() in {'hola'}

    def __call__(self, *args, **kwargs):
        return [Say(text="Hi, Sir!"),
                Say(text="What can I do for you?")]


# a bit changes here
class Goodbye(Intent):
    def score(self, message, **kwargs):
        # we can easily add more matching words
        return message.text.lower() in {'adios'}

    def __call__(self, *args, **kwargs):
        return [Say(text="I hope I served you well"),
                Say(text="Goodbye!")]


# We want to get what kind of food and where.
# Unless we get both entities (cuisine and location) right, we don't continue
# for this we need a special action: Attend
class RestaurantSearch(Intent):
    def score(self, message, **kwargs):
        return 0

    def __call__(self, *args, **kwargs):
        # you need a question for every named-entity
        # you need an actions when all information is obtained
        # you might need a confirmation [optional]
        return Attend(ask=[Ask(text='What cuisine you want?',
                               options=NamedEntity(name='cuisine')),
                           Ask(text='What location are you looking for?',
                               options=NamedEntity(name='location'))],
                      actions=[Say(text="your query is being processed..."),
                               Food(cuisine=r'\1', location=r'\2')],
                      confirm_text=r'Cuisine: \1, location: \2, right?')(message=self.message)


# defining the bot
class RasaRestaurantBot(Bot):
    intents = [Greet, Goodbye, RestaurantSearch]


# lets set a test mode, so we see what happens
config.MODE = 'test'
# creating the bot: don't forget to plug in the nlp-engine
bot = RasaRestaurantBot(nlp=nlp)

# in shell test:
bot.reply(text='i need food')
# at this point the intent is recognized and Attend action launched
# but we didn't specified anything else, therefore we have been asked about cuisine first
# but we will provide cuisine and location at the same time
# as long as entities are recognized, all is good
bot.reply(text='spanish cuisine in Munich')

# we confirm
bot.reply(text='right')
# food_api is called and we get a hint.
# let's check what bot said
bot.mouth[:]

# trying the bot using CLI or UI
bot_cli(bot)
bot_ui(bot)
