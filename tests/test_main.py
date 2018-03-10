"""
Many tests, high coverage, but a bit messy.

author: Deniss Stepanovs
"""
from time import sleep
import unittest
from botium import *
from botium.entities import *
from botium.signals import *
from botium.utils import *
from botium.ui import bot_ui
from botium.intents import *
from botium.bots import TestBot
from botium.conditions import *
from botium.nlp import TestNlp

config.SHOW_WELCOME_MESSAGE = False


# config.MODE = 'test'


class AskMe(Intent):
    def score(self, message, **kwargs):
        text = message.text
        return int(text.startswith('ask'))

    def __call__(self, *args, **kwargs):
        return [Ask(text=self.message.text.replace('ask', '').strip()), Say(text='Asked!')]


import logging

logging.getLogger().setLevel(logging.WARNING)


class botiumTest(unittest.TestCase):
    TEXT = 'hi'
    TEXT_2 = 'yahoo!'

    QUESTION = 'how are you?'
    ANSWER = 'good'

    RENAME_QUESTION = 'asking'
    RENAME_ANSWER = 'response'
    RENAME_KEY = 'yo'
    RENAME_WHERE = 'items'

    STORE_KEY = 'keys.mykey'
    STORE_VALUE = {'hi': 'hola'}

    # signals

    @property
    def message(self):
        return Message(text=self.TEXT)

    @property
    def event(self):
        return Event(signal=Message(text=self.TEXT))

    @property
    def condition_occ(self):
        return EventCondition(event=Event(signal=Message))

    @property
    def condition_count(self):
        return CountCondition(event=Event(signal=Message),
                              n=2)

    @property
    def condition_text(self):
        return TextCondition(event=Event(signal=Message), options=['hi'])

    @property
    def trigger(self):
        return Trigger(condition=self.condition_occ,
                       actions=Say(text=self.TEXT_2))

    @property
    def set_trigger_instant(self):
        return SetTrigger(
            trigger=Trigger(condition=self.condition_occ,
                            actions=Say(text=self.TEXT_2),
                            instant=True))

    @property
    def trigger_counts(self):
        return Trigger(condition=self.condition_count,
                       actions=Say(text=self.TEXT_2))

    @property
    def set_trigger(self):
        return SetTrigger(
            trigger=Trigger(condition=self.condition_occ,
                            actions=Say(text=self.TEXT_2)))

    # actions
    @property
    def say(self):
        return Say(text=self.TEXT)

    @property
    def ask(self):
        return Ask(text=self.QUESTION, options=[self.ANSWER, 'bad'])

    @property
    def ask_options(self):
        return Ask(text=self.QUESTION, options=[self.ANSWER,
                                                str, 'bad',
                                                int, float, 2, 5.1,
                                                bool, True,
                                                re.compile(r"([asf]+)", re.UNICODE),
                                                NamedEntity(name='age')])

    @property
    def ask_no_options(self):
        return Ask(text=self.QUESTION)

    @property
    def ask_action(self):
        return Ask(text=self.QUESTION,
                   options=[self.ANSWER, 'bad'],
                   actions={self.ANSWER: Say(text=self.TEXT_2)})

    @property
    def ask_store_rename(self):
        return Ask(text=self.QUESTION,
                   options=[self.ANSWER, 'bad'],
                   rename={'question': self.RENAME_QUESTION,
                           'answer': self.RENAME_ANSWER,
                           'key': self.RENAME_KEY,
                           'where': self.RENAME_WHERE},
                   store=self.STORE_VALUE)

    @property
    def clarify(self):
        return Clarify(ask=Ask(text=self.QUESTION, options=[self.ANSWER, 'bad']),
                       response=Response(confidence=0, match='asdf', message=Message(text='asdf')))

    @property
    def confirm(self):
        return Confirm(yes=Say(text='yeap'), no=Say(text='nope'))

    @property
    def store(self):
        return Store(data={self.STORE_KEY: self.STORE_VALUE})

    # stop = Stop()
    @property
    def pause(self):
        return Pause(condition=self.condition_occ)

    @property
    def clear(self):
        return Clear(area=['attention', 'actions'])

    # intent
    @property
    def intent(self):
        return Echo(message=Message(text=self.TEXT))

    @property
    def desire(self):
        return Desire(actions=Say(text=self.TEXT))

    @classmethod
    def setUpClass(cls):
        ''''''

    def test_bot_validate(self):
        # validating
        bot = TestBot()
        bot.validate()

    def test_action_json_restore(self):
        # inherited
        class SayTruth(Say):
            pass

        say_truth = SayTruth(text='truth')

        all_entities = dict(
            Signal=[self.message, self.desire,
                    self.event, self.trigger],
            Condition=[self.condition_occ, self.condition_count, self.condition_text],
            Action=[self.set_trigger_instant, self.set_trigger,
                    self.say,
                    self.ask, self.ask_options, self.ask_no_options, self.ask_action, self.ask_store_rename,
                    self.clarify, self.confirm,
                    self.store,
                    self.pause,
                    # home-made
                    say_truth,
                    Store(data={'@s@Sayz@@': {'text': 'hi'}}),
                    Store(data={'@s@Say@@': {'text': 'hi'}})
                    ],
            Intent=[self.intent])

        for signal_type, signals in all_entities.items():
            for signal in signals:
                self.assertTrue(signal._type == signal_type)
                self.assertTrue(signal == Entity._restore(signal._json))

    def test_sensors(self):
        bot = TestBot()
        bot.reply(text=self.TEXT)
        self.assertTrue("ECHO" in bot.mouth[0]['text'])

        bot.do(actions=self.say)
        self.assertTrue(equal_texts(self.TEXT, bot.mouth[1]['text']))

    def test_action_say(self):
        config.MODE = 'test'

        bot = Bot()

        say = Say(text=['hi', 'hola'])
        bot.do(actions=say)
        self.assertTrue(equal_texts('hi', bot.mouth[0]['text']) or equal_texts('hola', bot.mouth[0]['text']))

        bot = Bot()
        bot.do(actions=self.say)
        self.assertTrue(equal_texts(self.TEXT, bot.mouth[0]['text']))
        self.assertTrue(is_empty(bot.state))

    def test_action_store(self):
        bot = Bot()
        bot.do(actions=self.store)
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue(
            self.STORE_VALUE == bot.state['Memory'][self.STORE_KEY.split('.')[0]][self.STORE_KEY.split('.')[1]])

    def test_action_ask(self):
        # --------------
        # ASK+ACTION WITH PERFECT ANSWER
        # --------------
        # asking
        bot = Bot()
        bot.do(actions=self.ask_action)
        self.assertTrue(equal_texts(self.QUESTION, bot.mouth[0]['text']))
        # time is registered
        self.assertTrue('_time' in get_dict_value(bot.state['Attention']['focus']))
        self.assertTrue(compare_actions(bot.state['Attention']['focus'], self.ask_action._json))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        # perfect answer with action
        bot.reply(text='good')
        if config.STORE_TIME:
            self.assertTrue(is_empty(bot.state, but={'Memory'}))
            d = get_dict_value(bot.state['Memory']['general'])
            # self.assertTrue({'answer', 'question', 'answer_time', 'question_time', 'match'}.issubset(d))
            self.assertTrue(type(d['question']) == str)
            self.assertTrue(type(d['answer']) == str)
            self.assertTrue(type(d['match']) == str)
            self.assertTrue(type(d['question_time']) == int)
            self.assertTrue(type(d['answer_time']) == int)
            self.assertTrue(d['question_time'] <= d['answer_time'])
        else:
            self.assertTrue(is_empty(bot.state))

        self.assertTrue(len(bot.mouth) == 2)

        # perfect answer without action
        bot = Bot()
        bot.do(actions=self.ask_action)
        bot.reply(text='bad')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue(len(bot.mouth) == 1)

        # -------------------- #
        # CLARIFY ANSWER - YES #
        # -------------------- #
        # asking
        bot = Bot()  # test mode is needed to check presence on "option" in the answer
        bot.do(actions=self.ask_action)

        # clarify answer
        bot.reply(text='goo')
        # bot.areas['actions']._state
        self.assertTrue(len(bot.state['Attention']) == 1)
        self.assertTrue(set(bot.mouth[1]['options']) == set(config.CONFIRM_OPTIONS))

        # yes
        bot.reply(text='yes')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue({'answer', 'question'}.issubset(list(bot.state['Memory']['general'].values())[0]))
        self.assertTrue(len(bot.mouth) == 3)

        # ------------------- #
        # CLARIFY ANSWER - NO #
        # ------------------- #
        # asking
        bot = Bot()
        bot.do(actions=self.ask)
        # clarify answer
        bot.reply(text='hz')
        # actions have an event for the intent end
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        self.assertTrue(compare_actions(self.ask._json, bot.state['Attention']['focus']))
        self.assertTrue(len(bot.mouth) == 3)

        bot = Bot(state=bot.state)
        bot.reply(text='z')

        # ------------------------- #
        # STORING PLUS ( WITH RENAMING) ANSWER #
        # ------------------------- #

        # asking
        bot = Bot()
        bot.do(actions=self.ask_store_rename)
        bot.reply(text='good')
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue({self.RENAME_ANSWER, self.RENAME_QUESTION, list(self.STORE_VALUE.keys())[0]}.issubset(
            bot.state['Memory'][self.RENAME_WHERE][self.RENAME_KEY]))

        # -------------------------------- #
        # STORING WITH NO OPTIONS QUESTION #
        # -------------------------------- #
        # asking
        bot = Bot()
        bot.do(actions=self.ask_no_options)
        bot.reply(text=self.TEXT)
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue({'answer', 'question'}.issubset(list(bot.state['Memory']['general'].values())[0]))

        # STORING (with NamedEntity)
        bot = Bot(nlp=TestNlp())
        # bot = Bot()
        bot.do(actions=Ask(text='your name?', options=NamedEntity(name='name')))
        bot.reply(text="my name is bob")
        d = get_dict_value(bot.state['Memory']['general'])
        self.assertTrue(d['match'] == 'bob')

        # message = Message(text='my name is bob')
        # message.attach_nlp(TestNlp())
        # message._intents

    def test_action_clear(self):
        bot = Bot()
        bot.do(actions=self.ask_action)
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.do(actions=self.clear)
        Clear(area=['attention'])

    def test_action_ask_repeat_indirect_options(self):
        TEXT = "i don't know"

        def bot_at_choice():
            bot = Bot(nlp=TestNlp())
            bot.do(actions=Ask(text='where are you from?', options=NamedEntity(name='location')))
            self.assertTrue(is_empty(bot.state, but={'Attention'}))
            for i in range(config.RESPONSE_REPEAT_N):
                bot.reply(text=TEXT)

                if i == 0:
                    # REPEATED is saved
                    self.assertTrue(bot.state['Attention']['focus']["@@Ask@@"]['_n'] == i + 2)

                if i == 0 and i != config.RESPONSE_REPEAT_N:
                    # standard repeat
                    self.assertTrue(len(bot.mouth) == 3)
                    self.assertTrue(equal_texts(config.MESSAGE_ASK_REPEAT, bot.mouth[1]['text']))

            return bot

        # REPEAT FAIL CHOICE
        bot = bot_at_choice()
        # there are answers
        # self.assertTrue(set(['no', 'yes']).issubset(bot.state['Attention']['focus']['@Clarify']['options'].keys()))
        self.assertTrue(bot.state['Attention']['focus']['@@Clarify@@']['text'] == config.MESSAGE_ASK_REPEAT_FAIL)
        self.assertTrue(is_empty(bot.state, but={'Attention'}))

        # YES
        bot = bot_at_choice()
        bot.mouth[:]
        bot.reply(text='yes')
        self.assertTrue(len(bot.mouth) == 4)
        # self.assertTrue(equal_texts(config.MESSAGE_ASK_REPEAT_FAIL_YES, bot.mouth[4]['text']))
        self.assertTrue(is_empty(bot.state, but={'Memory'}))

        # NO
        bot = bot_at_choice()
        bot.reply(text='no')
        self.assertTrue(len(bot.mouth) == 6)
        # self.assertTrue(equal_texts(config.MESSAGE_ASK_REPEAT_FAIL_NO, bot.mouth[4]['text']))
        self.assertTrue(equal_texts(config.MESSAGE_CLARIFY_NO, bot.mouth[4]['text']))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        # then answer
        m = Message(text='riga')

        bot.reply(text='riga')
        self.assertTrue(len(bot.mouth) == 6)
        self.assertTrue(is_empty(bot.state, but={'Memory'}))

        # NEITHER (some random text)
        bot = bot_at_choice()  # was your answer complete?
        bot.reply(text='neither')
        self.assertTrue(len(bot.mouth) == 6)
        self.assertTrue(is_empty(bot.state, but={'Attention'}))

        # SKIP
        config.CLARIFY_ALLOW_SKIP = True
        bot = bot_at_choice()
        # bot.state
        bot.reply(text='skip')
        self.assertTrue(len(bot.mouth) == 4)
        self.assertTrue(is_empty(bot.state, but={'Memory'}))
        self.assertTrue(get_dict_value(bot.state['Memory']['general'])['answer'] == TEXT)
        self.assertTrue(get_dict_value(bot.state['Memory']['general'])['match'] == '<skipped>')

    def test_action_ask_repeat(self):
        # DIRECT OPTIONS are given
        bot = Bot()
        bot.do(actions=self.ask)

        bot.reply(text='g')
        # try to rephrase
        self.assertTrue(equal_texts(config.MESSAGE_ASK_REPEAT_DIRECT, bot.mouth[1]['text']))
        self.assertTrue(equal_texts(self.ask.text, bot.mouth[2]['text']))

        bot.reply(text='g')
        self.assertTrue(config.MESSAGE_ASK_REPEAT_DIRECT_OPTIONS[:10] in bot.mouth[3]['text'].lower())
        self.assertTrue(equal_texts(self.ask.text, bot.mouth[4]['text']))

        bot.reply(text='g')
        self.assertTrue(config.MESSAGE_ASK_REPEAT_DIRECT_OPTIONS[:10] in bot.mouth[5]['text'].lower())
        self.assertTrue(equal_texts(self.ask.text, bot.mouth[6]['text']))

    def test_action_ask_complete_answer(self):
        bot = Bot()
        ask = Ask(
            text='what is your favorite number?',
            options=[int, 'one', 'two', 'three', re.compile(r'is ([\d]+)')],
            actions=Say(text=r'number \1 is the best')
        )

        bot.do(actions=ask.copy())
        bot.reply(text='hii')
        bot.reply(text='hiii')
        bot.reply(text='yes')

        self.assertTrue('hiii' in bot.mouth[4].text)

        bot = Bot()
        bot.do(actions=ask.copy())
        bot.reply(text='hii')
        bot.reply(text='hii')
        bot.reply(text='no')

        self.assertTrue(bot.mouth[5] == Say(delay=1300, text="What is your favorite number?"))

    def test_action_confirm(self):
        bot = Bot()
        bot.do(actions=self.confirm)
        self.assertTrue(equal_texts(config.MESSAGE_CONFIRM, bot.mouth[0]['text']))
        self.assertTrue(set(bot.mouth[0]['options']) == set(config.CONFIRM_OPTIONS.keys()))

        # so mather options work
        bot.reply(text='nope')
        self.assertTrue(equal_texts('nope', bot.mouth[1]['text']))

    def test_action_trigger(self):
        bot = TestBot()
        # setting up the trigger
        bot.do(actions=self.set_trigger)
        self.assertTrue(is_empty(bot.state, but={'Triggers'}))
        self.assertTrue(not bot.mouth)
        # triggering
        bot.reply(text=self.TEXT)

        # self = bot.triggers._state[0]

        self.assertTrue(is_empty(bot.state))
        self.assertTrue(self.TEXT in bot.mouth[0]['text'])
        self.assertTrue(equal_texts(self.TEXT_2, bot.mouth[1]['text']))

        # TRIGGER BEFORE INTENT
        bot = TestBot()
        bot.do(actions=self.set_trigger_instant)
        bot.reply(text=self.TEXT)
        self.assertTrue(is_empty(bot.state))
        self.assertTrue(equal_texts(self.TEXT_2, bot.mouth[0]['text']))
        self.assertTrue(self.TEXT in bot.mouth[1]['text'])

        # TRIGGER SET ON COUNTS (+2)
        bot = TestBot()
        bot.reply(text=self.TEXT)
        bot.do(actions=SetTrigger(trigger=self.trigger_counts))
        bot.reply(text=self.TEXT)
        self.assertTrue(not is_empty(bot.state))
        bot.reply(text=self.TEXT)
        self.assertTrue(is_empty(bot.state))
        self.assertTrue(len(bot.mouth) == 4)
        self.assertTrue(equal_texts(self.TEXT_2, bot.mouth[-1]['text']))

    def test_trigger_done(self):
        # checking counts
        bot = Bot(intents=[AskMe])

        condition = EventCondition(event=Event(signal=AskMe, type='done'))
        set_trigger_done = SetTrigger(trigger=Trigger(condition=condition, actions=Say(text=self.TEXT_2)))
        # setting up the trigger
        bot.do(actions=set_trigger_done)
        self.assertTrue(is_empty(bot.state, but={'Triggers'}))
        bot.reply(text='ask how are you?')
        self.assertTrue(is_empty(bot.state, but={'Triggers', 'Attention', 'Actions'}))
        self.assertTrue(len(bot.mouth) == 1)
        bot.reply(text='ok')
        self.assertTrue(is_empty(bot.state, but={'Memory', }))
        self.assertTrue(len(bot.mouth) == 3)
        self.assertTrue(equal_texts(self.TEXT_2, bot.mouth[2]['text']))

        # DONE on Ask
        bot = Bot()
        condition = EventCondition(event=Event(signal=Ask, type='done'))
        set_trigger_done = SetTrigger(trigger=Trigger(condition=condition, actions=Say(text=self.TEXT_2)))
        bot.do(actions=[set_trigger_done, self.ask])
        self.assertTrue(len(bot.mouth) == 1)
        bot.reply(text='good')
        self.assertTrue(len(bot.mouth) == 2)

    def test_desire(self):
        bot = Bot()
        bot.do(actions=[self.say, self.say])
        self.assertTrue(len(bot.mouth) == 2)

    def test_action_pause(self):
        bot = TestBot()
        bot.do(actions=[self.say, self.pause, self.say, self.say])
        self.assertTrue(len(bot.mouth) == 1)
        self.assertTrue(is_empty(bot.state, but={'Triggers'}))
        bot.reply(text='hey')
        self.assertTrue(len(bot.mouth) == 4)
        self.assertTrue(is_empty(bot.state))

        # extra (maybe redundant)
        bot = TestBot()
        say = Say(text="Please try it out", options=['Am I extraverted?', 'Am I introverted?'])
        pause = Pause(condition=EventCondition(event=Event(signal=Echo, type="done")))
        bot._areas['Actions'].append([say, pause])
        bot.do(actions=pause)
        self.assertTrue(is_empty(bot.state, but={'Triggers'}))

    def test_action_graph(self):
        bot = Bot(intents=[Grapher])
        bot.reply(text='start')
        self.assertTrue(is_empty(bot.state, but={'Attention', "Actions"}))
        self.assertTrue(bot.mouth[0].text == "Do you have problems in your life?")
        self.assertTrue(set(bot.mouth[0].options) == {'no', 'yes'})

        bot.reply(text='yeap')
        self.assertTrue(equal_texts(config.MESSAGE_GRAPH_WRONG_TRANSITION, bot.mouth[1].text))
        bot.reply(text='yes')
        self.assertTrue(bot.mouth[3].text == "Can you do something about it?")

        bot.reply(text='no')
        self.assertTrue(bot.mouth[4].text == "Then don't worry.")

    def test_action_attend(self):
        bot = TestBot(intents=[AttendIntent], nlp=TestNlp())
        bot.reply(text='hi')
        self.assertTrue("ECHO" in bot.mouth[0].text)
        bot.reply(text='my name is bob')

        self.assertTrue(bot.mouth[1].text == "What is your age?")
        bot.reply(text='i am 1')

        self.assertTrue(bot.mouth[2].text == "Your name is bob and age 1 years, right?")
        bot.reply(text='yes')
        d = get_dict_value(bot.memory['general'])
        self.assertTrue(len(d['attend']) == 2)
        self.assertTrue(type(d['attend_time']) == int)
        self.assertTrue(d['mission_complete'] is True)

    def test_condition_interval(self):
        bot = Bot()
        trigger = Trigger(actions=self.say,
                          condition=IntervalCondition(interval=10),
                          n=3)
        bot.do(actions=SetTrigger(trigger=trigger))
        self.assertTrue(bot.mouth.is_empty())
        bot.check()
        # bot.triggers
        self.assertTrue(bot.mouth.is_empty())
        sleep(0.025)
        bot.check()
        self.assertTrue(len(bot.mouth) == 1)

        bot.check()
        self.assertTrue(len(bot.mouth) == 1)
        sleep(0.011)
        bot.check()
        self.assertTrue(len(bot.mouth) == 2)

        bot.check()
        self.assertTrue(len(bot.mouth) == 2)
        sleep(0.011)
        bot.check()
        self.assertTrue(len(bot.mouth) == 3)

        bot.check()
        self.assertTrue(len(bot.mouth) == 3)
        sleep(0.011)
        bot.check()
        self.assertTrue(len(bot.mouth) == 3)

    # ===== #
    # AREAS #
    # ===== #

    def test_area_events(self):
        # checking counts
        bot = TestBot()
        self.assertTrue(is_empty(bot.state))
        bot.reply(text=self.TEXT)
        # works in general
        self.assertTrue({'Action', 'Intent', 'Signal'}.issubset(bot.state['Events']['counts']))
        self.assertTrue(bot.state['Events']['counts']['Action']['Say']['n'] == 1)
        bot.reply(text=self.TEXT)
        self.assertTrue(bot.state['Events']['counts']['Action']['Say']['n'] == 2)
        self.assertTrue(bot.state['Events']['counts']['Intent']['Echo']['done'] == 2)

        # LOGGING
        bot = TestBot()
        bot.reply(text=self.TEXT)
        self.assertTrue({'signal', 'signal_name', 'signal_type', 'time'}.issubset(bot._areas['Events']['log'][0]))
        self.assertTrue(bot._areas['Events']['log'][0]['signal'].text == self.TEXT)
        self.assertTrue(bot._areas['Events']['log'][0]['signal']._name == "Message")
        self.assertTrue(bot._areas['Events']['log'][1]['signal']._name == "Say")

    def test_actions(self):
        # ------- #
        # ACTIONS #
        # ------- #

        # PUSHING RESPONSE/ETC. IN THE BEGINNING of the queue
        bot = Bot()
        bot.do(actions=[self.ask, self.ask])
        # clarify answer
        bot.reply(text='hz')
        # actions have an event for the intent end
        self.assertTrue(is_empty(bot.state, but={'Attention', 'Actions'}))
        self.assertTrue(compare_actions(self.ask._json, bot.state['Attention']['focus']))
        self.assertTrue(bot.state['Actions'][0] == self.ask._json)
        self.assertTrue(len(bot.mouth) == 3)

    # ================= #
    # Config parameters #
    # ================= #
    def test_config(self):
        config.SHOW_WELCOME_MESSAGE = True
        config.MESSAGE_WELCOME = 'hi'
        bot1 = TestBot()
        bot1.reply(text='any')

        config.MESSAGE_WELCOME = 'hola'
        bot2 = TestBot()
        bot2.reply(text='any')

        self.assertTrue(bot1.mouth[0].text == 'Hi.')
        self.assertTrue(bot2.mouth[0].text == 'Hola.')

        config.SHOW_WELCOME_MESSAGE = False

    def test_ask_config(self):
        # no clarification
        config.RESPONSE_CLARIFY = False
        bot = Bot()
        bot.do(actions=self.ask)
        bot.reply(text='goo')
        self.assertTrue(len(bot.state['Attention']) == 1)
        config.RESPONSE_CLARIFY = True

        # no storing
        config.RESPONSE_STORE = False
        bot = Bot()
        bot.do(actions=self.ask)
        bot.reply(text=self.ANSWER)
        self.assertTrue(is_empty(bot.state))
        config.RESPONSE_STORE = True

    # ============= #
    # Bigger things #
    # ============= #
    def test_bot_state_restore(self):
        bot = Bot()
        bot.do(actions=[self.ask, self.set_trigger, self.ask_options, self.say, self.event])
        # trigger_json = self.trigger._json
        bot.reply(text='good')
        self.assertTrue(len(bot.mouth) == 2)
        # things saved properly
        saved_state = bot.state
        bot = Bot(saved_state, nlp=TestNlp())
        self.assertTrue(saved_state == bot.state)

        # things can act properly
        bot.reply(text='good')
        # 4 because mouth is also stored
        self.assertTrue(len(bot.mouth) == 4)
        self.assertTrue(is_empty(bot.state, but={'Memory'}))

    def test_bot_check(self):
        bot = Bot()
        time_at = current_time() + 30
        trigger = Trigger(condition=TimeCondition(time=time_at),
                          actions=self.say)
        bot.do(actions=SetTrigger(trigger=trigger))
        bot.do(actions=SetTrigger(trigger=self.trigger_counts))
        bot.do(actions=SetTrigger(trigger=self.trigger))
        self.assertTrue(bot.mouth.is_empty())
        bot.check()
        self.assertTrue(bot.mouth.is_empty())
        while current_time() < time_at + 1:
            pass
        bot.check()

        self.assertTrue(not bot.mouth.is_empty())

    # ==== #
    # BOTS #
    # ==== #
    '''
    def test_bot_simple(self):
        bot = SimpleBot()
        bot.reply(text=self.TEXT)
        self.assertTrue(is_empty(bot.state))
        self.assertTrue(len(bot.mouth) == 1)
        self.assertTrue(self.TEXT in bot.mouth[0]['text'])

        bot = SimpleBot()
        bot.do(actions=Ask(text='how are you?'))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        self.assertTrue(len(bot.mouth) == 1)
        self.assertTrue(equal_texts('how are you?', bot.mouth[0]['text']))
    '''


self = botiumTest()
