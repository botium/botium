"""
Contains bot's top level entities.

author: Deniss Stepanovs
"""
from .config import config
from .utils import *
import logging


class MemoryState(dict):
    """Dict-like structure with easy access to nested fields (e.g. 'a.b' points to {'a': {'b':...}})"""

    def _get_key_pointer(self, key, safe=True):
        """getting to the final leave, creating the structure on the way"""
        keys = key.split('.')
        # setting a pointer and creating structure on the way
        d = self
        for i, k in enumerate(keys):
            if i < len(keys) - 1:
                dict.__setitem__(d, k, dict.get(d, k, {}))

                if type(dict.__getitem__(d, k)) != dict:  # and d[k] is not None
                    if safe:
                        dict.update(d, {'_%s' % k: dict.__getitem__(d, k)})
                    dict.__setitem__(d, k, {})

                # creating the structure on the way
                d = dict.__getitem__(d, k)

        return d, k

    def _initizalize(self, state):
        if type(state) == dict:
            for k, v in state.items():
                self[k] = v

    @property
    def _state(self):
        return dict(self)

    def __setitem__(self, key, value):
        if type(value) == dict and value:
            if value:
                for k, v in value.items():
                    self[key + "." + k] = v
            else:
                # empty dict
                dict.__setitem__(self, key, {})

        else:
            pointer, k = self._get_key_pointer(key)
            dict.__setitem__(pointer, k, value)

    def get(self, item, default=None):
        value = self[item]
        return value if value else default

    def __getitem__(self, item):
        try:
            value = reduce(lambda d, k: dict.get(d, k, {None: None}), item.split('.'), self)
            return value if value != {None: None} else None
        except:
            return None

    def __delitem__(self, key):
        if self[key] is not None:
            pointer, k = self._get_key_pointer(key)
            dict.__delitem__(pointer, k)

    def pointer(self, key):
        pointer, k = self._get_key_pointer(key)
        if k not in pointer:
            pointer[k] = {}
        return pointer[k]

    def __contains__(self, key):
        return self[key] is not None

    def is_empty(self):
        return not bool(self)

    def add(self, obj):
        for k, v in obj.items():
            self[k] = v

    def __add__(self, other):
        m = self.__class__(self)
        m.add(other)
        return m

    def pop(self, key):
        value = self[key]
        del self[key]
        return value


class StackState(list):
    """basically is a list, but push and pop works on zeroth element"""

    def _initizalize(self, state):
        self.clear()
        if type(state) == list:
            self.extend(state)

    def get(self, index=0, default=None):
        # zero element or None
        return self[index] if len(self) > index else default

    @property
    def _state(self):
        return list(self)

    def is_empty(self):
        return len(self) == 0

    def add(self, objs):
        self.append(objs)

    def __add__(self, other):
        m = self.__class__(self)
        m.add(other)
        return m

    def append(self, objs):
        self.extend(list_of(objs))

    def pop(self):
        # zero element + removing it
        if len(self) > 0:
            record = self[0]
            del self[0]
            return record

        return None

    def push(self, obj):
        # pushing to zero position
        new_list = list_of(obj) + self.copy()
        self.clear()
        self.extend(new_list)

    def all(self):
        return self[:]

    def pop_all(self):
        data = self.all()
        self.clear()
        return data


