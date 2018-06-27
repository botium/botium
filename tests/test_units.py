"""
Unit tests.

author: Deniss Stepanovs
"""
import unittest
from time import sleep

from botium import *
from botium.bots import TestBot
from botium.entities import Entity
from botium.intents import *
from botium.utils import *
from botium.areas import *
from botium.ui import bot_ui
from botium.nlp import TestNlp

from botium.conditions import *
from botium.intents import Echo, Stop

config.SHOW_WELCOME_MESSAGE = False

import logging

logging.getLogger().setLevel(logging.WARNING)


class botiumUnitTest(unittest.TestCase):
    """testing small units: matchers, entities, utils"""
    TEXT = 'hi'

    # ===== #
    # UTILS #
    # ===== #
    def test_clean_text(self):
        assert clean_text(' I   AM  ! ') == 'i am !'

    def test_small_things(self):
        # list_of
        self.assertTrue(list_of(None) == [])
        self.assertTrue(list_of([1, None, 2]) == [1, 2])
        self.assertTrue(list_of(1) == [1])
        self.assertTrue(list_of(None, keep_none=True) == [None])
        self.assertTrue(list_of([1, None, 2], keep_none=True) == [1, None, 2])
        self.assertTrue(list_of(1, keep_none=True) == [1])

        # is relative to
        self.assertTrue(is_relative_to(Say(text='text'), Action))
        self.assertTrue(is_relative_to(Say, Action))
        self.assertTrue(is_relative_to(Say, "@Action"))
        self.assertTrue(is_relative_to(Say, "Action"))
        self.assertTrue(is_relative_to(Say, Say))
        self.assertTrue(is_relative_to(Say, Say(text='hi')))

        # choose text
        self.assertTrue(choose_text('hi') == 'hi')
        self.assertTrue(choose_text(['hi', 'hola']) in ['hi', 'hola'])
        self.assertTrue(choose_text(Say(text='hi')) == 'hi')
        self.assertTrue(choose_text(Say(text=['hi', 'hola'])) in ['hi', 'hola'])

        # from_camel
        self.assertTrue(from_camel("hiHi") == 'hi_hi')
        self.assertTrue(from_camel("HiHiHi") == 'hi_hi_hi')
        self.assertTrue(from_camel("Hi_Hi") == 'hi_hi')
        self.assertTrue(from_camel("__hi_Hi__") == 'hi_hi')
        self.assertTrue(from_camel("__Hi__Hi__") == 'hi_hi')

        self.assertTrue(to_camel(from_camel("HiHi")) == "HiHi")
        self.assertTrue(to_camel(from_camel("Hi__Hi")) == "HiHi")
        self.assertTrue(to_camel(from_camel("__Hi__Hi__")) == "HiHi")

        self.assertTrue(is_subclass_of(Stop, Intent))
        self.assertTrue(is_subclass_of(Action, Entity))
        self.assertTrue(is_subclass_of(Ask, Action))
        self.assertTrue(not is_subclass_of(Ask, Ask))

        self.assertTrue(prepare_text('hi') == "Hi.")
        self.assertTrue(prepare_text('hi.') == "Hi.")
        self.assertTrue(prepare_text('hi!') == "Hi!")
        self.assertTrue(prepare_text('hi?') == "Hi?")
        self.assertTrue(prepare_text('"hi."') == '"Hi."')

        self.assertTrue(levenshtein('h1', 'h') < levenshtein('h21', 'h'))
        self.assertTrue(type(levenshtein_similarity('good', 'goo')) in {float, int})
        self.assertTrue(0 <= levenshtein_similarity('good', 'goo') <= 1)

        # VALIDATION
        self.assertTrue(validate_type('asf', str))
        self.assertTrue(validate_type(1, int))
        self.assertTrue(validate_type(True, bool))
        self.assertTrue(validate_type(1, [int, float]))

        self.assertTrue(validate_type([1, 2], list))
        self.assertTrue(validate_type([1, [2]], list))
        self.assertTrue(validate_type([1, 2], [int]))
        self.assertTrue(not validate_type([1, [2]], [int]))

        self.assertTrue(validate_type([1, [2]], list))
        self.assertTrue(validate_type({'x': [1, 2], 'y': [3, 4]}, {str: list}))
        self.assertTrue(validate_type(Say(text='hi'), Say))
        self.assertTrue(validate_type(Say, Say))
        self.assertTrue(validate_type([Say, Say], [Say]))

        self.assertTrue(validate_type(['b', 'c'], [str]))
        self.assertTrue(not validate_type(['b', 1], [str]))

        # regex
        self.assertTrue(validate_type([re.compile('(hi)[i]+'), re.compile('(hi)[i]+')], [re._pattern_type]))

        self.assertTrue(validate_type(NamedEntity(name='location'), NamedEntity))

    # ===== #
    # OTHER #
    # ===== #

    def test_sub_text_by_kwargs(self):
        config.MODE = 'test'
        ask = Ask(text=r'\0 is \1', actions=[Say(text=r'\0 is \1'),
                                             SetTrigger(trigger=Trigger(condition=None,
                                                                        actions=[Say(text=r'\0 is \1')]))])

        ask = Entity._restore(ask._json)

        group_kwargs = {r'\0': 'life',
                        r'\1': 'good'}
        TEXT_REPLACED = 'life is good'

        ask._text_sub_kwargs(group_kwargs)
        self.assertTrue(ask.text == TEXT_REPLACED)
        self.assertTrue(ask.actions[0].text == TEXT_REPLACED)
        self.assertTrue(ask.actions[1].trigger.actions[0].text == TEXT_REPLACED)

    def test_nlp(self):
        nlp = TestNlp()
        d = nlp('heidelberg is a great town')
        self.assertTrue({'entities', 'intents'} == set(d))

        '''
        d = nlp('my name is deniss')
        self.assertTrue(d['intent']['name'] == 'my_name')
        # self.assertTrue(d['intent']['name'] == 'MyName')
        self.assertTrue({'entity': 'name', 'value': 'deniss'} in d['entities'])

        d = nlp('i am from riga')
        self.assertTrue(d['intent']['name'] == 'my_location_from')
        # self.assertTrue(d['intent']['name'] == 'MyLocationFrom')
        self.assertTrue({'entity': 'location', 'value': 'riga'} in d['entities'])

        d = nlp('i am 32 years old')
        self.assertTrue(d['intent']['name'] == 'my_age')
        # self.assertTrue(d['intent']['name'] == 'MyAge')
        self.assertTrue({'entity': 'age', 'value': '32'} in d['entities'])
        '''

    # ======= #
    # SIGNALS #
    # ======= #
    def test_message(self):
        message = Message(text=self.TEXT)
        self.assertTrue(dict(message) == dict(text=self.TEXT))

    def test_matcher(self):
        # saving restoring
        # matcher = Matcher(options=['a', int, str, re.compile('(hi)[i]+'), NamedEntity(name='age')])
        # self.assertTrue(matcher == Entity._restore(matcher._json))

        # None
        message = Message(text='5')
        self.assertTrue(Matcher(options=None)(message) == Response(match="5", message=message, confidence=1))

        # bool
        self.assertTrue(
            Matcher(options=bool)(Message(text='TruE')) == Response(match="true", message=Message(text='TruE'),
                                                                    confidence=1))
        self.assertTrue(
            Matcher(options=bool)(Message(text='False')) == Response(match="false", message=Message(text='False'),
                                                                     confidence=1))
        self.assertTrue(
            Matcher(options=bool)(Message(text='xx')) == Response(match=None, message=Message(text='xx'), confidence=1))

        # float
        self.assertTrue(
            Matcher(options=float)(Message(text='5.1')) == Response(confidence=1, message=Message(text='5.1'),
                                                                    match='5.1'))
        self.assertTrue(
            Matcher(options=float)(Message(text='5')) == Response(confidence=1, message=Message(text='5'), match='5'))
        # self.assertTrue(Matcher(options=float)(Message(text='xx')) == )

        # int
        self.assertTrue(
            Matcher(options=int)(Message(text='5')) == Response(confidence=1, message=Message(text='5'), match='5'))
        self.assertTrue(
            Matcher(options=int)(Message(text='a')) == Response(confidence=1, message=Message(text='a'), match=None))

        self.assertTrue(
            Matcher(options=str)(Message(text='asdf')) == Response(confidence=1, message=Message(text='asdf'),
                                                                   match='asdf'))

        # str
        # self.assertTrue(Matcher(options=['a', int])(Message(text='hi')) == Response(confidence=0.001, match="a", message=Message(text='hi')))
        self.assertTrue(Matcher(options=['a', int])(Message(text='hi')) == Response(confidence=1, match=None,
                                                                                    message=Message(text='hi')))
        self.assertTrue(
            Matcher(options=['h', int])(Message(text='hi')) == Response(confidence=0.5, match="h",
                                                                        message=Message(text='hi')))

        # function
        self.assertTrue(Matcher(options=lambda x: x.text in {'hi'})(Message(text='hi')) ==
                        Response(confidence=1, match="hi", message=Message(text='hi')))
        self.assertTrue(Matcher(options=lambda x: 0.5 * (x.text in {'hi'}))(Message(text='hi')) ==
                        Response(confidence=0.5, match="hi", message=Message(text='hi')))

        # regex
        self.assertTrue(
            Matcher(options=re.compile('(hi)[i]+'))(Message(text='hiiii')) == Response(confidence=1, match="hi",
                                                                                       message=Message(text='hiiii')))
        self.assertTrue(
            Matcher(options=re.compile('(hi)[i]+'))(Message(text='11111')) == Response(confidence=1, match=None,
                                                                                       message=Message(text='11111')))

        # synonym dict
        self.assertTrue(
            Matcher(options={'yes': ['yes', 'yeah'], 'no': ['no', 'nope']})(Message(text='nope')) == Response(
                message=Message(text='nope'), match="no", confidence=1.0, entities={'no': 'nope'}))

        # not direct match
        r = Matcher(options={'yes': ['yes', 'yeah'], 'no': ['no', 'nope']})(Message(text='neither'))
        self.assertTrue(r.confidence < 0.3)

        # entity
        TEXT = 'i am 1 years old'
        message = Message(text=TEXT)
        message.attach_nlp(TestNlp())
        self.assertTrue(Matcher(options=NamedEntity(name='age'))(message) == \
                        Response(confidence=1, match="1", message=message))

        TEXT = 'my name is bob'
        message = Message(text=TEXT)
        message.attach_nlp(TestNlp())
        self.assertTrue(Matcher(options=NamedEntity(name='name'))(message) == \
                        Response(confidence=1, match="bob", message=message))

        TEXT = 'i am from heidelberg'
        message = Message(text=TEXT)
        message.attach_nlp(TestNlp())
        self.assertTrue(Matcher(options=NamedEntity(name='location'))(message) == \
                        Response(confidence=1, match="heidelberg", message=message))

        message = Message(text='who knows')
        message.attach_nlp(TestNlp())
        self.assertTrue(Matcher(options=NamedEntity(name='location'))(message) == \
                        Response(confidence=1, match=None, message=message))

    # ---------- #
    # CONDITIONS #
    # ---------- #

    def test_condition(self):
        # ON TYPE (CLASS) MATCH
        say = Say(text='hi')
        ask = Ask(text='hi')
        event = Event(signal=say)
        # event = Event(signal=Say._name)
        condition = EventCondition(event=Event(signal=Say))

        # occurrence of events
        self.assertTrue(condition(event))
        self.assertTrue(not condition(Event(signal=ask)))

        # counts
        condition = CountCondition(event=Event(signal=Say), n=2)

        events = Events(Bot())
        self.assertTrue(not condition(event, _areas={'Events': events}))
        events(say)
        self.assertTrue(not condition(event, _areas={'Events': events}))
        events(say)
        # now is true
        self.assertTrue(condition(event, _areas={'Events': events}))

        # on text
        condition = TextCondition(event=Event(signal=Say), options='hi')
        self.assertTrue(not condition(Event(signal=Say(text='text'))))
        self.assertTrue(condition(Event(signal=Say(text='hi'))))
        self.assertTrue(not condition(Event(signal=Ask(text='hi'))))
        # on any signal
        condition = TextCondition(event=Event(signal=Signal), options='hi')
        self.assertTrue(condition(Event(signal=Say(text='hi'))))
        self.assertTrue(condition(Event(signal=Ask(text='hi'))))

        # DIRECT MATCH
        message = Message(text='hola')
        # not direct
        condition = EventCondition(event=Event(signal=Message))
        self.assertTrue(condition(Event(signal=message)))
        # direct
        condition = EventCondition(event=Event(signal=message))
        self.assertTrue(not condition(Event(signal=Message(text='hahaha'))))
        self.assertTrue(condition(Event(signal=message)))

    def test_condition_time(self):
        event = Message(text='hi')
        condition = TimeCondition(time=current_time() + 5)
        self.assertTrue(not condition(event=event))
        sleep(0.006)
        self.assertTrue(condition(event))

    # =======
    def test_graph(self):

        graph = Graph(transitions=dict(a=Ask(text='<a>',
                                             options={'b': ['goto b']},
                                             actions={'b': Say(text='hey')}),
                                       b=Ask(text='<b>', options={'c': ['goto c']}),
                                       c=Ask(text='<c>',
                                             options={'a': ['goto a']})),
                      state='a',
                      final=None)

        response = Matcher(options=graph.options)(Message(text='goto b'))
        r = graph(response)
        self.assertTrue(r[0].text == 'hey')
        self.assertTrue(r[1].state == 'b')

        response = Matcher(options=graph.options)(Message(text='goto c'))
        r = graph(response)
        # self.assertTrue(r[0].text == '<c>')
        self.assertTrue(r[0].state == 'c')

        response = Matcher(options=graph.options)(Message(text='goto a'))
        r = graph(response)
        # self.assertTrue(r[0].text == '<a>')
        self.assertTrue(r[0].state == 'a')

        self.assertTrue(r[0]._path == ['a', 'b', 'c'])

        response = Matcher(options=graph.options)(Message(text='xxx'))
        r = graph(response)
        self.assertTrue(r[0].text == config.MESSAGE_GRAPH_WRONG_TRANSITION)
        self.assertTrue(r[1].state == 'a')

        message = Message(text='xxx')
        self = Matcher(options={'a': ['a', 'b']})

    def test_attend(self):
        TEXT = 'got it'

        def get_attend(confirm_text=None):
            return Attend(ask=[Ask(text='What is your name?',
                                   options=NamedEntity(name='name')),
                               Ask(text='What is your age?',
                                   options=NamedEntity(name='age'))],
                          actions=Say(text=TEXT),
                          confirm_text=confirm_text,
                          store=False)

        attend = get_attend(r'name: \1, age \2')
        # COMPLETE MATCH
        message = Message(text='my name is bob and my age is 1 year')
        message.attach_nlp(TestNlp())
        response = Matcher(options=attend.options)(message)
        r = attend(response)
        self.assertTrue(r._is(Confirm))
        self.assertTrue(r.text == "name: bob, age 1")
        self.assertTrue(all([r for r in attend._responses]))

        # PARTIAL MATCH
        attend = get_attend()
        message = Message(text='my age is 1 year')
        # message = Message(text='my name is bob')
        message.attach_nlp(TestNlp())

        response = Matcher(options=attend.options)(message)
        r = attend(response)
        self.assertTrue(attend._responses[0] is None and attend._responses[1] is not None)
        self.assertTrue(r._is(Attend))
        self.assertTrue(r._focus['i'] == 0)
        # matching the rest
        message = Message(text='my name is bob')
        message.attach_nlp(TestNlp())
        response = Matcher(options=attend.options)(message)
        r = attend(response)
        self.assertTrue(r[0].text == TEXT)
        self.assertTrue(all([r for r in attend._responses]))

        # PARTIAL MATCH + BAD RESPONSE
        attend = get_attend()
        message = Message(text='my age is 1 year')
        message.attach_nlp(TestNlp())
        response = Matcher(options=attend.options)(message)
        r = attend(response)
        # bad response
        message = Message(text='hz')
        message.attach_nlp(TestNlp())
        r = attend(Matcher(options=attend.options)(message))

        # REDEFINITION OF PREVIOUS

        message._nlp

    # ------- #
    # ACTIONS #
    # ------- #

    def test_ask(self):
        # ASK, NO ACTIONS
        # perfect match
        ask = Ask(text=self.TEXT, options=[self.TEXT, 'asdf'])
        response = Response(confidence=1, match=self.TEXT, message=Message(text=self.TEXT))
        # getting store
        self.assertTrue(ask(response)[0]._name == Store._name)

        # clarify match
        config.RESPONSE_CLARIFY = True
        ask = Ask(text=self.TEXT, options=[self.TEXT, 'asdf'])
        response = Response(confidence=config.RESPONSE_CLARIFY_CONF + 0.01, match=self.TEXT,
                            message=Message(text=self.TEXT))
        clarify = ask(response)
        self.assertTrue(clarify._name == Clarify._name)

        # no match
        ask = Ask(text=self.TEXT, options=[self.TEXT, 'asdf'])
        response = Response(confidence=0.01, match=self.TEXT, message=Message(text=self.TEXT))
        repeat = ask(response)
        self.assertTrue(repeat[0]._name == Say._name)
        self.assertTrue(compare_actions(ask, repeat[1]))

        # ASK + ACTIONS
        ask = Ask(text=self.TEXT, options=[self.TEXT, 'asdf'], actions={self.TEXT: Say(text='yo')})
        # no actions choice
        response = Response(confidence=1, match="asdf", message=Message(text=self.TEXT))
        store = ask(response)[0]
        self.assertTrue(store._name == Store._name)
        response = Response(confidence=1, match=self.TEXT, message=Message(text=self.TEXT))
        store, say, event = ask(response)
        self.assertTrue(store._is(Store))
        self.assertTrue(say._is(Say))
        self.assertTrue(event._is(Event))

    def test_action_ask_regex_matcher(self):

        say = Say(text=r'you said: "\text" (\0) that matches "\match" and "\foo" and "\1"')
        ask = Ask(text=self.TEXT,
                  options=[re.compile('(?P<foo>hi)[i]+'), 'hola'],
                  actions={'hi': say},
                  store=False)
        matcher = Matcher(options=ask.options)
        message = Message(text='hiiiiiii')
        response = matcher(message)
        action = ask(response)[0]
        self.assertTrue(action.text == 'you said: "hiiiiiii" (hiiiiiii) that matches "hi" and "hi" and "hi"')

        # TWO ENTITIES
        say = Say(text=r'two matches: "\hi" and "\bye" \1')
        ask = Ask(text=self.TEXT,
                  options=[re.compile('# ((?P<hi>hi)[i]+ (?P<bye>bye)[e]+) #'), 'hola'],
                  actions=say,
                  store=False)
        matcher = Matcher(options=ask.options)
        message = Message(text='# hiiiiiii byeeee #')
        response = matcher(message)
        action = ask(response)[0]
        self.assertTrue(action.text == 'two matches: "hi" and "bye" hiiiiiii byeeee')

    def test_action_ask_to_store(self):
        def get_store_dict(store):
            return list(store.data.values())[0]

        def check_store(store):
            store_dict = get_store_dict(store)
            patterns = [('answer_time', int), ('answer', str), ('question', str),
                        ('question_time', type(None)), ('match', str)]
            for key, t in patterns:
                if key in store_dict and type(store_dict[key]) != t:
                    return False
            return True

        ask = Ask(text='hola', options=['hola', 'hey'])
        response = Matcher(options=ask.options)(Message(text='text'))
        store = ask.to_store(response)
        self.assertTrue(check_store(store))

        ask = Ask(text='hola', options=['hola', int])
        response = Matcher(options=ask.options)(Message(text='text'))
        store = ask.to_store(response)
        self.assertTrue(check_store(store))

        ask = Ask(text='hola')
        response = Matcher(options=str)(Message(text='text'))
        store = ask.to_store(response)
        self.assertTrue(check_store(store))

        # entity matched
        ask = Ask(text='your name?', options=NamedEntity(name='name'))
        message = Message(text='my name is deniss')
        message.attach_nlp(TestNlp())
        response = Matcher(options=ask.options)(message)
        store = ask.to_store(response)
        self.assertTrue(check_store(store))

        # entity doesn't match
        ask = Ask(text='your name?', options=NamedEntity(name='name'))
        message = Message(text='who knows...')
        message.attach_nlp(TestNlp())
        response = Matcher(options=ask.options)(message)
        store = ask.to_store(response)
        self.assertTrue(check_store(store))

    def test_clarify(self):
        # ASK, NO ACTIONS

        ask = Ask(text=self.TEXT, options=[self.TEXT, 'asdf'])
        response = Response(confidence=config.RESPONSE_CLARIFY_CONF, match=self.TEXT, message=Message(text=self.TEXT))
        clarify = Clarify(ask=ask, response=response)

        response = Response(confidence=1, match='yes', message=Message(text='yes'))
        store = clarify(response)[0]
        self.assertTrue(store._name == Store._name)

        response = Response(confidence=1, match='no', message=Message(text='no'))
        say, ask_new = clarify(response)
        self.assertTrue(say._name == Say._name)
        self.assertTrue(compare_actions(ask, ask_new))

    def test_confirm(self):
        confirm = Confirm(text='yes, no', yes=Say(text='yeah'), no=Say(text='nope'))
        response = Response(confidence=1, match='yes', message=Message(text='yes'))

        # ask = Clarify(text=self.TEXT, options=[self.TEXT, 'asdf'])
        response = Response(confidence=1, match='yes', message=Message(text='yes'))
        self.assertTrue(confirm(response).text == 'yeah')

        # response = Response(confidence=1, match='yesssss', text='yes')
        # self.assertTrue(confirm(response).text == 'yeah')

        response = Response(confidence=1, match='yes', message=Message(text='yeeeees'))
        self.assertTrue(confirm(response).text == 'yeah')

        # response = Response(confidence=1, match='asdf', text='asdf')
        # self.assertTrue(confirm(response).text != confirm.text)

    def test_set_trigger(self):
        # CHECKING THAT COUNTS IS SET PROPERLY (depending on events)
        trigger = Trigger(condition=CountCondition(event=Event(signal=Say), n=2),
                          actions=[Say(text='yo'), Say(text='yo')])

        bot = Bot()
        set_trigger = SetTrigger(trigger=trigger)

        res = bot._areas['Triggers']._process_signal(set_trigger)[0]
        self.assertTrue(res.condition.n == 2)

        bot.do(actions=Say(text='hi'))

        # count
        res = bot._areas['Triggers']._process_signal(set_trigger)[0]
        self.assertTrue(res.condition.n == 3)

    def test_actions_text_multiple_choice(self):
        TEXTS = ['hi', 'hola']

        def check(text):
            return text in [prepare_text(t) for t in TEXTS]

        bot = TestBot()
        bot.do(actions=Say(text=TEXTS))
        self.assertTrue(check(bot.mouth[0].text))

        # renaming
        say = Say(text=[r'you said: "\text" (\0) that matches "\match" and "\foo" and "\1"',
                        r'you said: "\text" (\0) that matches "\match" and "\foo" and "\1"'])
        ask = Ask(text=self.TEXT,
                  options=[re.compile('(?P<foo>hi)[i]+'), 'hola'],
                  actions={'hi': say},
                  store=False)
        matcher = Matcher(options=ask.options)
        message = Message(text='hiiiiiii')
        response = matcher(message)
        action = ask(response)[0]
        self.assertTrue(action.text[0] == 'you said: "hiiiiiii" (hiiiiiii) that matches "hi" and "hi" and "hi"')
        self.assertTrue(action.text[1] == 'you said: "hiiiiiii" (hiiiiiii) that matches "hi" and "hi" and "hi"')

    # ============= #
    # BASIC INTENTS #
    # ============= #
    def test_basic_first_message(self):
        config.SHOW_WELCOME_MESSAGE = True
        bot = TestBot()
        bot.reply(text=self.TEXT)
        self.assertTrue(is_empty(bot.state))
        self.assertTrue(equal_texts(config.MESSAGE_WELCOME, bot.mouth[0]['text']))
        config.SHOW_WELCOME_MESSAGE = False

    def test_basic_intent_stop(self):
        ask_action = Ask(text='hi', actions=Say(text='yo'))

        config.CONFIRM_STOP = False
        bot = TestBot()
        bot.do(actions=ask_action.copy())
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.reply(text='stop')
        self.assertTrue(is_empty(bot.state))

        config.CONFIRM_STOP = True
        bot = TestBot()
        bot.do(actions=[ask_action.copy(), ask_action.copy(), ask_action.copy()])
        self.assertTrue(is_empty(bot.state, but={'Attention', "Actions"}))
        bot.reply(text='stop')
        self.assertTrue(is_empty(bot.state, but={'Attention', 'Actions'}))
        self.assertTrue(equal_texts(config.MESSAGE_CONFIRM_STOP, bot.mouth[1]['text']))

        # NO
        bot.reply(text='no')
        self.assertTrue(is_empty(bot.state, but={'Attention', 'Actions'}))
        bot.reply(text='stop')
        # YES
        bot.reply(text='yes')
        self.assertTrue(is_empty(bot.state))

    def test_basic_intent_restart(self):
        config.CONFIRM_RESTART = False
        bot = TestBot()
        bot.do(actions=Ask(text='hi', actions=Say(text='yo')))
        self.assertTrue(is_empty(bot.state, but={'Attention'}))
        bot.reply(text='restart')
        self.assertTrue(is_empty(bot.state))  # , ignore={}
        config.CONFIRM_RESTART = True

    def test_basic_intent_image_receiver(self):
        bot = TestBot(intents=[ImageReceiver])
        bot.reply(image="http://bla.bla/image")
        self.assertTrue(bot.mouth[0].text == "Nice image!")

    # ===== #
    # AREAS #
    # ===== #

    def test_mouth(self):
        # SAY + delays
        bot = Bot()
        mouth = Mouth(areas=bot._areas)

        self.assertTrue(type(Mouth.text_delay('hi')) == int)
        self.assertTrue(type(Mouth.text_delay('')) == int)
        self.assertTrue(Mouth.text_delay('hi hi hi') > Mouth.text_delay('hi'))

        mouth(Say(text='how are you doing my little friend?', delay_coef=0.5))
        mouth(Say(text='how are you doing my little friend?', ))
        mouth(Say(text='how are you doing my little friend?', delay_coef=1.5))
        self.assertTrue(mouth[0]['delay'] < mouth[1]['delay'] < mouth[2]['delay'])
        self.assertTrue(type(mouth[0]['delay']) == int)

        mouth(Say(text='how are you doing my little friend?', delay=100))
        self.assertTrue(mouth[3]['delay'] == 100)

        mouth(Say(text='how are you doing my little friend?', delay=100, delay_coef=2.1))
        self.assertTrue(mouth[4]['delay'] == 210)

        # POP_DICTS, POP_DICTS
        actions = mouth.pop_all()
        self.assertTrue(actions[0]._name == "Say")
        mouth(Say(text='text'))
        dicts = mouth.pop_dicts()
        self.assertTrue(type(dicts[0]) == dict)

    def test_area_memory_test_score(self):
        """score takes dict or list of dicts"""

        memory = Memory(Bot())

        KEY, VALUE = 'hi.hola', "yo"
        test_dict = {KEY: VALUE}
        test_dict2 = {'a': VALUE}
        test_list = [test_dict, test_dict2]

        store = Store(data=test_dict)
        res_dict = store(_area=memory)
        self.assertTrue(test_dict == res_dict)

        memory(store)
        self.assertTrue(memory[KEY] == VALUE)

        memory = Memory(Bot())
        memory(Store(data=test_list))
        self.assertTrue(memory[KEY] == VALUE)
        self.assertTrue(memory['a'] == VALUE)

    def test_area_events(self):
        """score takes dict or list of dicts"""

        events = Events(Bot())

        # ACTION COUNTS
        say = Say(text='hi')
        events(say)
        self.assertTrue(events['counts.Action.Say.n'] == 1)
        events(say)
        self.assertTrue(events['counts.Action.Say.n'] == 2)

        # intent counts
        intent = Echo(message=Message(text='hi'))
        events(intent)
        self.assertTrue(events['counts.Intent.Echo.n'] == 1)
        # intent done (event)
        event = Event(signal=intent, type='done')
        events(event)
        self.assertTrue(events['counts.Intent.Echo.done'] == 1)

        # history check
        self.assertTrue(len(events['history']) == 4)
        self.assertTrue({'signal_name', 'signal_type', 'time'}.issubset(events['history'][0]))
        self.assertTrue(
            events['history'][0]['signal_name'] == "Say" and events['history'][-1]['signal_name'] == "Event")

        # summary check
        self.assertTrue(events['counts.Intent.done'] == 1)
        self.assertTrue(events['counts.Intent.n'] == 1)
        self.assertTrue(events['counts.Action.n'] == 2)
        # lowest level
        self.assertTrue(events['counts.n'] == 3)
        self.assertTrue(events['counts.done'] == 1)

    def test_area_triggers(self):
        area = Triggers()
        trigger = Trigger(condition=EventCondition(event=Event(signal=Message)),
                          actions=Say(text='hi'),
                          instant=True)
        area(SetTrigger(trigger=Trigger(**trigger)))
        area(SetTrigger(trigger=Trigger(**trigger)))
        area(SetTrigger(trigger=Trigger(**trigger)))
        self.assertTrue(len(area) == 3)

        r = area(Event(signal=Message(text='yo')))
        self.assertTrue(len(r) == 3)
        self.assertTrue(area.is_empty())

        # N: TRIGGER SEVERAL TIMES
        area = Triggers()
        trigger = Trigger(condition=EventCondition(event=Event(signal=Message)),
                          actions=Say(text='hi'),
                          instant=True,
                          n=3)
        area(SetTrigger(trigger=Trigger(**trigger)))
        r = area(Event(signal=Message(text='yo')))
        self.assertTrue(r[0]._is(Trigger))
        self.assertTrue(area[0].n == 2)

        r = area(Event(signal=Say(text='yo')))
        self.assertTrue(not r)

        r = area(Event(signal=Message(text='yo')))
        self.assertTrue(r[0]._is(Trigger))
        self.assertTrue(area[0].n == 1)

        r = area(Event(signal=Message(text='yo')))
        self.assertTrue(r[0]._is(Trigger))
        self.assertTrue(area.is_empty())

    # ====================== #
    # MEMORY AND STACK STATE #
    # ====================== #

    def test_memory_state(self):
        m = MemoryState()

        self.assertTrue(m['a.b'] is None)
        self.assertTrue(m.get('a.b') is None)
        self.assertTrue(m.get('a.b', -1) == -1)
        m['a.b'] = 1
        self.assertTrue(m['a.b'] == 1)

        m['a.b.c'] = 2
        self.assertTrue(m['a._b'] == 1)

        del m['a._b']
        self.assertTrue(m['a.b._b'] is None)

        m['a.b'] = {'c2': 3}
        m['a.b'] = dict(c=dict(d=4))
        del m['a.b.c._c']
        m['a.b'] = dict(c=dict(d2=4))
        self.assertTrue(m['a.b.c.d'] == 4)
        self.assertTrue(m['a.b.c.d2'] == 4)

        # __contains__
        self.assertTrue('a.b.c' in m)
        self.assertTrue('a.b.c.d' in m)
        self.assertTrue('a.b.c.d.e' not in m)

        m.clear()
        self.assertTrue(not m)
        self.assertTrue(m.is_empty())

        # add + __add__
        m = MemoryState()
        m['a.b'] = 1
        m2 = m + {'a.c': 2}
        m.add({'a.c': 2})
        self.assertTrue(m2['a.c'] == 2)
        self.assertTrue(m['a.c'] == 2)

        # pop
        m = MemoryState({'a': {'b': 1, 'c': 2}})
        v = m.pop('a.b')
        self.assertTrue(v == 1)
        self.assertTrue(m['a.b'] is None)
        self.assertTrue(m['a.c'] == 2)
        v = m.pop('a.c')
        self.assertTrue(v == 2)
        self.assertTrue(m['a'] == {})
        # pop main key
        m = MemoryState({'a': {'b': 1, 'c': 2}})
        v = m.pop('a')
        self.assertTrue(not m)

        # CREATE EMPTY LIST
        m = MemoryState()
        m['a.b'] = {}
        self.assertTrue(m == {'a': {'b': {}}})
        # adding thing to empty list (through ref)
        p = m['a.b']
        p['c'] = 5
        self.assertTrue(m == {'a': {'b': {'c': 5}}})

        # DEL doesn't create structure
        m = MemoryState()
        del m['a.b.c']
        self.assertTrue(not m)

        # GET POINTER
        m = MemoryState()
        p = m.pointer('a.b')
        p['c'] = 5
        self.assertTrue(m == {'a': {'b': {'c': 5}}})
        # if there is a value
        m = MemoryState()
        m['a.b'] = 1
        p = m.pointer('a.b')

    def test_stack_state(self):
        s = StackState()

        s.append(1)
        s.append(2)
        s.append(3)
        s.push(0)

        self.assertTrue(s == [0, 1, 2, 3])
        self.assertTrue(s.pop() == 0)
        self.assertTrue(s == [1, 2, 3])
        del s[2]
        self.assertTrue(s == [1, 2])
        self.assertTrue(s.all() == [1, 2])
        self.assertTrue(2 in s)
        self.assertTrue(len(s) == 2)

        # ADD + __add__
        s = StackState()

        s.add(1)
        s.add(2)
        s.add([3])
        s += [4]

        self.assertTrue(s == [1, 2, 3, 4])


self = botiumUnitTest()
