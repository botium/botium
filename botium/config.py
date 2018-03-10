"""
Bot's configuration file.

author: Deniss Stepanovs
"""
import logging


class Config:
    # GLOBAL
    MODE = 'not test'

    CONFIRM_STOP = True
    CONFIRM_RESTART = True

    # -------- #
    # MESSAGES #
    # -------- #
    SHOW_WELCOME_MESSAGE = False
    SHOW_STOP_MESSAGE = True
    SHOW_RESARTED_MESSAGE = True

    MESSAGE_WELCOME = 'welcome'
    MESSAGE_STOPPED = "stopped"
    MESSAGE_RESTARTED = "restarted"

    MESSAGE_ASK_REPEAT_DIRECT = 'please choose from given options'
    MESSAGE_ASK_REPEAT_DIRECT_OPTIONS = 'options are (%s)'
    MESSAGE_ASK_REPEAT = "i didn't get it, please try to rephrase the answer"

    MESSAGE_ASK_REPEAT_FAIL = "sorry, i still didn't get it, is your answer complete?"
    MESSAGE_ASK_REPEAT_FAIL_YES = "great!"
    MESSAGE_ASK_REPEAT_FAIL_NO = "let's try again. Try to make your answer as complete as possible"
    MESSAGE_ASK_REPEAT_FAIL_SKIP = "your answer is marked as skipped"

    MESSAGE_CONFIRM = "do you confirm?"

    MESSAGE_CLARIFY = "Did you mean, %s?"
    MESSAGE_CLARIFY_OPTIONS = ['no', 'yes']
    MESSAGE_CLARIFY_NO = "sorry, let's try again"
    MESSAGE_CLARIFY_FAIL = "sorry, let's try again"

    MESSAGE_CONFIRM_FAIL = 'Please choose between "%s"'

    MESSAGE_CONFIRM_STOP = "do you really want to stop?"
    MESSAGE_CONFIRM_RESTART = "do you really want to restart the bot?"

    MESSAGE_GRAPH_WRONG_TRANSITION = "please choose one of the options"
    # ------ #
    # OTHERS #
    # ------ #

    # if bot doesn't get the anser, how many time to repeat
    RESPONSE_REPEAT_N = 2

    # clarify response if unclear (by default, can be overwritten)
    RESPONSE_CLARIFY = True
    # min levenshtein to clarify the answer (not to repeat)
    RESPONSE_CLARIFY_CONF = 0.65
    # store response (by default, can be overwritten)
    RESPONSE_STORE = True

    CLARIFY_ALLOW_SKIP = False

    STORE_PARAMETERS = dict(where='general', question='question', answer='answer', match='match')
    # if false -> str of time
    STORE_HASH_KEY = True
    # store time in the answers and question or not
    STORE_TIME = True
    # store what was expected
    STORE_MATCH = True

    # options for yes and no (!change only possible answers!)
    CONFIRM_OPTIONS = dict(no=['n', 'no', 'nope', 'negative', 'not', 'disagree', 'not right'],
                           yes=['y', 'yes', 'yeah', 'yeap', 'positive', 'sure', 'agree', 'confirm', 'right'])

    CONFIRM_SKIP_OPTIONS = dict(no=CONFIRM_OPTIONS['no'],
                                skip=['skip', 's'],
                                yes=CONFIRM_OPTIONS['yes'])

    # history limit (how much to story in progress.history)
    HISTORY_LIMIT = 64
    # log (user:messages and bot:says)
    LOG_LIMIT = 64

    PROVIDE_DELAYS = True
    # ~1/delay (Word per Minute)
    WPM = 300

    def __init__(self, config=None):
        if type(config) == dict:
            self._update(config)

    def _update(self, config_dict):
        for k, v in config_dict.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                logging.error("unknown config key (%s)" % k)

    def update(self, config=None, **kwargs):
        params = dict(**kwargs)
        if type(config) == dict:
            params.update(config)

        self._update(params)


config = Config()
