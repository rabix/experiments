import sys
import json
import yaml

from os.path import dirname, join

from jsonschema.validators import validator_for, validate


def validate_schema(schema):
    cls = validator_for(schema)
    cls.check_schema(schema)


def validate_tool(tool):
    schema_path = join(dirname(__file__), 'tool.json')
    tool_schema = json.load(open(schema_path))
    validate(tool, tool_schema)


def validate_job_inputs(job, tool):
    validate(job['inputs'], tool['inputs'])


def clean_none(d):
    return {k: v for k, v in d.iteritems() if v is not None}


def load_tool(path):
    with open(path) as f:
        tool = clean_none(yaml.load(f))
    return tool


def main(args=None):
    if args is None:
        args = sys.argv
    for f in args:
        tool = load_tool(f)
        validate_tool(tool)

if __name__ == "__main__":
    main()
