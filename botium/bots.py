"""
Contains main Bot class plus a few more.

author: Deniss Stepanovs
"""
from .config import config
from .entities import Entity
from .areas import Do, Events, Attention, Memory, Actions, Triggers, Mouth
from .signals import Message
from .intents import Echo, FirstMessage, Stop, Restart
from .utils import list_of, from_camel

import logging
from collections import OrderedDict
from itertools import groupby


class Bot:
    _config = None

    intents = []
    _intents_ = []

    areas = []
    _areas_ = [
        # interface for executing actions
        Do,
        # classifies and prioritize intents
        Attention,
        # memorizes things
        Memory,
        # keeps track of the events
        Events,
        # keeps track of triggers
        Triggers,
        # keeps track of the actions
        Actions,
        # Area accumulating what bot says
        Mouth,
    ]

    def __init__(self, state=None, intents=None, nlp=None, **kwargs):
        # bot mode
        self.nlp = nlp

        if kwargs:
            config.update(kwargs)

        if self._config is not None:
            config.update(self._config)

        # for Intents area
        self._intents = {intent._name: intent for intent in self._intents_ + self.intents + list_of(intents)}

        # restoring bot's state
        state = Entity._restore(state) if state is not None else {}

        # allocating brain areas in "priority order"
        self._areas = OrderedDict()
        for cArea in sorted(self._areas_ + self.areas, key=lambda x: x.priority, reverse=True):

            area_name = cArea._name

            # creating area
            area = cArea(state=state.get(area_name), areas=self._areas)
            # attaching intents and nlp to Attention
            if cArea in {Attention}:
                area._intents = self._intents
                area._nlp = self.nlp

            self._areas[area_name] = area

            # attaching interfaces: interface to the bot's face
            if area.is_interface:
                setattr(self, from_camel(area_name), self._get_sensor_interface(area_name))

            # stateful areas can be accessed directly
            if self._areas[area_name].is_stateful:
                setattr(self, from_camel(area_name), self._areas[area_name])

    def reply(self, **kwargs):

        if kwargs:
            message = Message(**kwargs)
            if Events._name in self._areas:
                # logging the message
                self._areas[Events._name].log_signal(message)

            self.process(None, message)

        else:
            logging.warning("reply: nothing is provided to create a Message from")

    def _get_sensor_interface(self, name):
        return lambda **kwargs: self.process(self._areas[name], self._areas[name](**kwargs))

    def _process(self, source_area, signals_in):
        """Recursive part of the progress"""
        for area in self._areas.values():
            # sensors and source areas (those who made a signal) don't receive a signal
            if (area != source_area or area.listen_to_self) and not area.is_interface:
                for signal_in in list_of(signals_in):
                    if signal_in is not None:
                        if any([signal_in._is_relative_to(a) for a in area.listen_to]):
                            signal_out = area(signal_in)
                            if signal_out:
                                self._process(area, signal_out)

    def process(self, source_area, signal_in):
        """
        Progresses (propagates) the signal from source_area
        :param source_area: area that generated the signal
        :param signal_in:  the signal that was generated
        """
        # progressing the signal (entering recursion)
        self._process(source_area, signal_in)

        # Some things still needed to be checked: Triggers and pending actions

        # Triggering "after" type of triggers
        self._check_triggers()

        # Checking for pending action if Attention is empty
        if Actions._name in self._areas:
            # checking if current action is not expection
            is_exception = bool(
                not self._areas[Actions._name].is_empty() and self._areas[Actions._name].get()._is('@Clear'))

            # if there is Action area at all
            if is_exception or Attention._name not in self._areas or not self._areas[Attention._name]['focus']:
                source_area = self._areas[Actions._name]
                # getting pending task from Actions
                signal_in = source_area()
                if signal_in:
                    # progressing further
                    self.process(source_area, signal_in)

    def _check_triggers(self):
        """
        Checks and processes bot's triggers

        It is mainly needed to check the conditions that involve time as bot cannot get himself awaken.
        """
        if Triggers._name in self._areas:
            # if bot has triggers at all
            trigger_area = self._areas[Triggers._name]
            # getting already triggered stuff (that needed to be run "after" - standard mode)
            triggers = trigger_area.pop_triggered(instant=False)
            if triggers:
                self.process(trigger_area, triggers)

    def check(self):
        if Triggers._name in self._areas:
            self._areas[Triggers._name].check()
            self._check_triggers()

    def log(self, grouped=False):
        # self = bot
        log = [dict(time=l['time'],
                    agent='bot' if l['signal_name'] == 'Say' else 'user',
                    **l['signal']) for l in self._areas['Events'].log]
        if grouped:
            log_grouped = []
            for k, g in groupby(log, lambda x: x['agent']):
                log_grouped.append(list(g))
            return log_grouped

        return log

    @property
    def state(self):
        """Complete state of the bot"""
        state = {}
        for area_name, area in self._areas.items():
            if area.is_stateful:
                state.update(area._json)
        return state

    def validate(self):

        # BOT SOMEHOW REACTS TO THE TEST MESSAGES
        # text to test bot's reaction

        # creating test bot for validation (so current bot's states are not altered)
        bot = self.__class__(self.state)

        stateful_areas = [area for area in bot._areas.values() if area._name not in {'Events'} and area.is_stateful]
        # areas in which the effect of a messages could have been notices (except motors)

        test_texts = ['hi']
        for cIntent in bot._intents.values():
            test_texts += cIntent._test_texts
            # calling intents directly with texts, checking for failure
            for text in ['hi'] + cIntent._test_texts:
                intent = cIntent(message=Message(text=text))
                try:
                    _ = bot._areas[Actions._name]._process_signal(intent)
                except:
                    logging.error('intent <%s> failed at text "%s"' % (intent._name, text))

        for text in test_texts:
            # sending text to the bot's ear
            bot.reply(text=text)
            # checking all motors
            if not any([bool(stateful_area) for stateful_area in stateful_areas]):
                logging.error('no output for text: "%s"' % text)
            # cleaning all motors
            for motor in stateful_areas:
                motor.clear()


class TestBot(Bot):
    intents = [Echo, Restart, FirstMessage, Stop]


class EchoBot(Bot):
    intents = [Echo]