class Entity:
    @classproperty
    def _name(cls):
        return cls.__name__

    @classproperty
    def _type(cls):
        parent_names = [p._name for p in cls._parents]
        types = ['Condition', 'Action', 'Intent']
        for t in types:
            if t in parent_names:
                return t
        return 'Signal'

    @classproperty
    def _children(cls):
        ks = cls.__subclasses__()
        for k in cls.__subclasses__():
            ks += k._children
        return ks

    @classproperty
    def _parents(cls):
        return [c for c in inspect.getmro(cls) if c not in {dict, list, str, object}]

    def _is(self, klass):
        """if an object is of given klass (strings are accepted)"""
        if type(klass) == str:
            return self.__class__.__name__ == klass.replace('@', '')
        return self.__class__ == klass

    def _is_relative_to(self, obj):
        """Check if obj is the older relative"""
        return is_relative_to(self, obj)

    @classmethod
    def _jsonify(cls, obj):
        """Serializes object to json"""
        if type(obj) in {int, float, str, bool, type(None)}:
            return obj
        elif type(obj) in {tuple, list, set, StackState}:
            return [cls._jsonify(o) for o in obj]
        elif type(obj) in {dict, MemoryState}:
            return {k: cls._jsonify(v) for k, v in obj.items()}
        elif type(obj) == type and obj in {int, str, bool, float}:
            # can be used for patter matching
            return "@type@%s@@" % obj.__name__

        elif type(obj) == type:
            # can be used for patter matching
            return "@@%s@@" % obj.__name__

        elif type(obj) == re._pattern_type:
            # can be used for patter matching
            return "@%s@re@%s@" % (obj.flags, obj.pattern)
        else:
            return obj._json

    @classproperty
    def _entities(cls):
        return {c.__name__: c for c in cls._children}

    @classmethod
    def _restore(cls, obj):
        """
        Restores the serialized (._json-ed) obj
        :param obj: input object
        :return: Class instance
        """

        if type(obj) in {int, float, bool, type(None)}:
            return obj

        elif type(obj) in {str}:
            arg = re.findall(r'^@([^@]*)@(.+)@([^@]*)@$', obj)
            if arg:
                arg_p1, arg_type, arg_p2 = arg[0]
                if arg_type in {'int', 'str', 'bool', 'float'}:
                    return dict(int=int, str=str, bool=bool, float=float)[arg_type]

                elif arg_type == 're':
                    if arg_p1:
                        return re.compile(arg_p2, int(arg_p1))
                    return re.compile(arg_p2)

                elif arg_p1 == arg_p2 == '':
                    _entities_dict = cls._entities
                    if arg_type in _entities_dict:
                        return _entities_dict[arg_type]

                return obj

            else:
                return obj

        elif type(obj) == dict:
            if len(obj) == 1:
                # bot's entity
                klass = cls._restore(list(obj.keys())[0])
                if type(klass) != str:
                    kwargs = list(obj.values())[0]
                    return klass(**{k: cls._restore(v) for k, v in kwargs.items()})

            # standard dict
            return {k: cls._restore(v) for k, v in obj.items()}

        elif type(obj) == list:
            return [cls._restore(o) for o in obj]

        else:
            logging.error('unknown object (%s)' % obj)


