import os
from collections import defaultdict

from cliche.ref_resolver import from_url, resolve_pointer


class Argument(object):

    def __init__(self, arg):
        self.arg = arg
        self.value = arg.get('value')

    @classmethod
    def from_input(cls, name, input):
        arg = input.get('adapter')
        if arg:
            arg = dict(arg)
            arg['valueFrom'] = "#inputs/" + name
            return cls(arg)
        return None

    def bind(self, job):
        value_from = self.arg.get('valueFrom')
        if value_from:
            return resolve_pointer(job, value_from)

    @property
    def weight(self):
        return self.arg.get('order', 99)


class Adapter(object):

    def __init__(self, tool):
        self.tool = tool
        self.args = [Argument(arg) for arg in tool['adapter']['args']]
        self.args += [Argument.from_input(*input)
                      for input in tool['inputs']['properties'].iteritems()
                      if input[1].get('adapter')]
        sorted(self.args, key=lambda a: a.weight)

    def cli(self, job):
        for arg in self.args:
            arg.bind(job)
        return ""



def gen_cli(tool, job):
    a = Adapter(tool)
    return a.cli(job)


def test_bwa_mem():
    path = os.path.join(os.path.dirname(__file__), '../examples/bwa-mem.yml')
    doc = from_url(path)
    tool, job = doc['tool'], doc['job']
    gen_cli(tool, job)


def test_tmap_mapall():
    path = os.path.join(os.path.dirname(__file__), '../examples/tmap.yml')
    doc = from_url(path)
    tool, job = doc['mapall'], doc['exampleJob']
    gen_cli(tool, job)
