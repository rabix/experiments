import os
import docopt
import six
import sys
from executors import __version__ as version
from executors.runner import DockerRunner
from cliche.adapter import from_url


TEMPLATE_JOB={
    'app': 'http://example.com/app.json',
    'inputs': {},
    'platform': 'http://example.org/my_platform/v1',
    'allocatedResources': {}
}

USAGE='''
Usage:
    rabix run [-v] <tool> (--job=<job> [{inputs}] | {inputs})
    rabix -h

Options:
  -h --help                               Show help
  -v --verbose                            Verbosity. More Vs more output.
'''

def make_tool_usage_string(tool):
    inputs = tool.get('inputs', {}).get('properties')
    usage_str = []
    for k, v in inputs.items():
        arg = ''
        if v.get('type') == 'file':
            arg = '--%s=<%s_file>' % (k, k)
            usage_str.append(arg if v.get('required') else '[%s]' %arg)
        elif v.get('type') == 'array' and (v.get('items').get('type') == 'file' or v.get('items').get('type') == 'directory'):
            arg = '--%s=<%s_file>...' % (k, k)
            usage_str.append(arg if v.get('required') else '[%s]' %arg)
    return USAGE.format(inputs=' '.join(usage_str))


def get_inputs(tool, args):
    inp = {}
    inputs = tool.get('inputs', {}).get('properties')
    for k in inputs.keys():
        val = args.get('--' + k)
        if val:
            if isinstance(val, list):
                inp[k]=[]
                for v in val:
                    inp[k].append({'path': v})
            else:
                inp[k] = {'path': val}
    print inp
    return {'inputs': inp}

def update_job(job, args):
    job.update(args)
    return job


def main():
    DOCOPT = USAGE
    if sys.argv[1] == 'run' and len(sys.argv) > 2:
        tool = from_url(os.path.join(os.path.dirname(__file__), sys.argv[2])).get('tool')
        DOCOPT = make_tool_usage_string(tool)
        pass
    try:
        args = docopt.docopt(DOCOPT, version=version)
        if args['run']:
            job = TEMPLATE_JOB
            if args['--job']:
                job_from_arg = from_url(os.path.join(os.path.dirname(__file__), sys.argv[2])).get('job')
                job = update_job(job, job_from_arg)
            # inp = get_inputs(tool, args)
            # update_job(job, inp)
            print job
            runner = DockerRunner(tool)
            runner.run_job(job)

    except docopt.DocoptExit:
        print(DOCOPT)
        return
    print args


if __name__=='__main__':
    main()