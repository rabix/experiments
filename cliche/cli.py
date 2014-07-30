import os
from os.path import splitext

from cliche.ref_resolver import from_url, resolve_pointer

# TODO: lists, transforms


class Argument(object):
    def __init__(self, arg):
        self.arg = arg
        self.value = arg.get('value')
        self.transforms = {
            'strip_ext': lambda x: splitext(x)[0]
        }
        self.types = {
            'file': lambda val: val['path']
        }

    @classmethod
    def from_input(cls, name, input):
        arg = input.get('adapter')
        if arg:
            arg = dict(arg)
            arg['valueFrom'] = "#inputs/" + name
            arg['type'] = input['type']
            arg['transform'] = input.get('transform')
            return cls(arg)
        return None

    def bind(self, job):
        value_from = self.arg.get('valueFrom')
        if value_from:
            self.value = resolve_pointer(job, value_from[1:], None)
        return self

    def cli(self):
        type_func = self.types.get(self.arg.get('type'), str)
        transform = self.transforms.get(self.arg.get('transform'), lambda x: x)
        prefix = self.arg.get('prefix') or ''
        separator = self.arg.get('separator') or ' '
        value = transform(type_func(self.value))

        if separator != ' ':
            return [prefix + separator + value]

        if prefix:
            return [prefix, value]

        return [value]

    @property
    def weight(self):
        return self.arg.get('order', 99)


class ArrayArgument(Argument):
    def __init__(self, tool):
        super(ArrayArgument, self).__init__(tool)

    def cli(self):
        list_separator = self.arg.get('listSeparator')
        if list_separator:
            item_arg = Argument(self.arg['items'])
            values = []
            for val in self.value:
                item_arg.value = val
                values += item_arg.cli()

            self.value = list_separator.join(values)
            return super(ArrayArgument, self).cli()
        else:
            items = self.arg['items']
            items['prefix'] = self.arg.get('prefix')
            items['separator'] = self.arg.get('separator')
            item_arg = Argument(items)
            values = []
            for val in self.value:
                item_arg.value = val
                values += item_arg.cli()

            return values


class Adapter(object):
    def __init__(self, tool):
        self.tool = tool
        self.args = []

        if tool['adapter'].get('args'):
            self.args += [Argument(arg) for arg in tool['adapter']['args']]

        self.args += [Argument.from_input(*input)
                      for input in tool['inputs']['properties'].iteritems()
                      if input[1].get('adapter')]
        sorted(self.args, key=lambda a: a.weight)

    def cli(self, job):
        for req in self.tool['inputs']['required']:
            if not req in job['inputs']:
                raise RuntimeError("Required input not provided: " + req)

        cli = list(self.tool['adapter']['baseCmd'])
        for arg in self.args:
            arg.bind(job)
            if arg.value is not None:
                cli += arg.cli()
        return cli


def gen_cli(tool, job):
    a = Adapter(tool)
    return a.cli(job)


## Here be tests
from copy import deepcopy
from nose.tools import eq_

TOOL_STUB = {
    'inputs': {
        'type': 'object',
        'required': [],
        'properties': {},
        'adapter': {
            'baseCmd': [],
            'args': []
        }
    }
}


def test_simple_argument():
    arg = Argument({'order': 1, 'value': 5})
    eq_(arg.cli(), ['5'])


def test_ref_argument():
    arg = Argument({'order': 1, 'valueFrom': '#ref'})
    arg.bind({'ref': 'value'})
    eq_(arg.cli(), ['value'])


def test_argument_separator():
    arg = Argument({'order': 1, 'value': 'str', 'prefix': '-x'})
    eq_(arg.cli(), ['-x', 'str'])

    arg = Argument({'value': 'str', 'prefix': '-x', 'separator': '='})
    eq_(arg.cli(), ['-x=str'])


def test_argument_transform():
    arg = Argument({'value': 'str.ext',
                    'transform': 'strip_ext'})
    eq_(arg.cli(), ['str'])


def test_file_argument():
    arg = Argument({'value': {'path': 'a/path'},
                    'type': 'file'})
    eq_(arg.cli(), ['a/path'])


def test_list_argument():
    arg = ArrayArgument({'value': [1, 2, 3],
                         'prefix': '-x',
                         'type': 'array',
                         'items': {'type': 'number'}
    })
    eq_(arg.cli(), ['-x', '1', '-x', '2', '-x', '3'])

    arg = ArrayArgument({'value': [1, 2, 3],
                         'prefix': '-x',
                         'type': 'array',
                         'items': {'type': 'number'},
                         'listSeparator': ','
    })
    eq_(arg.cli(), ['-x', '1,2,3'])


def test_list_argument_file_transform():
    arg = ArrayArgument({'value': [{'path': 'a/b.txt'}, {'path': 'c/d.txt'}],
                         'prefix': '-x',
                         'type': 'array',
                         'items': {'type': 'file', 'transform': 'strip_ext'}
    })
    eq_(arg.cli(), ['-x', 'a/b', '-x', 'c/d'])


def test_bwa_mem():
    path = os.path.join(os.path.dirname(__file__), '../examples/bwa-mem.yml')
    doc = from_url(path)
    tool, job = doc['tool'], doc['job']
    print gen_cli(tool, job)


def test_tmap_mapall():
    path = os.path.join(os.path.dirname(__file__), '../examples/tmap.yml')
    doc = from_url(path)
    tool, job = doc['mapall'], doc['exampleJob']
    print gen_cli(tool, job)

