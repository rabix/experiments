import os
import docker
import logging
import uuid
import stat
import json
import copy
from docker.errors import APIError
from cliche.adapter import Adapter, from_url
from cliche.transforms import sbg_schema2json_schema



class BindDict(dict):

    def items(self):
        ret = []
        for k, v in self.iteritems():
            ret.append((v, k))
        return ret


class Runner(object):

    WORKING_DIR = '/work'

    def __init__(self, tool, working_dir='./', stdout=None, stderr=None):
        if not os.path.isabs(working_dir):
            working_dir = os.path.abspath(working_dir)
        self.tool = tool
        self.container = tool['requirements']['environment']['container']
        self.image_id = tool['requirements']['environment']['container']['imageId']
        self.working_dir = working_dir
        self.stdout = stdout
        self.stderr = stderr

    def run(self, command):
        pass

    def run_job(self, job):
        pass

    def rnd_name(self):
        return str(uuid.uuid4())
        #return '-'.join([uuid.uuid4(), self.tool.get('description')]) get name DOAP


class DockerRunner(Runner):

    def __init__(self, tool, working_dir='./', dockr=None, stdout=None, stderr=None):
        super(DockerRunner, self).__init__(tool, working_dir, stdout, stderr)
        self.docker_client = dockr or docker.Client()

    def make_config(self, image, command):
        config = {'Image': image,
                  'Cmd': command,
                  'AttachStdin': False,
                  'AttachStdout': False,
                  'AttachStderr': False,
                  'Tty': False,
                  'Privileged': False,
                  'Memory': 0
                }
        return config

    def volumes(self, job):
        remaped_job = copy.deepcopy(job)
        volumes = {}
        binds = {}
        is_single = lambda i: inputs[i]['type'] == 'directory' or inputs[i]['type'] == 'file'
        is_array = lambda i: inputs[i]['type'] == 'array' and \
                             (inputs[i]['items']['type'] == 'directory' or
                              inputs[i]['items']['type'] == 'file')

        inputs = self.tool.get('inputs', {}).get('properties')
        input_values = remaped_job.get('inputs')
        if inputs:
            single = filter(is_single, [i for i in inputs])
            lists = filter(is_array, [i for i in inputs])
            for inp in single:
                docker_dir = '/' + inp
                dir_name, file_name = os.path.split(os.path.abspath(input_values[inp]['path']))
                volumes[docker_dir] = {}
                binds[docker_dir] = dir_name
                remaped_job['inputs'][inp]['path'] = '/'.join([docker_dir, file_name])
            for inp in lists:
                for num, inv in enumerate(input_values[inp]):
                    docker_dir = '/' + '/'.join([inp, str(num)])
                    dir_name, file_name = os.path.split(os.path.abspath(inv['path']))
                    volumes[docker_dir] = {}
                    binds[docker_dir] = dir_name
                    remaped_job['inputs'][inp][num]['path'] = '/'.join([docker_dir, file_name])
            return volumes, BindDict(binds), remaped_job

    def inspect(self, container):
        return self.docker_client.inspect_container(container)

    def is_running(self, container):
        return self.inspect(container)['State']['Running']

    def wait(self, container):
        if self.is_running(container):
            self.docker_client.wait(container)
        return self

    def is_success(self, container):
        self.wait(container)
        return self.inspect(container)['State']['ExitCode'] == 0

    def get_stdout(self, container):
        self.wait(container)
        return self.docker_client.logs(container, stdout=True, stderr=False,
                                       stream=False, timestamps=False)

    def pipe_stdout(self, container, pipe):
        stream = self.docker_client.logs(container, stdout=True, stream=True)
        while True:
            try:
                pipe.write(stream.next())
            except StopIteration:
                pipe.close()
                return
            else:
                raise RuntimeError

    def get_stderr(self, container):
        self.wait(container)
        return self.docker_client.logs(container, stdout=False, stderr=True,
                                       stream=False, timestamps=False)

    def provide_image(self):
        if filter(lambda x: (self.image_id in x['Id']), self.docker_client.images()):
            return
        else:
            uri = self.container.get('uri')
            if not uri:
                logging.error('Image cannot be pulled')
                raise Exception('Cannot pull image')
            repo, tag = uri.split('#')
            repo = repo.lstrip('docker://')
            self.docker_client.pull(repo, tag)
            if filter(lambda x: (self.image_id in x['Id']),
                      self.docker_client.images()):
                return
            raise Exception('Image not found')

    def run(self, command, vol=None, bind=None, **kwargs):
        volumes = vol or {self.WORKING_DIR: {}}
        binds = bind or {self.working_dir: self.WORKING_DIR}
        config = self.make_config(self.image_id, command)
        config['Volumes'] = volumes
        config['WorkingDir'] = self.WORKING_DIR
        config.update(**kwargs)
        self.provide_image()
        try:
            cont = self.docker_client.create_container_from_config(config)
        except APIError as e:
            if e.response.status_code == 404:
                logging.info('Image %s not found:' % self.image_id)
                raise RuntimeError('Image %s not found:' % self.image_id)
        try:
            self.docker_client.start(container=cont, binds=binds)
        except APIError:
            logging.error('Failed to run container')
            raise RuntimeError('Unable to run container from image %s:' % self.image_id)
        return cont

    def run_job(self, job, job_id=None):
        job_dir = job_id or self.rnd_name()
        os.mkdir(job_dir)
        os.chmod(job_dir, os.stat(job_dir).st_mode | stat.S_IROTH |
                 stat.S_IWOTH | stat.S_IXOTH)
        adapter = Adapter(self.tool)
        volumes, binds, remaped_job = self.volumes(job)
        print adapter.cmd_line(remaped_job)
        print volumes
        print binds
        container = self.run(['bash', '-c', adapter.cmd_line(remaped_job)],
                             vol=volumes, bind=binds,
                             WorkingDir='/'.join([self.WORKING_DIR, job_dir]))
        if not self.is_success(container):
            raise RuntimeError("err %s" % self.get_stderr(container))
        return adapter.get_outputs(job_dir, job)


class NativeRunner(Runner):

    def __init__(self, tool, working_dir='./', stdout=None, stderr=None):
        super(NativeRunner, self).__init__(tool, working_dir, stdout, stderr)

    def run(self, command):
        pass


if __name__=='__main__':
    #command = ['bash', '-c', 'grep -r chr > output.txt']
    #command = ['/bin/bash', '-c', 'touch /reads/1/bla1']
    doc = from_url(os.path.join(os.path.dirname(__file__), '../examples/bwa-mem.yml'))
    bwa = json.load(open(os.path.join(os.path.dirname(__file__), "../tests/test-data/BwaMem.json")))
    #tool = sbg_schema2json_schema(bwa)
    tool, job = doc['tool'], doc['job']
    job = doc['job']
    runner = DockerRunner(tool)
    print(runner.run_job(job))
    #print runner.get_stdout(runner.run(command))
    # print d.items()
    # print revitems.items()
    #volumes, binds, remap_job = runner.volumes(job)
    # print binds.items()