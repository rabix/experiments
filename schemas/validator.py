import sys
import json

from os.path import dirname, join

from jsonschema.validators import validator_for, validate


def validate_schema(schema):
    cls = validator_for(schema)
    cls.check_schema(schema)


def validate_tool(tool):
    schema_path = join(dirname(__file__), 'tool.json')
    tool_schema = json.load(open(schema_path))
    validate(tool, tool_schema)


def main(args=None):
    if args is None:
        args = sys.argv
    for f in args:
        validate_schema(json.load(open(f)))

if __name__ == "__main__":
    main()
