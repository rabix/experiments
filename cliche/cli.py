import os
from os.path import splitext

from cliche.ref_resolver import from_url, resolve_pointer

# TODO: lists, transforms


ARGUMENT_TYPES = {}


def make_argument(arg, input_name=None):
    arg_class = ARGUMENT_TYPES.get(arg.get('type'), Argument)

    if input_name:
        adapter_arg = arg.get('adapter')
        if adapter_arg:
            arg_class = ARGUMENT_TYPES.get(adapter_arg.get('type'), Argument)
            adapter_arg = dict(arg)
            adapter_arg['valueFrom'] = "#inputs/" + input_name
            adapter_arg['type'] = arg['type']
            adapter_arg['transform'] = arg.get('transform')
        else:
            return None

    return arg_class(arg)


class Argument(object):
    def __init__(self, arg):
        self.arg = arg
        self.value = arg.get('value')
        self.transforms = {
            'strip_ext': lambda x: splitext(x)[0]
        }

    def bind(self, job):
        value_from = self.arg.get('valueFrom')
        if value_from:
            self.value = resolve_pointer(job, value_from[1:], None)
        return self

    def _cli(self, prefix, separator, value):
        transform = self.transforms.get(self.arg.get('transform'), str)
        value = transform(value)

        if separator != ' ':
            return [prefix + separator + value]

        if prefix:
            return [prefix, value]

        return [value]

    def cli(self):
        return self._cli(self.prefix, self.separator, self.value)

    @property
    def weight(self):
        return self.arg.get('order', 99)

    @property
    def prefix(self):
        return self.arg.get('prefix') or ''

    @property
    def separator(self):
        return self.arg.get('separator') or ' '


class FileArgument(Argument):
    def __init__(self, arg):
        super(FileArgument, self).__init__(arg)

    def cli(self):
        return super(FileArgument, self)._cli(self.prefix,
                                       self.separator,
                                       self.value['path'])

ARGUMENT_TYPES['file'] = FileArgument


class ArrayArgument(Argument):
    def __init__(self, tool):
        super(ArrayArgument, self).__init__(tool)

    def cli(self):
        list_separator = self.arg.get('listSeparator')
        if list_separator:
            item_arg = make_argument(self.arg['items'])
            values = []
            for val in self.value:
                item_arg.value = val
                values += item_arg.cli()

            return self._cli(self.prefix,
                             self.separator,
                             list_separator.join(values))
        else:
            items = self.arg['items']
            items['prefix'] = self.arg.get('prefix')
            items['separator'] = self.arg.get('separator')
            item_arg = make_argument(items)
            values = []
            for val in self.value:
                item_arg.value = val
                values += item_arg.cli()

            return values

ARGUMENT_TYPES['array'] = ArrayArgument


class ObjectArgument(Argument):

    def __init__(self, tool):
        super(ObjectArgument, self).__init__(tool)

ARGUMENT_TYPES['object'] = ObjectArgument


class Adapter(object):
    def __init__(self, tool):
        self.tool = tool
        self.args = []

        if tool['adapter'].get('args'):
            self.args += [make_argument(arg) for arg in tool['adapter']['args']]

        self.args += [make_argument(input_spec, input_name)
                      for input_name, input_spec
                      in tool['inputs']['properties'].iteritems()
                      if input_spec.get('adapter')]
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


# # Here be tests
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
    arg = make_argument({'order': 1, 'value': 5})
    eq_(arg.cli(), ['5'])


def test_ref_argument():
    arg = make_argument({'order': 1, 'valueFrom': '#ref'})
    arg.bind({'ref': 'value'})
    eq_(arg.cli(), ['value'])


def test_argument_separator():
    arg = make_argument({'order': 1, 'value': 'str', 'prefix': '-x'})
    eq_(arg.cli(), ['-x', 'str'])

    arg = make_argument({'value': 'str', 'prefix': '-x', 'separator': '='})
    eq_(arg.cli(), ['-x=str'])


def test_argument_transform():
    arg = make_argument({'value': 'str.ext',
                         'transform': 'strip_ext'})
    eq_(arg.cli(), ['str'])


def test_file_argument():
    arg = make_argument({'value': {'path': 'a/path'},
                         'type': 'file'})
    eq_(arg.cli(), ['a/path'])


def test_list_argument():
    arg = make_argument({'value': [1, 2, 3],
                         'prefix': '-x',
                         'type': 'array',
                         'items': {'type': 'number'}
    })
    eq_(arg.cli(), ['-x', '1', '-x', '2', '-x', '3'])

    arg = make_argument({'value': [1, 2, 3],
                         'prefix': '-x',
                         'type': 'array',
                         'items': {'type': 'number'},
                         'listSeparator': ','
    })
    eq_(arg.cli(), ['-x', '1,2,3'])


def test_list_argument_file_transform():
    arg = make_argument({'value': [{'path': 'a/b.txt'}, {'path': 'c/d.txt'}],
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
