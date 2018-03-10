"""
A few tests for ask.options.

author: Deniss Stepanovs
"""
import unittest
from botium import *
from botium.utils import *
from botium.signals import *
from botium.nlp import TestNlp
from botium.intents import Profiler
from botium.ui import bot_ui

config.SHOW_WELCOME_MESSAGE = False

import logging

logging.getLogger().setLevel(logging.WARNING)


class botiumTest(unittest.TestCase):
    TEXT = 'hi'

    def test_xxx(self):
        bot = Bot(nlp=TestNlp())
        ask = Ask(text='where are you from?', options=NamedEntity(name='location'))
        bot.do(actions=ask)

        self.assertTrue(is_empty(bot.state, but={'Attention'}))

        bot.reply(text='i am from latvia')

        bot = Bot()
        bot.do(actions=Ask(text='do you agree?', options=['agree', 'disagree']))
        bot.reply(text='AGREE')

        bot.state

    def test_action_ask_options_name(self):
        bot = Bot(nlp=TestNlp())
        bot.do(actions=Ask(text='what is your name?', options=NamedEntity(name='name')))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.reply(text='my name is deniss')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))

    def test_action_ask_options_location(self):
        bot = Bot(nlp=TestNlp())
        bot.do(actions=Ask(text='where are you from?', options=NamedEntity(name='location')))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.reply(text='i am from latvia')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))

    def test_action_ask_options_number(self):
        bot = Bot(nlp=TestNlp())
        bot.do(actions=Ask(text='how old are you?', options=NamedEntity(name='age')))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.reply(text='I am 32 years old')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))


self = botiumTest()
