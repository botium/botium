"""
This is an example of how to create a new area (and a new signal).
It is far from basics as a standard bot equipped with "all necessary" areas.

We are going to create a new signal that caries Twitter message with a Twitter area that will process this signal.
This is not an illustration of how to build TwitterBot, but rather how to adapt the Botium to your needs.

We will create two areas:
    i) interface area that only emits a signal
    ii) standard area that process signal

Another way to make it is to do processing in the interface
    (but still emitting the signal so i can be registered as an event)

author: Deniss Stepanovs
"""

from botium import Bot, Say, Ask, Area
from botium.entities import Signal, MemoryState
from botium.ui import bot_ui, bot_cli
from botium.intents import Echo

import logging


class Tweet(Signal):
    # tweet is a must key for Tweet signal
    _structure = dict(must='tweet')
    # it should be of dict type (otherwise we will see a warning)
    _prototype = dict(tweet=dict)

    # we don't have to define a call method
    # but we can if we want: let the signal output the tweet if it is in the Twitter area
    def __call__(self, *args, **kwargs):
        pass


class Twitter(Area):
    """simple area that is interfacing with the bot"""
    is_interface = True

    # Notice! interface area must be called with kwargs only
    def __call__(self, **kwargs):
        if 'tweet' in kwargs:
            # area just creates a Tweet and sends it to all other areas
            return Tweet(tweet=kwargs['tweet'])
        else:
            logging.warning('no tweet is provided')


class Tweets(Area, MemoryState):
    """
    Area that will take care tweets: processing, storing statistics

    Notice, it inherits also from MemoryState, to make area "stateful"
    """

    is_interface = True

    # listens only to tweets
    listen_to = [Tweet]

    # we must define a call method, this is a way to tell the area what to do with the signal
    def __call__(self, signal):
        # in this simple case we know that signal is always tweet (so, no other checks are not needed)

        # getting the dict (tweet) that signal carries
        tweet = signal.tweet

        # let's listnen only to tweets from "Botium" and all two words tweets
        if tweet.get('user_id') == "Botium" or len(tweet.get('text', '').split()) == 2:
            # we store the tweet
            self['history'] = self.get('history', []) + [tweet]

            # and some statistics (per user_id)
            key = 'counts.%s' % tweet['user_id']
            self[key] = self.get(key, 0) + 1

            # lets say something when
            return Say(text='[tweet received from %s]' % tweet.get('user_id'))


# now, let plug in the area
class TwitterBot(Bot):
    # standard echo intent
    intents = [Echo]
    #
    areas = [Tweets, Twitter]

# creating a bot
bot = TwitterBot()

# creating artificial tweets

tweets = [
    # one from Botium (one word)
    dict(user_id="Botium", text="hi"),
    # one from X-man (one word)
    dict(user_id="X-man", text="hola"),
    # one from Batman with two words
    dict(user_id="Batman", text="need help")
]


for tweet in tweets:
    bot.tweets(tweet=tweet)


# sending all tweets to the bot
for tweet in tweets:
    bot.twitter(tweet=tweet)

# lets check what we have in the Tweets (!) area
# 1. only 2 tweets should have been received
bot.mouth[:]
# 2. those should be in the history
bot.tweets['history']
# 3. and counts updated
bot.tweets['counts']

# and what bot has in the state
# 1. it has tweets
bot.state['Tweets']
# 2. not much happened, but happened
bot.state['Events']['counts']