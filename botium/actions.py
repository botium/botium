"""
Contains bot's actions.

author: Deniss Stepanovs
"""
from .config import config
from .entities import Signal
from .signals import Trigger, Response, NamedEntity, Matcher, Message, Event
from .conditions import CountCondition, IntervalCondition
from .utils import *


class Action(Signal):
    """Action is just a Signal"""


class Clear(Action):
    """
    Clears stateful areas.

    :param area: name (or list of names) of areas to clear

    Examples
    --------
    >>> Clear(area=['Attention', 'Actions'])
    """

    _structure = {'area'}
    _prototype = dict(area=[str])

    def __call__(self, _areas=None, **kwargs):
        to_clear = [a for a in list_of(self.area)]
        for area_name, area in _areas.items():
            if area_name in to_clear or '*' in to_clear:
                if area.is_stateful:
                    area.clear()


class Say(Action):
    """
    Saying things.

    Say actions end up in the Mouth(Area).

    Parameters
    ----------
    text : text to be uttered by the bot
        type(text) == str
    options : options to be shown as quick_replies (fb) or in other button-like way
        type(options) == list of str,
    """

    _structure = {'may': {'as_is', 'delay', 'delay_coef'},
                  'or': ({'text'}, {'options'})}
    _prototype = dict(text=[str],
                      options=[str],
                      as_is=bool,
                      delay=int,
                      delay_coef=float)

    def to_say(self):
        return self.copy()

    def __call__(self, *args, **kwargs):
        pass


class Ask(Action):
    """Asking things."""

    _structure = {'or': ({'text'}, {'options'}),
                  'may': {'actions', 'store', 'rename'}}
    _prototype = dict(text=str,
                      options={int, float, type, str, re._pattern_type, NamedEntity, dict, bool},
                      actions={dict, Signal},
                      store={bool, dict},
                      rename=dict)

    def to_say(self):
        kwargs = {}
        if self.text:
            kwargs['text'] = self.text

        if self.options and all([type(o) in {str, int, float, bool} for o in list_of(self.options)]):
            kwargs['options'] = [str(o) for o in self.options]

        return Say(**kwargs) if kwargs else None

    def __call__(self, response=None, _area=None, **kwargs):
        if response:
            if response.is_perfect:
                # perfect match
                if type(self.actions) == dict:
                    actions = list_of(self.actions[response.match]) \
                        if self.actions and response.match in self.actions else []
                else:
                    actions = list_of(self.actions)

                # substituting text markup from response
                group_kwargs = {r'\0': response.message.text,
                                r'\text': response.message.text,
                                r'\1': response.match,
                                r'\match': response.match}
                # adding entities
                if response.entities:
                    group_kwargs.update({r'\%s' % k: v for k, v in response.entities.items()})

                # substitute text by group kwargs
                for action in actions:
                    if is_relative_to(action, Action):
                        action._text_sub_kwargs(group_kwargs)

                # storing things if needed
                if config.RESPONSE_STORE and self.store is not False:
                    actions = list_of(self.to_store(response)) + actions

                # adding event of Ask-done
                actions.append(Event(signal=self, type='done'))

                return actions

            elif response.match and config.RESPONSE_CLARIFY and response.confidence and response.confidence >= config.RESPONSE_CLARIFY_CONF:
                # good answer, but needs Clarify-cation
                return Clarify(response=response, ask=self, skip=False)

            else:
                # bad answer

                # direct options to choose from
                direct_options = all([type(o) in {str, int, float} for o in list_of(self.options)])
                if direct_options:
                    if self.get("_n", 0) >= config.RESPONSE_REPEAT_N:
                        text = config.MESSAGE_ASK_REPEAT_DIRECT_OPTIONS
                        if '%s' in text:
                            text = text % ", ".join(self.options)

                        return [Say(text=text), self]
                    else:
                        return [Say(text=config.MESSAGE_ASK_REPEAT_DIRECT), self]

                if self.get("_n", 0) >= config.RESPONSE_REPEAT_N:
                    # is your answer complete (real skipping)
                    return Clarify(text=config.MESSAGE_ASK_REPEAT_FAIL,
                                   response=Response(message=response.message,
                                                     confidence=1,
                                                     match=response.message.text),
                                   ask=self)
                else:
                    return [Say(text=config.MESSAGE_ASK_REPEAT), self]

    def to_store(self, response, text=None):
        ct = current_time()

        rename = self.rename if self.rename is not None else {}

        question = rename.get('question', config.STORE_PARAMETERS['question'])
        answer = rename.get('answer', config.STORE_PARAMETERS['answer'])
        match = rename.get('match', config.STORE_PARAMETERS['match'])
        where = rename.get('where', config.STORE_PARAMETERS['where'])
        key = rename.get('key', time_hash() if config.STORE_HASH_KEY else str(ct))

        store_key = where + '.' + key
        store_value = {question: self.text,
                       answer: text if text is not None else str(response.message.text)}
        if config.STORE_TIME:
            store_value['%s_time' % question] = self._time
            store_value['%s_time' % answer] = ct

        if config.STORE_MATCH and self.options is not None:
            if response.match:
                store_value[match] = response.match

        if type(self.store) == dict:
            store_value.update(self.store)

        return Store(data={store_key: store_value})


