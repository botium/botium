"""
Contains bot's signals.

author: Deniss Stepanovs
"""
from .entities import Signal
from .utils import *
import logging

from types import MethodType, FunctionType


class Check(Signal):
    """Empty signal to get the bot awake for a moment"""

    # redefining the type so no triggers on "Signal" are
    _type = 'Entity'

    def __getattr__(self, item):
        return None

    def __call__(self, *args, **kwargs):
        pass


class NamedEntity(Signal):
    """Signal to match named entities (with Matcher)"""

    _structure = {'name'}
    _prototype = dict(name=str)

    def __call__(self, message, **kwargs):
        if message._entities is not None:
            for entity in message._entities:
                if self.name.lower() == entity['entity'].lower():
                    return Response(message=message, confidence=1, match=entity['value'])
        else:
            logging.warning("NamedEntities require NLP engine, but you haven't specified one. You need to provide "
                            "nlp=Nlp() where Nlp is a class of your NLP engine")

        return Response(message=message, confidence=1, match=None)


class Message(Signal):
    """Carries user's message (text/image/etc.)"""

    _structure = dict(may={'text', 'image', 'voice', 'video'},
                      default=dict(text=''))
    _prototype = dict(text=str,
                      image=str,
                      voice=str,
                      video=str)

    _intents = []
    _entities = []

    def attach_nlp(self, nlp):
        if nlp:
            _nlp = nlp(self.text)
            self._entities = _nlp['entities']
            self._intents = _nlp['intents']


class Desire(Signal):
    """Simple carrier for actions, used by Do(Area)"""

    _structure = {'actions'}
    _prototype = dict(actions=[Signal])

    def __call__(self, **kwargs):
        return self.actions


class Event(Signal):
    """Simple signal: carries another signal and type (of what happened). Used for triggering things."""

    _structure = dict(must={'signal'}, may={'type'})
    _prototype = dict(signal=[Signal], type=str)

    def __call__(self, *args, **kwargs):
        return None


class Trigger(Signal):
    """Releases actions when it is triggered=True (the condition is met)"""

    _structure = dict(must={'condition', 'actions'},
                      default=dict(triggered=False,
                                   instant=False,
                                   n=1))
    _prototype = dict(condition={'@Condition'},
                      actions=[Signal],
                      instant=bool,
                      triggered=bool,
                      n=int)

    def __call__(self, event=None, **kwargs):
        if kwargs['_area']._is('Actions'):
            # if at Actions-area, release actions
            if self.triggered:
                return self.actions

        if event is not None:
            triggered = self.trigger(event, **kwargs)
            return triggered

    def trigger(self, event, **kwargs):
        for condition in list_of(self.condition):
            triggered = condition(event, **kwargs)
            if triggered:
                self['triggered'] = True
                self['n'] -= 1
                return True


class Matcher(Signal):
    """Matches Message with options (from Ask-type actions)"""

    _structure = dict(must={'options'})
    _prototype = dict(
        options={int, float, type, str, re._pattern_type, NamedEntity, dict, bool, MethodType, FunctionType})

    def _score(self, option, message, **kwargs):
        """scores a message vs. single option"""
        text = message.text
        if type(option) == type and option in {int, float}:
            try:
                option(text)
                return {'match': text, 'confidence': 1}
            except:
                return {'match': None, 'confidence': 1}

        if type(option) == type and option == bool:
            if text.lower() in {'true', 'false'}:
                return {'match': text.lower(), 'confidence': 1}
            else:
                return {'match': None, 'confidence': 1}

        elif option is None or option is str:
            # rare case: anything is fine
            return {'match': text, 'confidence': 1}

        # regex
        elif type(option) == re._pattern_type:
            m = option.search(text)
            if m:
                # if more than one entity is present -> match=Text
                d = {'match': m.group(1), 'confidence': 1}
                # adding named things
                if m.groupdict():
                    d['entities'] = m.groupdict()
                return d
            else:
                return {'match': None, 'confidence': 1}

        elif callable(option):
            res = option(message, **kwargs)
            # response from NamedEntity
            if type(res) == Response:
                # add other things
                return {'match': res.match, 'confidence': res.confidence}

            # bool from scoring function
            if type(res) == bool:
                res = int(res)

            return {'match': text, 'confidence': res}

        elif type(option) in {int, float, bool}:
            return {'match': option, 'confidence': type(option)(str(option) == text)}

        elif type(option) == str:
            # minimum similarity for strings
            similarity = levenshtein_similarity(option, text)
            if similarity > 0:
                return {'match': option, 'confidence': levenshtein_similarity(option, text)}
            else:
                return {'match': None, 'confidence': 1}
                # return {'match': option, 'confidence': max(0.001, levenshtein_similarity(option, text))}

        else:
            logging.error("unknown type (%s) in Matcher" % option)
            return dict(match=None, confidence=0)

    def scores(self, message, **kwargs):
        if type(self.options) == dict:
            scores = []
            for match, options in self.options.items():
                _scores = [self._score(option, message, **kwargs) for option in options]
                for s in _scores:
                    if s['match'] is not None:
                        s['match'] = match
                    # adding named things
                    s['entities'] = {match: message.text}
                scores.extend(_scores)
            return scores
        else:
            return [self._score(option, message, **kwargs) for option in list_of(self.options, keep_none=True)]

    def __call__(self, message, **kwargs):
        scores = [d for d in self.scores(message, **kwargs) if d['match'] is not None]

        if scores:
            best_match = max(scores, key=lambda x: x['confidence'])
        else:
            best_match = dict(match=None, confidence=1)

        best_match['message'] = message
        return Response(**best_match)


class Response(Signal):
    """Result of matcher"""
    _structure = dict(must={'confidence', 'match', 'message'},
                      may={'entities'})
    _prototype = dict(confidence={float, int},
                      match={str, None},
                      text=str,
                      entities={str: str})

    @property
    def is_perfect(self):
        """defines the perfect answer"""
        return self.match is not None and self.confidence > 0.95


class Monitor(Signal):
    _structure = {}

    def __init__(self, _areas):
        super().__init__()

        # first message
        if 'Events' in _areas:
            self['is_first_message'] = _areas['Events']['counts.n'] == 1

            # last message time
            messages = [d for d in _areas['Events']['history'] if d['signal_name'] == "Message"]
            self['last_message_time'] = messages[-1]['time'] if messages else 0

    def __call__(self, *args, **kwargs):
        return self._state
