import os
import operator

from jsonschema import Draft4Validator
from cliche.ref_resolver import resolve_pointer, from_url

TRANSFORMS = {
    'strip_ext': lambda x: os.path.splitext(x)[0]
}


def arg_to_str(arg):
    return unicode(arg.arg_list()[0])


class Argument(object):
    def __init__(self, value, schema):
        self.schema = schema
        if 'oneOf' in schema:
            for opt in schema['oneOf']:
                validator = Draft4Validator(opt)
                try:
                    validator.validate(value)
                except:
                    pass
                else:
                    self.schema = opt
                    break

        self.adapter = schema.get('adapter', {})
        self.position = self.adapter.get('order', 99)
        self.prefix = self.adapter.get('prefix')
        self.separator = self.adapter.get('separator')
        if self.separator == ' ':
            self.separator = None
        self.item_separator = self.adapter.get('item_separator', ',')
        # Hackity
        if isinstance(value, dict) and 'path' in value:
            value = value['path']
        self.value = TRANSFORMS.get(self.adapter.get('transform'), lambda x: x)(value)

    def __int__(self):
        return bool(self.arg_list())

    # def make_value(self, value):
    #     value = value or self.adapter.get('value')
    #     if not value:
    #         v_from = self.adapter.get('valueFrom')
    #         value = resolve_pointer(self.job, v_from, None)
    #     value = TRANSFORMS.get(self.adapter.get('transform', lambda x: x))(value)
    #     if self.schema.get('type') in ('file', 'directory'):
    #         value = value.get('path') if value else None
    #     return value

    def arg_list(self):
        if isinstance(self.value, dict):
            return self.as_dict()
        if isinstance(self.value, list):
            return self.as_list()
        return self.as_primitive()

    def as_primitive(self):
        if self.value in (None, False):
            return []
        if self.value is True and (self.separator or not self.prefix):
            raise Exception('Boolean arguments must have a prefix and no separator.')
        if not self.prefix:
            return [self.value]
        if self.separator is None:
            return [self.prefix] if self.value is True else [self.prefix, self.value]
        return [self.prefix + self.separator + unicode(self.value)]

    def as_dict(self, extend_with=None):
        args = []
        for k, v in self.value.iteritems():
            schema = self.schema.get('properties', {}).get(k, {})
            args.append(Argument(v, schema))
        args.sort(key=lambda x: x.position)
        return reduce(operator.add, [a.arg_list() for a in args], [])

    def as_list(self):
        item_schema = self.schema.get('items', {})
        args = [Argument(item, item_schema) for item in self.value]
        if not self.prefix:
            return reduce(operator.add, [a.arg_list() for a in args], [])
        if not self.separator:
            return reduce(operator.add, [[self.prefix] + a.arg_list() for a in args], [])
        args_as_strings = map(arg_to_str, filter(None, args))
        return [self.prefix + self.separator + self.item_separator.join(args_as_strings)]


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(__file__), '../examples/tmap.yml')
    doc = from_url(path)
    tool, job = doc['mapall'], doc['exampleJob']
    print Argument(job['inputs'], tool['inputs']).arg_list() # .as_dict(extend_with=)