class Clarify(Action):
    """
    Clarifying things.

    Clarify action for Ask (or other Actions that use Response).
    In case of "almost" (high similarity) match, it confirms that the match is correct.
    """
    _structure = dict(must={'response', 'ask'},
                      may={'skip', 'text'})
    _prototype = dict(ask=Ask,
                      response=Response,
                      text=str,
                      skip=bool)

    def to_say(self):
        text = self.text if self.text else config.MESSAGE_CLARIFY % self.response.match
        options = list(self.options)
        return Say(text=text, options=options)

    @property
    def options(self):
        if self.skip is None:
            return config.CONFIRM_SKIP_OPTIONS if config.CLARIFY_ALLOW_SKIP else config.CONFIRM_OPTIONS
        else:
            return config.CONFIRM_SKIP_OPTIONS if self.skip else config.CONFIRM_OPTIONS

    def __call__(self, response=None, _area=None, *args, **kwargs):

        if response:
            if response.is_perfect:
                if response.match == 'yes':
                    # changing response text accordingly
                    match = self.response.match if self.response.match is not None else self.response.message.text
                    new_response = Response(confidence=1, match=match, message=Message(text=match))
                    # returning what ask would returned
                    return self.ask(new_response)
                elif config.CLARIFY_ALLOW_SKIP and self.skip is not False and response.match == 'skip':
                    new_response = Response(confidence=1, match="<skipped>", message=self.response.message)
                    # returning what ask would returned
                    return self.ask(new_response)
                else:
                    return [Say(text=config.MESSAGE_CLARIFY_NO), self.ask]
            else:
                return [Say(text=config.MESSAGE_CLARIFY_FAIL), self.ask]


class Confirm(Action):
    """
    Confirming things.

    This is a "syntactic sugar" for Ask.
    """

    _structure = dict(may={'no'},
                      must={'yes'},
                      default=dict(text=config.MESSAGE_CONFIRM))
    _prototype = dict(text=str,
                      yes=[Signal],
                      no=[Signal])

    options = config.CONFIRM_OPTIONS

    def to_say(self):
        return Say(text=self.text, options=list(config.CONFIRM_OPTIONS.keys()))

    def __call__(self, response=None, **kwargs):

        if response:
            if response.match in config.CONFIRM_OPTIONS and response.is_perfect:
                if response.match == 'yes':
                    return self.yes
                else:
                    return self.no
            else:
                kwargs = dict(self)
                kwargs['text'] = config.MESSAGE_CONFIRM_FAIL % '", "'.join(config.CONFIRM_OPTIONS.keys())
                return Confirm(**kwargs)


class Store(Action):
    """
    Storing things.

    Actions for storing - bringing data to the Memory(Area)
    """

    _structure = {'data'}
    _prototype = dict(data={dict, list})

    def __call__(self, _area, **kwargs):
        if _area._is('Memory'):
            return self.data


class SetTrigger(Action):
    """
    Setting triggers.


    """

    _structure = {'trigger'}
    _prototype = dict(trigger=Trigger)

    def __call__(self, _area=None, **kwargs):
        if _area._is('Triggers'):
            # Exception: CountCondition needs adjustment with the current 'n'
            # all conditions needs to be checked
            conditions = list_of(self.trigger.condition)
            for condition in conditions:
                if condition._is(CountCondition):
                    key = "counts.%s.%s.n" % (condition.event.signal._type,
                                              condition.event.signal._name)
                    condition['n'] += kwargs['_areas']['Events'].get(key, 0)

                # IntervalCondition
                elif condition._is(IntervalCondition):
                    if condition.time is None:
                        condition['time'] = current_time()

            condition = conditions if type(self.trigger.condition) == list else conditions[0]
            self.trigger['condition'] = condition

            return self.trigger


