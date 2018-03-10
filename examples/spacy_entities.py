"""
This is an illustration of Spacy integration.

Spacy provides a model for Named Entity Recognition. This is exactly what is being used in this example.

author: Deniss Stepanovs
"""
from botium import Bot, Say, Ask
from botium.signals import NamedEntity
from botium.intents import Echo
from botium.nlp import SpacyEntitiesNlp


# defining the bot: it will echo everything user says
class EchoBot(Bot):
    intents = [Echo]


# defining the NLP engine
nlp = SpacyEntitiesNlp(lang='en')

# creating the bot: don't forget to plug in the nlp-engine
bot = EchoBot(nlp=nlp)

# testing Echoing
bot.reply(text='hi')
# checking the log
bot.log()

# imagine, at some point you want the bot to ask a user about his favorite city
# as we will be using this action few times, let's store it
ask = Ask(text='What is your favorite city?',
          # we expect named entities: as we use spacy, we need to use spacy's naming
          # spacy has GPE and LOC for english model, though cities should be GPE, we can easily use both
          options=[NamedEntity(name='gpe'), NamedEntity(name='loc')],
          # when ask is done, let's say something
          actions=Say(text='nice location!'))

# we use .do(...) interface to force the bot doing things

# CASE 1. Long answer
bot.do(actions=ask.copy())
bot.reply(text='My favorite city is Riga.')

# checking that all is good
bot.mouth[:]
# by default all questions-answers are saved in memory-general
bot.memory['general']
# notice, both answer and match is saved


# CASE 2. Short answer: entity recognized, answer=match
# again asking
bot.do(actions=ask.copy())
# short
bot.reply(text='Riga')
bot.log()

# CASE 2. City that spacy doesn't regognize (but should!)
bot.do(actions=ask.copy())
bot.reply(text='Heidelberg')
# by default bot first asks to rephrase. We cannot do better:
bot.mouth[:]
bot.reply(text='Heidelberg')
# now bot ask to confirm that the answer is complete: yes
bot.reply(text='yes')

# as before, it is stored in memory
list(bot.memory['general'].values())

# let's check all bot's responses
bot.mouth[:]

