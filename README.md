# Botium
[![Build Status](https://travis-ci.org/botium/botium.svg?branch=master)](https://travis-ci.org/botium/botium)
[![Coverage Status](https://coveralls.io/repos/github/botium/botium/badge.svg?branch=master)](https://coveralls.io/github/botium/botium?branch=master)

This is a python Bot Framework that makes bot development easy, straightforward and enjoyable.

It was originally developed to bring into life [SentinoBot](https://www.facebook.com/sentinobot/) that "Knows you better than your mum":)

Botium will help you to build bots of any complexity.


## Key Features

Your bot will be able:
* Saying, Asking, Memorizing things
* Trigger-ing things based on user text, intent, time, bot's statistics
* Creating new actions that as easy to use as built in
* Easy making different scenarios (e.g. tutorial)
* Integrating with modern NLP tools, but keeping full control over them

Main features of the "Botium" framework:
* full control of the bot's flow
* linear, parallel and graph-like bot flows
* seamless integration with NLP tools ([Spacy](https://spacy.io/), [Rasa](https://github.com/RasaHQ/rasa_nlu) etc.)
* many predefined bot's actions
* fully json serialization
* tests covered

Developer friendly features:
* written in pure python
* a bunch of [examples](./examples)
* simple UI and CLI included
* easy integration with messaging platforms
* straghtforward access to all bot's parameters (state)


## Installation

Botium should work on `Python 3.5+` and can be simply installed by

    pip install botium

... or clone the repository from GitHub and run:

    git clone https://github.com/botium/botium.git
    cd botium
    python setup.py install
    
## Quickstart

Starging a new bot is easy.
You need to define `Intent`-s and tell the `Bot` to use them. 
Intent is something that transforms user's text into actions.

We are creating a `PoliteBot` that will greet and ask about your life.

First, let's define an `Greetings` intent 

```python
from botium import Intent  # all intents should inherit from it
from botium import Say, Ask, Store  # predefined actions

class Greetings(Intent):
    # must be defined and return something like "score" depending on user message
    # should be of type int/float/bool 
    def score(self, message, **kwargs):
        # message.text contains user input
        return message.text.lower().strip(' ') in {'hi', 'hello'}

    # must be defined and return actions when it is called: call() -> actions
    def __call__(self, *args, **kwargs):
        return [
            # first greeting
            Say(text='hi'),
            # then asking
            Ask(text='how is life?',
                # expected options
                options=['bad', 'good'],
                # defined actions (on options)
                actions=dict(good=Say(text='great!'),
                             bad=Say(text='get better!')),
                # let's save something together with question
                store_extra={'no': 1}),
            # let's save something anywhere we want
            Store(data={'mood': 'polite boy'})]
```

Now we need to plug in the intent to the bot.

```python
from botium import Bot

# defining the bot
class PoliteBot(Bot):
    intents = [Greetings]
```

Bot is ready to go!

```python
# creating the bot
bot = PoliteBot()

# user's text
bot.reply(text='Hi')
bot.mouth
>>> [Say(delay=500, text="Hi."),
>>>  Say(options=['bad', 'good'], delay=899, text="How is life?")]
# As expected, bot greets first and then asks

# user answers 'good'
bot.reply(text='good')
# let's check the last object in the bot's mouth
bot.mouth[-1]
>>> Say(delay=500, text="Great!")
```

It is pretty straightforward to understand what just happened.
However, much more happened under the scene.
Next sections will shed some light on it.
If you patience is not your strong side, explore the following
```python
bot.log()   # keeps user-bot textual transactions
bot.memory  # keeps questions-answers pairs or anything as result of the Store action
bot.events  # keeps statistics and history
```

## Bot in action

There are two main pieces of a `Bot`: `Area`-s and `Signal`-s. 
Areas are building blocks of the bot and signals is the way areas communicate with each other.
The main formula is _"Areas receive, process and emit signals"_.

The story begins with the user's input - signal `Message` is created.
Several areas are tuned to received the message. 
First, `Events` area updates its statistics (as for all other signals).
Second, `Attention` area chooses what `Intent` fits best to the message.

When `Intent` is recognized, it travels to `Actions` area where intent is transformed into `Action`-s.
Actions can end up in different areas, one of which is the output of the bot `Mouth`. 
If an action requires user's input, it ends up in `Attention`.
During aforementioned scenario, many events are being created and emitted. 
These events can trigger some bot's `Trigger`-s if any is set.
`Trigger`-s are actions set on some specific (built-in or user-defined) condition.
This takes place in area called `Triggers`.

In the end of any transaction, all necessary information is stored in the bot's state that is a topic of the next section.

### Bot's state

Bot's state is a json object that contains everything about the bot. 
Literally everything, so the bot can be easily cloned/restored 
(simple clonine:`CloneBot(state=bot.state)`).

Let's examine bot's state contains.

```python
bot.state.keys()
>>> dict_keys(['Events', 'Memory', 'Actions', 'Attention', 'Triggers', 'Mouth'])
```
Here is a brief summary of what these beasts are about.

**Events**. Keeps statistics of all events that took place. 
It also keeps [limited] history of the events and log - textual messages of both user and bot.

**Memory**. Keeps information of all question asked by the bot and user's answers. 
Memory can be directly updated using bot's `Store` action.

**Attention**. Keeps information of what the bot is currently attending to. 
For example, when bot asked a question or tries to clarify something.

**Actions**. Keeps a queue of actions that should be performed after user's input 
(more precisely, when bot's Attention is empty).

**Triggers**. Keeps active triggers. 
Trigger is a way to set predefined bot's reaction conditioned on user's input.

**Mouth**. Keeps the output of the bot, everything in Say-objects. 
This is a place which should be looked at for bot's response.

It is important to understand that bot's state contains states from all bot's Areas.

On the other hand, `Area`-s can be easily created, in the same fashion as Intents.
```python
from botium import Area, Bot
from botium.entities import MemoryState # to make an area "stateful"

class CoolArea(Area, MemoryState):
    """see corresponding example for more details on how to specify an area"""

class CoolBot(Bot):
    areas = [CoolArea]

bot = CoolBot()
```  

### Bot's interface

Bot's state is a json object. 
The main purpose of it is to store/restore a bot.
However, during development, one can directly access all areas.


We have already seen `reply` and `mouth`, but all areas can be accessed the same way.
Note, that area names are transformed from "camel style" (e.g. CoolArea -> .cool_area)

```python
bot.memory
bot.events
```

Getting log is painless too.

```python
# standard log
bot.log()
# log with grouped user/bot utterances
bot.log(grouped=True)  
```

Areas can be of different types, one of which is has self-explanatory flag `is_interface`. 
When`is_interface=True`, the area is attached to the bot and serves as starting point for the signals.

One important interface is `Do`. Let's see it in action.

```python
from botium import Bot

bot = Bot()
bot.do(actions=[Say(text='hi'), 
                Ask(text='how are you?')])
# the result is quite similar to what we had before
# the difference is that bot is active, but not reactive
```

## Deep dive

Bot's documentation is being prepared and coming soon... 
until then, please have a look onto [examples](./examples).

If things are still unclear, don't hesitate to contact the me (the author), directly. 
I will try to make things more transparent.

## Author

[Deniss Stepanovs](mailto:bellatrics@gmail.com)

## Licence

Apache 2.0

## Support

You are very welcome to contribute!

For bug reports and other issues, please open an issue on GitHub.

Pull requests are even more welcome.

For any other questions, please contact to [Deniss Stepanovs](mailto:bellatrics@gmail.com)