class Pause(Action):
    """
    Pauses all current actions.

    Pause requires a condition on which all actions will be brought back.
    It sets a trigger and clears Actions(Area).
    """

    _structure = dict(must={'condition'},
                      may={'instant'})
    _prototype = dict(condition={'@Condition'},
                      instant=bool)

    def __call__(self, _areas=None, **kwargs):
        _actions = _areas.get('Actions')
        if _actions:
            # getting all actions to pause
            actions = _actions.all()
            if actions:
                # creating a trigger to get actions back
                trigger = SetTrigger(trigger=Trigger(**self, actions=actions))
                # cleaning action queue
                _actions.clear()
                return trigger


class Graph(Action):
    """
    Complex action for putting the bot in state-machine regime

    Graph needs definition of states and transitions between them.
    Plus, it requires current/final states.
    """
    _structure = dict(must={'transitions', 'state'},
                      may={'final'})
    _prototype = dict(transitions={str: '@Ask'},
                      state=str)

    @property
    def options(self):
        return self.transitions[self.state].options

    def to_say(self):
        kwargs = dict(text=self.transitions[self.state].text)
        options = [x for y in [v for v in self.options.values()] for x in y]
        if options:
            kwargs['options'] = options
        return Say(**kwargs)

    def __call__(self, response=None, **kwargs):

        if response is not None:
            if response.is_perfect:
                # adding move to the path
                self['_path'] = self.get('_path', []) + [self['state']]

                current_ask = self.transitions[self['state']]
                # actions of the current ask
                actions = [a for a in list_of(current_ask(response)) if a._name not in {'Store', 'Event'}]

                self['state'] = response.match

                # Say() from new state
                # actions.append(self.transitions[self['state']].to_say())

                if self.final == self['state']:
                    # in the end appending only Say
                    actions.append(self.transitions[self['state']].to_say())
                else:
                    # keeping the graph
                    actions.append(self)

                return actions
            else:
                return [Say(text=config.MESSAGE_GRAPH_WRONG_TRANSITION), self]


class Attend(Action):
    """
    Complex action for handling multiple Ask objects.

    This action is similar to Ask. Attend is looking for answers to multiple Asks.
    When all Asks done, it stores the results and executes actions.
    """

    _structure = dict(must={'ask', 'actions'},
                      may={'confirm_text'},
                      default={'store': True})
    _prototype = dict(ask=[Ask],
                      actions=[Signal],
                      confirm_text=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self['ask'] = list_of(self.ask)
        self['_focus'] = None
        self['_responses'] = [None] * len(self.ask)

    @property
    def options(self):
        # current ask matcher
        # return self.ask[self._current].options
        return None

    def to_say(self):
        return self.ask[self._focus['i']].to_say()

    def to_store(self):
        questions = []
        for a, r in zip(self.ask, self._responses):
            store = a.to_store(r)
            store_key = list(store.data.keys())[0]
            d = {k: v for k, v in store.data[store_key].items() if '_time' not in k}
            questions.append(d)

        store_data = dict(attend=questions,
                          attend_time=current_time())
        if type(self.store) == dict:
            store_data.update(self.store)

        return Store(data={store_key: store_data})

    def get_actions(self):
        group_kwargs = {r'\%d' % (i + 1): r.match for i, r in enumerate(self._responses)}

        actions = []
        for action in list_of(self.actions):
            if is_relative_to(action, Action):
                action._text_sub_kwargs(group_kwargs)
            actions.append(action)

        if self.store:
            actions = [self.to_store()] + actions

        if self.confirm_text:
            text = text_sub_kwargs(self.confirm_text, group_kwargs)
            return Confirm(text=text, yes=actions)

        return actions

    def __call__(self, response=None, message=None, *args, **kwargs):
        if message is not None and response is None:
            # first run
            response = Matcher(options=self.options)(message)

        if response is not None:
            for i, ask in enumerate(self.ask):
                r = Matcher(options=ask.options)(response.message)
                if r.is_perfect:
                    self['_responses'][i] = r

            if self['_focus'] and not all(self['_responses']):
                # was already asked
                self['_responses'][self['_focus']['i']] = response

            if all(self['_responses']):
                # all responses done
                return self.get_actions()
            else:
                # first not answered ask
                next_id = next(i for i, r in enumerate(self._responses) if r is None)
                self['_focus'] = dict(i=next_id, n=1)
                return self
