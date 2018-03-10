"""
Contains conditions that are used for setting triggers.

author: Deniss Stepanovs
"""

from .entities import Signal
from .signals import Message, Matcher
from .utils import current_time

import re


class Condition(Signal):
    """Prototype for creating Conditions

    Simply inherit from it and define __call__ function to return True/False depending on whether or not condition is met."""

    _structure = dict(must={'event'})
    _prototype = dict(event='@Event')

    def reset(self):
        pass

    def __call__(self, *args, **kwargs):
        """Must return bool: True if condition is met, False otherwise."""
        assert False


class TextCondition(Condition):
    """Condition on signal's text"""

    _structure = dict(must={'event', 'options'})
    _prototype = dict(event='@Event',
                      options={int, float, type, str, re._pattern_type, dict, bool})

    def __call__(self, event, _areas=None, **kwargs):
        if event.signal._is_relative_to(self.event.signal) and event.signal.text:
            message = Message(text=event.signal.text)
            response = Matcher(options=self.options)(message)
            return response.is_perfect
        else:
            return False


class EventCondition(Condition):
    """Condition on occurrence of an event"""

    _structure = dict(must={'event'}, may={'type'})
    _prototype = dict(event='@Event')

    def __call__(self, event, *args, **kwargs):
        if type(self.event.signal) == type:
            # relative event + type of event ('n', 'done') matches (if defined)
            return event.signal._is_relative_to(self.event.signal) and self.event.type == event.type
        else:
            # complete match of the events
            return self.event == event


class CountCondition(Condition):
    """Condition on counts of events"""

    # type is for 'n' or 'done'
    _structure = dict(must={'event', 'n'},
                      may={'type'})
    _prototype = dict(event='@Event', n=int)

    def __call__(self, event, _areas=None, **kwargs):
        event_type = self.event.type if self.event.type else 'n'
        key = "counts.%s.%s.%s" % (self.event.signal._type, self.event.signal._name, event_type)
        return self.n <= _areas['Events'].get(key, 0)


class TimeCondition(Condition):
    """
    Condition on certain time

    NB! bot should be "checked" from time to time to check for triggers
    """
    _structure = dict(must={'time'})
    _prototype = dict(time=int)

    def __call__(self, event, _areas=None, **kwargs):
        return current_time() >= self.time


class IntervalCondition(Condition):
    """
    Condition on certain time

    NB! bot should be "checked" from time to time to check for triggers
    """
    _structure = dict(must={'interval'},
                      may={'time'})
    _prototype = dict(interval=int,
                      time=int)

    def reset(self):
        """updating condition, needed for repeating the condition (n>1)"""
        self['time'] = current_time()

    def __call__(self, event, _areas=None, **kwargs):
        check = current_time() >= self.time + self.interval
        if check:
            self.time += self.interval
        return check
