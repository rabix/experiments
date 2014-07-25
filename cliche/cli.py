import sys
import yaml


def gen_cli(desc):

    pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    for arg in args:
        print gen_cli(yaml.load(arg))


if __name__ == '__main__':
    main()
