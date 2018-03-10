"""
Contains a base Intent class and some handy intents.

author: Deniss Stepanovs
"""
from .entities import Signal
from .signals import Matcher, NamedEntity
from .actions import Trigger, Ask, Clarify, Confirm, Store, Say, Pause, Clear, Graph, Attend
from . import config


class Intent(Signal):
    """Intent transforms text into actions. Requires score method that transforms text into score"""

    # texts to be used for bot/intent validation (sanity checks)
    _test_texts = []

    _structure = {'message'}

    # when True the intent can be always chosen (like Stop)
    _command = False

    def score(self, message, **kwargs):
        """Depending on message.[text], outputs score, usually [0-1]"""
        raise NotImplementedError("Please Implement this method")


class Stop(Intent):
    """
    Cleans areas: attention, actions
    """
    _command = True

    def score(self, message, **kwargs):
        text = message.text
        return int(text.lower() in {'stop'})

    def __call__(self, _areas=None, **kwargs):
        # cleating areas: actions, attention
        stop_actions = []

        if config.SHOW_STOP_MESSAGE:
            stop_actions.append(Say(text=config.MESSAGE_STOPPED))

        stop_actions.append(Clear(area=['Attention', 'Actions']))

        if config.CONFIRM_STOP:

            return Confirm(text=config.MESSAGE_CONFIRM_STOP,
                           yes=stop_actions,
                           no=_areas['Attention']['focus'])
        else:
            return stop_actions


class Restart(Intent):
    """Cleans all (stateful) areas"""

    _command = True

    def score(self, message, **kwargs):
        return int(message.text.lower() in {'restart'})

    def __call__(self, _areas, **kwargs):
        # cleaning everything
        restart_actions = []

        if config.SHOW_RESARTED_MESSAGE:
            restart_actions.append(Say(text=config.MESSAGE_RESTARTED))

        restart_actions.append(Clear(area=['Attention', 'Actions', 'Memory', 'Triggers', 'Events']))

        if config.CONFIRM_RESTART:
            return Confirm(text=config.MESSAGE_CONFIRM_RESTART,
                           yes=restart_actions,
                           no=_areas['Attention']['focus'])
        else:
            return restart_actions


class Echo(Intent):
    def score(self, message, **kwargs):
        return 0.01

    def __call__(self, *args, **kwargs):
        return Say(text='ECHO: %s' % self.message.text)


class FirstMessage(Intent):
    def score(self, message, **kwargs):
        return 2 * int(config.SHOW_WELCOME_MESSAGE and kwargs.get('is_first_message', False))

    def __call__(self, *args, **kwargs):
        return Say(text=config.MESSAGE_WELCOME)


class ImageReceiver(Intent):
    def score(self, message, **kwargs):
        return bool(message.image)

    def __call__(self, *args, **kwargs):
        return Say(text='nice image!')


class NonText(Intent):
    def score(self, message, **kwargs):
        return bool(not message.text)

    def __call__(self, *args, **kwargs):
        if self.message.image is not None:
            return Say(text="nice image!")

        elif self.message.video is not None:
            return Say(text="nice video!")

        elif self.message.voice is not None:
            return Say(text="nice voice!")

        else:
            return Say(text="i see...")


class Grapher(Intent):
    def score(self, message, **kwargs):
        return message.text in {'start'}

    def __call__(self, *args, **kwargs):
        graph = Graph(state='start',
                      final='no_worries',
                      transitions=dict(start=Ask(text='Do you have problems in your life?',
                                                 options=dict(yes_problem=['yes'],
                                                              no_worries=['no'])),
                                       yes_problem=Ask(text='Can you do something about it?',
                                                       options=dict(no_worries=['no', 'yes'])),
                                       no_worries=Ask(text="Then don't worry",
                                                      options=dict()),
                                       ))

        return graph


class AttendIntent(Intent):
    def score(self, message, **kwargs):
        return message.text.lower().strip('.?\n!') in {'my name is bob and my age is 1',
                                                       'my name is bob',
                                                       'my age is 1',
                                                       'age name'}

    def __call__(self, *args, **kwargs):
        attend = Attend(ask=[Ask(text='What is your name?',
                                 options=NamedEntity(name='name')),
                             Ask(text='What is your age?',
                                 options=NamedEntity(name='age'))],
                        actions=Say(text='got it'),
                        confirm_text=r'your name is \1 and age \2 years, right?',
                        store={'mission_complete': True})

        actions = attend(message=self.message)
        return actions


class Profiler(Intent):
    def process(self, _areas, **kwargs):
        message = self.message
        if message._intent:
            memory = _areas['Memory']
            name = message._intent['name']
            if name.split('_')[0] in {'my', 'your'}:
                qa, key = name.split('_', 1)

                if qa == 'my':
                    # statement
                    data = {'answer': message.text, 'entities': message._entities}
                    for entity in message._entities:
                        if entity['entity'] == key:
                            data['short_answer'] = entity['value']

                    return Store(data={'user.%s' % key: data})
                else:
                    # question
                    data = str(memory['bot.%s' % key])
                    return Say(text=data)

        return 0

    def score(self, message, _areas, **kwargs):
        return bool(self.process(_areas, **kwargs))

    def __call__(self, _areas=None, **kwargs):
        return self.process(_areas)
