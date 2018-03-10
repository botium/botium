"""
Contains wrappers for modern NLP tools like Spacy and Rasa.

author: Deniss Stepanovs
"""
import json, re
import logging


class NlpData:
    entity_regex = re.compile(r'\[(?P<entity_text>[^\]]+)'
                              r'\]\((?P<entity>\w*?)'
                              r'(?::(?P<value>[^)]+))?\)')  # [entity_text](entity_type(:entity_synonym)?)

    def from_md(self, text_md):
        r = dict()
        block_content = re.findall(r'#+\s*([^\n]+)([^#]+)', text_md)
        for block, content in block_content:
            r[block.strip()] = [l.strip() for l in re.findall(r'[-*+]\s+(.+)', content)]

        data = []
        for k, pp in r.items():
            for p in pp:
                what, value = map(str.strip, k.split(':'))
                if what == 'intent':
                    text = self.entity_regex.sub(r'\1', p)
                    entities = [dict(value=e[0], entity=e[1]) for e in self.entity_regex.findall(p)]
                    data.append(dict(entities=entities, intent=value, text=text))

        return data

    def _readfile(self, file=None, filename=None):
        if filename is not None:
            file = open(filename)

        file_data = file.read()

        try:
            # trying json first
            data = json.loads(file_data)

        except:
            # otherwise must be MD
            data = self.from_md(file_data)

        if 'rasa_nlu_data' in data:
            # rasa format
            data = data['rasa_nlu_data']['common_examples']

        return data

    def __init__(self, obj):
        if type(obj) == str:
            # file name
            self.data = self._readfile(filename=obj)

        elif hasattr(obj, 'read'):
            # file
            self.data = self._readfile(file=obj)
        else:
            self.data = obj


class Nlp:
    _entity_keys = {'entity', 'value', 'confidence', 'start', 'end'}
    _intent_keys = {'intent', 'confidence'}

    @staticmethod
    def _transform_data(data):
        return NlpData(data).data

    def _validate(self, result):
        for entity in result['entities']:
            if not {'entity', 'value'}.issubset(entity):
                logging.error("entities should have right structure: [dict(entity=..., value=...), ...]")

        for intent in result['intents']:
            if not {'intent', 'confidence'}.issubset(intent):
                logging.error("intents should have right structure: [dict(intent=..., confidence=...), ...]")

    def predict(self, text):
        """text -> dict(intent_ranking=..., entities=...)"""
        raise AttributeError('please define .predict method')

    def __call__(self, text):
        predict_result = self.predict(text)

        result = dict()
        result["entities"] = predict_result.get("entities", [])
        result["entities"] = [{k: v for k, v in entity.items() if k in self._entity_keys} for entity in
                              result["entities"]]

        result["intents"] = predict_result.get("intents", [])
        result["intents"] = [{k: v for k, v in intent.items() if k in self._intent_keys} for intent in
                             result["intents"]]
        result["intents"] = sorted(result["intents"], key=lambda x: x['confidence'], reverse=True)

        self._validate(result)

        return result


class RasaNlp(Nlp):
    def __init__(self, file_name, lang='en'):
        from rasa_nlu.training_data import load_data
        from rasa_nlu.config import RasaNLUConfig
        from rasa_nlu.model import Trainer

        self.data = load_data(file_name)
        self._trainer = Trainer(RasaNLUConfig(cmdline_args=dict(pipeline="spacy_sklearn", language=lang)))
        self._interpreter = self._trainer.train(self.data)

    def predict(self, text):
        r = self._interpreter.parse(text)
        r['intents'] = r.pop('intent_ranking')
        for intent in r['intents']:
            intent['intent'] = intent.pop('name')

        return r


class SpacyEntitiesNlp(Nlp):
    def __init__(self, lang='en'):
        import spacy

        self._nlp = spacy.load(lang)

    def predict(self, text):
        doc = self._nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append(dict(entity=ent.label_,
                                 value=ent.text))
        return dict(entities=entities)


class SpacySklearnNlp(Nlp):
    def __init__(self, data, lang='en', clf=None):
        import spacy
        from sklearn.linear_model import LogisticRegression

        self.data = self._transform_data(data)
        self._nlp = spacy.load(lang)
        self._clf = clf if clf is not None else LogisticRegression(C=100)

        self.fit()

    def fit(self):
        X = [self._nlp(d['text']).vector for d in self.data]
        intents = [d['intent'] for d in self.data]
        self._clf.fit(X, intents)

    def predict(self, text):
        doc = self._nlp(text)
        vector = doc.vector
        probas = self._clf.predict_proba([vector])[0]

        intents = [dict(intent=intent, confidence=confidence) for intent, confidence in
                   zip(self._clf.classes_, probas)]

        entities = []
        for ent in doc.ents:
            entities.append(dict(entity=ent.label_, value=ent.text))

        return dict(entities=entities, intents=intents)


class TestNlp(Nlp):
    """Used only for tests"""

    def extract_entities(self, text):
        # text = "i am from latvia"
        patterns = [r"from (?P<location>\w+)",
                    r"(?P<location>riga|heidelberg)",

                    r"am (?P<age>\d+)",
                    r"age is (?P<age>\d+)",

                    r"name is (?P<name>\w+)",
                    r"(?P<location>bob|alice)",
                    ]

        entities = []
        for pattern in patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                if m:
                    for entity, value in m.groupdict().items():
                        entities.append(dict(entity=entity,
                                             value=value,
                                             start=m.start(1),
                                             end=m.end(1)))
        return entities

    def predict(self, text):
        return dict(entities=self.extract_entities(text))
