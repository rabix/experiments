import os
import operator

from jsonschema import Draft4Validator
from cliche.ref_resolver import resolve_pointer, from_url


class Argument(object):
    TRANSFORMS = {
        'strip_ext': lambda x: os.path.splitext(x)[0],
        'M-suffix': lambda x: '%sM' % x,
    }

    def __init__(self, value, schema, adapter=None):
        self.schema = schema or {}
        if 'oneOf' in schema:
            self.schema = self._schema_from_opts(schema['oneOf'], value)
        self.adapter = adapter or schema.get('adapter', {})
        self.position = self.adapter.get('order', 99)
        self.prefix = self.adapter.get('prefix')
        self.separator = self.adapter.get('separator')
        if self.separator == ' ':
            self.separator = None
        self.item_separator = self.adapter.get('item_separator', ',')
        self.transform = self.adapter.get('transform')
        if self.schema['type'] in ('file', 'directory'):
            value = value['path']  # FIXME
        self.value = self.TRANSFORMS.get(self.transform, lambda x: x)(value)

    def __int__(self):
        return bool(self.arg_list())

    def __unicode__(self):
        return unicode(self.value)

    def arg_list(self):
        if isinstance(self.value, dict):
            return self._as_dict()
        if isinstance(self.value, list):
            return self._as_list()
        return self._as_primitive()

    def _as_primitive(self):
        if self.value in (None, False):
            return []
        if self.value is True and (self.separator or not self.prefix):
            raise Exception('Boolean arguments must have a prefix and no separator.')
        if not self.prefix:
            return [self.value]
        if self.separator is None:
            return [self.prefix] if self.value is True else [self.prefix, self.value]
        return [self.prefix + self.separator + unicode(self.value)]

    def _as_dict(self, extend_with=None):
        args = [Argument(v, self.schema.get('properties', {}).get(k)) for k, v in self.value.iteritems()]
        if extend_with:
            args += extend_with
        args.sort(key=lambda x: x.position)
        return reduce(operator.add, [a.arg_list() for a in args], [])

    def _as_list(self):
        item_schema = self.schema.get('items', {})
        args = [Argument(item, item_schema) for item in self.value]
        if not self.prefix:
            return reduce(operator.add, [a.arg_list() for a in args], [])
        if not self.separator:
            return reduce(operator.add, [[self.prefix] + a.arg_list() for a in args], [])
        args_as_strings = [a._list_item() for a in args if a._list_item() is not None]
        return [self.prefix + self.separator + self.item_separator.join(args_as_strings)]

    def _list_item(self):
        as_arg_list = self.arg_list()
        if not as_arg_list:
            return None
        if len(as_arg_list) > 1:
            raise Exception('Multiple arguments as part of str-separated list.')
        return unicode(as_arg_list[0])

    def _schema_from_opts(self, options, value):
        for opt in options:
            validator = Draft4Validator(opt)
            try:
                validator.validate(value)
                return opt
            except:
                pass
        raise Exception('No options valid for supplied value.')


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(__file__), '../examples/tmap.yml')
    doc = from_url(path)
    tool, job = doc['mapall'], doc['exampleJob']
    print Argument(job['inputs'], tool['inputs']).arg_list() # .as_dict(extend_with=)





