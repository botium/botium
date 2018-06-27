"""
Contains useful (and less useful) utils.

author: Deniss Stepanovs
"""
from functools import reduce
import time
import re
import random
import inspect
import uuid
import logging

def clean_text(text, lower=True):
    # TODO: remove bad characters
    if lower:
        text = text.lower()
    return " ".join(text.split())

def signal_hash():
    return str(uuid.uuid4())


def time_hash():
    return str(uuid.uuid1())[:8]


def from_camel(name):
    return re.sub('_+', '_', re.sub(r'([A-Z])', r'_\1', name).strip(' _').lower())


def to_camel(name):
    return name.replace('_', ' ').title().replace(' ', '')


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def current_time():
    return int(1000 * time.time())


def list_of(obj, keep_none=False):
    """Filters out None from the list. If object is provided, puts it in the list"""
    if obj is None:
        return [None] if keep_none else []
    else:
        if type(obj) == list:
            return [o for o in obj if keep_none or o is not None]
        return [obj]


def is_subclass_of(small, big):
    # NB! will be false for the sama classes (Ask is not sublacc of Ask)
    intersection = set(inspect.getmro(small)[1:]).intersection(set([big]))
    return bool(intersection)


def is_relative_to(klass, relative):
    klass = klass.__class__ if type(klass) != type else klass
    if type(relative) == str:
        parent_names = [c._name for c in inspect.getmro(klass) if c not in {dict, list, str, object}]
        return relative.replace('@', '') in parent_names
    else:
        parent_names = [c for c in inspect.getmro(klass) if c not in {dict, list, str, object}]
        relative_klass = relative if type(relative) == type else relative.__class__
        return relative_klass in parent_names


hash_text_regex_sub = re.compile(r"[^\w ]|_")


def hash_text(text):
    text = text.lower()
    text = hash_text_regex_sub.sub('', text)
    text = text.replace(' ', '')

    return text


def choose_text(obj):
    """randomly selecting text, if choice is present"""

    if type(obj) not in {str, list}:
        obj = obj.text

    if type(obj) == str:
        return obj
    elif type(obj) == list:
        return random.choice(obj)
    return obj


def prepare_text(text):
    # strip trash if any and titling
    text = text.strip().replace(' i ', ' I ')

    if text:
        # first upper letter
        if text.startswith('"'):
            if len(text) >= 2:
                text = '"' + text[1].upper() + text[2:]
        else:
            text = text[0].upper() + text[1:]

        # adding a dot
        if text[-1] not in {'.', '!', '?', '"', ":", "'"}:
            text += '.'

    return text


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(a, b):
    m = max(len(a), len(b))
    if m == 0:
        return 0
    return (m - levenshtein(a, b)) / m


def collect_entities(obj):
    """collects (merges) all entities (list/str) down the branch"""
    if type(obj) == dict:
        return reduce(lambda x, y: x + y, [collect_entities(v) for v in obj.values()], [])
    elif type(obj) == str:
        return collect_entities([obj])
    else:
        return obj


def validate_type(obj, obj_type):
    # type is directly specified
    if type(obj_type) == type and obj_type in {int, float, bool, str, list, dict}:
        return type(obj) == obj_type or obj == obj_type

    # string can define a class
    elif type(obj_type) == str and obj_type.startswith('@'):
        return is_relative_to(obj, obj_type)

    # object (or all objects in the list) must have a type one from the set
    elif type(obj_type) in {set}:
        # iterating over types
        for o in list_of(obj):
            passed = False
            for ot in obj_type:
                if validate_type(o, ot):
                    passed = True
                    break
            if not passed:
                return False
        return True

    # all objects should have same type as in list: e.g. [str] -> all should be strings
    elif type(obj_type) in {list}:
        # iterating over objects
        for o in list_of(obj):
            if not validate_type(o, obj_type[0]):
                return False
        return True

    elif type(obj_type) == dict:
        if len(obj_type) != 1 or type(obj) != dict:
            return False
        ot = obj_type[list(obj_type.keys())[0]]
        for v in obj.values():
            if not validate_type(v, ot):
                return False
        return True

    elif type(obj_type) in {type}:
        # if class is defined, then list containing this class members are also allowed
        return is_relative_to(obj, obj_type)

    else:
        logging.error('uknown type')


def text_sub_kwargs(text, kwargs):
    for key in kwargs:
        text = text.replace(key, kwargs[key])
    return text


# ========= #
# FOR TESTS #
# ========= #

def get_dict_value(d):
    return list(d.values())[0]


def is_empty(obj, but=set(), ignore={'Events', 'Mouth'}):
    for key, value in obj.items():
        if key in ignore:
            continue
        if key in but and not value:
            return False
        if key not in but and value:
            return False
    return True


def equal_texts(text, mouth_text, precise=True):
    if precise:
        return mouth_text == prepare_text(text)
    else:
        return mouth_text in prepare_text(text)


def compare_actions(a, b, ingnore_underscore=True):
    a = a if type(a) == dict else a._json
    b = b if type(b) == dict else b._json

    key = list(set(a.keys()).intersection(b.keys()))
    if len(key) != 1:
        return False
    key = key[0]
    return {k: v for k, v in a[key].items() if not k.startswith('_') or not ingnore_underscore} == \
           {k: v for k, v in b[key].items() if not k.startswith('_') or not ingnore_underscore}
