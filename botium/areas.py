"""
Contains bot's areas.

author: Deniss Stepanovs
"""
from .entities import Area, MemoryState, StackState
from .signals import *
from .actions import *
from .intents import Intent
from .utils import *
from . import config
import logging


class Do(Area):
    """
    Bot's interface for emitting actions.

    This is a way to directly tell to the bot what actions to execute.
    Being an interface, it is attached to the bot.

    Examples
    --------
    >>> bot = Bot()
    >>> bot.do(actions=[Say(text='hi'), Ask(text='How are you?')])
    """

    is_interface = True

    def __call__(self, **kwargs):
        if 'actions' in kwargs:
            return Desire(actions=kwargs['actions'])
        else:
            logging.warning('do: no actions provided')


class Mouth(Area, StackState):
    """
    Mouth prepares the message to be uttered.

    Mouth capitalizes messages, calculates delays etc... small things.
    Mouth listens to all objects that can be turned to Say.
    When Action arrives, it is transformed into Say object and pushed to the container.
    Keys of Say-objects are limited to {text, options, delay}
    """
    listen_to = [Ask, Say, Clarify, Confirm, Graph, Attend]

    _output_keys = {'text', 'options', 'delay'}

    @staticmethod
    def text_delay(text):
        # in miliseconds

        WPS = config.WPM / 60
        n = len(text.split())
        return int(1000 * (0.3 + n / WPS))

    def append_and_log(self, action):
        if "Events" in self._areas:
            self._areas['Events'].log_signal(action)
        self.append(action)

    def pop_dicts(self):
        dicts = [dict(a) for a in self]
        self.clear()
        return dicts

    def __call__(self, action):
        if config.MODE == 'test':
            print("MOUTH:")
            print(action)

        # say it is the final product of mouth
        say = action.to_say()

        #if say.text is not None:
        if say.text:
            say['text'] = choose_text(say)

        # updating the text (making it nicer)
        if say.text and not say.get('as_is', False):
            say['text'] = prepare_text(say['text'])

        if 'options' in say:
            say['options'] = list_of(say['options'])

        # adding delays to messages:
        if config.PROVIDE_DELAYS and say.text:
            delay_coef = say.get('delay_coef', 1)
            say['delay'] = int(delay_coef * say.get('delay', self.text_delay(say['text'])))

        # preparing for the output: filtering
        say_keys = {k: v for k, v in say.items() if k in self._output_keys}
        say = Say(**say_keys)

        self.append_and_log(say)


class Memory(Area, MemoryState):
    """
    Memorizing things.

    This is dict-like Area for permanent keeping things.
    Store action is used to push things directly into the Memory.
    Other actions (like Ask and Attend) can be also transformed into Store action.
    """

    listen_to = [Store]

    def __call__(self, signal):
        objs = self._process_signal(signal)
        if objs:
            for obj in list_of(objs):
                if type(obj) == dict:
                    self.add(obj)
                else:
                    logging.error('memory area: wrong type of signal output (should be dict or list of dicts)')


class Attention(Area, MemoryState):
    """
    Attends and understands user input.

    This is a key Area where text is transform into Intent.
    It also keeps in focus things that require user's Response.
    """
    listen_to = [Ask, Clarify, Confirm, Graph, Attend, Message]

    priority = 6

    def __call__(self, signal, **kwargs):
        # received a message (directly from the sensors)
        if signal._is(Message):
            # adding nlp stuff (not for serializing)
            signal.attach_nlp(self._nlp)

            # areas monitor
            monitor = Monitor(self._areas)

            # creating all things to attend to
            SOURCE_ATTENTION, SOURCE_INTENTS, SOURCE_COMMANDS = 'attention', 'intents', 'commands'
            attention = []

            # 1. intents
            for cIntent in self._intents.values():
                intent = cIntent(message=signal)
                attention.append(dict(intent=intent,
                                      options=intent.score,
                                      source=SOURCE_INTENTS if not intent._command else SOURCE_COMMANDS))
            # 2. responses from Focus
            if self['focus']:
                attention.append(dict(options=self['focus'].options,
                                      source=SOURCE_ATTENTION))

            if not attention:
                logging.warning('no intent recognized')
                return None

            # getting weights
            for a in attention:
                if self['focus']:
                    a['weight'] = 1 if a['source'] in {SOURCE_ATTENTION, SOURCE_COMMANDS} else 0
                else:
                    a['weight'] = 1 if a['source'] in {SOURCE_INTENTS, SOURCE_COMMANDS} else 0

            # intent classification
            self.classify(attention, message=signal, **monitor)

            # adding confidences from NLP part
            if signal._intents is not None:
                intent_confidence = {hash_text(d['intent']): d['confidence'] for d in signal._intents}
                for att in attention:
                    if att['source'] in {SOURCE_INTENTS, SOURCE_COMMANDS}:
                        att['response']['confidence'] += intent_confidence.get(hash_text(att['intent']._name), 0)

            # some base confidence to attention
            for att in attention:
                if att['source'] in {SOURCE_ATTENTION}:
                    att['response']['confidence'] = min(1., att['response'].confidence + 0.1)

            # selecting intents: confidence > 0 and > 0.7 of maximum confidence
            # max_score = max(attention, key=lambda x: x['weight'] * (x['response'].confidence))['response'].confidence
            # atts = [a for a in attention if 0 < a['response'].confidence > 0.7 * max_score]
            atts = [max(attention, key=lambda x: x['weight'] * (x['response'].confidence))]

            signals = []
            for att in atts:
                if att['source'] in {SOURCE_ATTENTION}:
                    focus = self.pop('focus')
                    actions = self._process_signal(focus, response=att['response'])
                    self._areas['Actions'].push(actions)
                else:
                    signals.append(att['intent'])

            return signals

        else:
            if signal._is_relative_to(Action):
                signal['_time'] = current_time()
                signal['_n'] = signal.get('_n', 0) + 1
                self['focus'] = signal

    def classify(self, attention, message, **kwargs):
        """just gets a match to everything in attention"""
        for att in attention:
            att['response'] = Matcher(options=att['options'])(message, _areas=self._areas, **kwargs)


