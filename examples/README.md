# Examples

In this section you find several examples that steepens your learning curve.
If something is not clear, please don't hesitate to contact me.

More examples will come soon.

## Basic Usage

This category contains some basic use cases

#### Ask action
* [basic_ask](./examples/basic_ask.py)

Ask is quite the central action of the bot. 
This example shows how to setup the ask using some of its parameters.

You can specify:
* what type of answer you expect
* where to store the question/answer pair
* what extra information to store
* what actions to perform after question is answered, also, depending on the answer


#### Graph action
* [basic_graph](./examples/basic_graph.py)

Graph is a bot's action for creating state-machine-like flow.
You need to define states, possible transitions between them and actions performed when moving to a new state.
The rest bot will do for you.
You can also create no-exit graphs too.


#### Triggers, Conditions and Events
* [basic_trigger](./examples/basic_trigger.py)

Sometimes it is necessary to remind a user of something or do something regardless of the standard flow.
To accomplish this, one sets up a trigger.
This example guides you through this process.
You will learn how define and set up a trigger, conditioned on user's text and message statistics


#### Pausing
* [basic_pause](./examples/basic_pause.py)

If you want to create a flexible flow that has a mainstream, but doesn't force user to strictly follow it, this example should be of help to you.
The standard use case is setting up a Tutorial, where user is guided and adviced on his way.
The example shows how to do this using Pause action.
Pause simply pauses all actions in the queue until certain condition is met

#### Creating bot area and a new signal
* [complex_area_twitter](./examples/complex_area_twitter.py)

This example will illustrate how to create a new Signal and Area that listens to the signal.


## Integration
Here you find a few examples of how to integrate other NLP tools with the bot's framework.

#### Spacy integration

* [Spacy Integration](./examples/spacy_entities.py)

[Spacy](https://spacy.io/) provides pretrained models for named entity recognition (NER).
In this example you will learn how to integrate spacy's NER.
You will also learn how to force the bot to perform some actions, and some aspects of `Ask` action.


#### Rasa Integration

[Rasa](https://github.com/RasaHQ/rasa_nlu) is another framework that help bot development.
Rasa's NLU part can be easily integrated.
Here you find examples of how to do it.

These are good examples of how to integrate "something" that provides intent recognition.

* [Simple Rasa Integration example](./examples/rasa_simple.py)

In this example you will learn how to integrate intent recognition abilities of Rasa.
We will add one extra intent that will control the behavior of Rasa.

* [Complex Rasa Integration example](./examples/rasa_complex.py)

This example will teach you how to define a complete task: from user input to the result, using some extra API call.
We will create a new `Action` and define our task using `Attend` action.
This example is similar to one of Rasa.