class Signal(Entity, dict):
    """Is the main carrier of information.
    When created, stores all (except "_private") parameters in its state. Parameters also accesible as class attributes.
    """
    # used for validation if defined
    _structure = {}
    _prototype = {}

    def __init__(self, **kwargs):
        super(dict, self).__init__()

        # updating kwargs with default params (if any)
        if 'default' in self._structure and type(self._structure) == dict:
            for k, v in self._structure['default'].items():
                kwargs[k] = kwargs.get(k, v)
        self.update(**kwargs)

        # creating class attributes from parameters
        for k, v in kwargs.items():
            setattr(self, k, v)

        # validating structure
        if config.MODE == 'test':
            self._validate()

    def __call__(self, *args, **kwargs):
        pass

    def __repr__(self):
        args = []
        for k, v in self.items():
            if type(v) == str:
                # inverting "->' if " present in the string
                v = ("'%s'" % v) if '"' in v else ('"%s"' % v)
            args.append((k, v))

        kwargs = ["%s=%s" % kv for kv in args]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(kwargs))

    def __getattr__(self, item):
        # is called when "get" didn't find anything
        return None

    def __setitem__(self, key, value):
        setattr(self, key, value)
        dict.__setitem__(self, key, value)

    @property
    def _json(self):
        return self._jsonify({"@@%s@@" % self.__class__.__name__: self._state})

    def copy(self):
        # deepcopy
        return Entity._restore(self._json)

    @property
    def _state(self):
        return dict(self)

    def _validate(self):
        if self._structure:
            if type(self._structure) == set:
                self._structure = {'must': self._structure}

            # must-type
            if 'must' in self._structure:
                if not self._structure['must'].issubset(self._state):
                    missing_keys = set(self._structure['must']) - set(self._state)
                    raise AttributeError("<%s> missing keys: %s" % (self._name, ", ".join(missing_keys)))

            # or-type (must)
            if 'or' in self._structure:
                passed = False
                for names in self._structure['or']:
                    if names.issubset(self._state):
                        passed = True
                        break

                if not passed:
                    missing_keys = [" ".join(keys) for keys in self._structure['or']]
                    raise AttributeError("Action: missing keys (%s)" % (" or ".join(missing_keys)))

            # checking that there is no garbage provided
            allowed_keys = [v for k, v in self._structure.items() if k in {'may', 'must'}]
            if 'or' in self._structure:
                allowed_keys += [x for x in self._structure['or']]
            if 'default' in self._structure:
                allowed_keys += [{k} for k in self._structure['default']]

            allowed_keys = set([x for y in allowed_keys for x in y])

            for key in allowed_keys:
                if key.startswith('_'):
                    logging.error("key should not start with _, it might lead to problems... might also not")

            bad_keys = set([k for k in self._state if not k.startswith('_')]) - allowed_keys
            if bad_keys:
                error_message = 'unknown keys ("%s") for <%s>' % ('", "'.join(bad_keys), self._name)
                logging.warning(error_message)

        if self._prototype:
            for key, obj in self.items():

                if obj is None and key in self._structure.get('may', {}):
                    # exception: obj is given None, but it is not obligatory
                    continue

                if key in self._prototype:
                    obj_type = self._prototype[key]
                    if not validate_type(obj, obj_type):
                        logging.error(
                            " %s>: wrong type (%s) for <%s>, required %s" % (self._name, type(obj), key, obj_type))

        # EXCEPTIONS (additional rules)
        if self._is('CountCondition'):
            if type(self.event.signal) != type:
                logging.error(
                    "counts don't work on instances, only on classes - set signal=Class or use EventCondition")

        if self._is('Attend'):
            if self.confirm_text:
                if any([x in self.confirm_text for x in ['\0', '\1', '\2']]):
                    logging.warning(
                        r'Most likely you forgot double "\" before number? or pur "r" in front of the stirng.')

    def _text_sub_kwargs(self, kwargs):
        """Substitute kwargs (\1->'text') in all action str-like fields, recursively"""

        for k, v in self.items():
            if type(v) == str:
                self[k] = text_sub_kwargs(v, kwargs)
            elif type(v) == list and all([type(x) == str for x in v]):
                self[k] = [text_sub_kwargs(x, kwargs) for x in v]
            elif is_relative_to(v, Signal):
                v._text_sub_kwargs(kwargs)
            elif type(v) == list and all([is_relative_to(x, Signal) for x in v]):
                for x in v:
                    x._text_sub_kwargs(kwargs)


class Area(Entity):
    """[Brain] Areas receive/process/outputs Signals"""

    # interfaces produce, but don't receive signals
    is_interface = False
    # what signals area listens listen to
    listen_to = []
    # area listens to self-produced signals (usually not)
    listen_to_self = False
    # priority for calling areas (important for Events: only for events that run "before")
    priority = 0

    def __init__(self, state=None, areas=None):

        self._areas = areas

        # if Area is_stateful
        if set(self.__class__.__bases__).intersection([MemoryState, StackState]):
            self.is_stateful = True
            self._initizalize(state)
        else:
            self.is_stateful = False

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._state if self.is_stateful else "Area")

    def __eq__(self, other):
        return type(self) == type(other) and self._name == other._name

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def _json(self):
        return self._jsonify({self.__class__.__name__: self._state})

    def _process_signal(self, signal_in, **kwargs):
        return list_of(signal_in(_area=self, _areas=self._areas, **kwargs)) if signal_in is not None else []