class Actions(Area, StackState):
    """
    Area for acting things out.

    The main purpose is to keep a queue of the bot's actions.
    In this area actions are obtained from the action-carriers and processed.
    NB! Actions can be complex (encapsulated), so area emits initial signal with encapsulated if any!
    """

    # signals that design to carry actions
    listen_to = [Intent, Desire, Trigger]

    def __call__(self, signal=None):

        if signal:
            # processing the signal
            actions = self._process_signal(signal)

            if actions:
                # loading actions
                if signal._is_relative_to(Intent):
                    # + event for intent completion
                    actions = list_of(actions) + [Event(signal=signal, type='done')]

                self.push(actions)

        # if queue not empty doing actions
        if not self.is_empty():
            # poping the action
            action = self.pop()
            # emmiting the initial signal too
            return [action] + self._process_signal(action)


class Triggers(Area, StackState):
    """
    Keeps and checks triggers.

    It looks for Events, checks the trigger and if trigger conditions are met, releases the trigger.
    """
    listen_to = [Event, SetTrigger]

    priority = 8

    def __call__(self, signal):

        if signal._is(Event):
            # updating/triggering all triggers
            for trigger in self:
                self._process_signal(trigger, event=signal)
            # if it is ready and should be run "before" (usually not)
            return self.pop_triggered(instant=True)

        elif signal._is(SetTrigger):
            # just adding the triggers
            triggers = self._process_signal(signal)
            if triggers:
                self.append(triggers)

    def check(self):
        for trigger in self:
            self._process_signal(trigger, event=Event(signal=Check()))

    def pop_triggered(self, instant=False):
        triggered = []
        keep = []
        for trigger in self:
            if trigger.triggered and trigger.instant == instant:
                triggered.append(trigger)
                if trigger.n > 0:
                    keep_trigger = trigger.copy()
                    keep_trigger['triggered'] = False
                    # mainly because of IntervalCondition
                    keep_trigger['condition'].reset()
                    keep.append(keep_trigger)
            else:
                keep.append(trigger)
        self._initizalize(keep)
        return triggered


class Events(Area, MemoryState):
    """
    Emits events, keeps event data.

    The area listens to all that happens with the bot.
    It keeps statistics, history and log.
    Plus, it emits events.
    """
    listen_to = [Signal]

    # should run first
    priority = 10

    def log_signal(self, signal):
        record = dict(signal=signal,
                      signal_name=signal._name,
                      signal_type=signal._type,
                      time=current_time())
        self['log'] = (self.get('log', []) + [record])[-config.LOG_LIMIT:]

    @property
    def log(self):
        return self.get('log', [])

    def __call__(self, signal):
        # history is permanent !
        signal = signal.copy()

        if signal._is(Event):
            # event was received (like "intent done") from other areas
            event = signal
            # nothing to send around
            event_out = None
            event_type = event.type if event.type else 'unk'
            key = "counts.%s.%s.%s" % (event.signal._type, event.signal._name, event_type)
        else:
            # creating the event of the sending around the event of the signal
            event_out = Event(signal=signal)
            # simple count
            event_type = 'n'
            key = "counts.%s.%s.%s" % (signal._type, signal._name, event_type)

        # saving precise counts
        self[key] = self.get(key, 0) + 1

        # saving summaries
        subs = key.split('.')
        # lower level
        summary_key = '.'.join(subs[:2] + subs[3:])
        self[summary_key] = self.get(summary_key, 0) + 1
        # base level
        summary_key = '.'.join(subs[:1] + subs[3:])
        self[summary_key] = self.get(summary_key, 0) + 1

        # pushing event to history
        record = dict(signal_name=signal._name,
                      signal_type=signal._type,
                      time=current_time())
        self['history'] = (self.get('history', []) + [record])[-config.HISTORY_LIMIT:]

        return event_out
