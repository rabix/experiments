import sys
from os.path import dirname, join
import yaml
from cliche.ref_resolver import JsonLoader


def gen_cli(doc):
    print doc
    pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    for arg in args:
        doc = yaml.load(arg)
        loader = JsonLoader()
        loader.load(doc)
        print gen_cli(doc)


if __name__ == '__main__':
    #main()
    main([join(dirname(__file__), '../examples/bwa-mem.yml')])
