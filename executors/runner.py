import os
import docker
import logging
from docker.errors import APIError


class Runner(object):

    WORKING_DIR = '/work'

    def __init__(self, working_dir='./', stdout=None, stderr=None):
        if not os.path.isabs(working_dir):
            working_dir = os.path.abspath(working_dir)
        self.working_dir = working_dir
        self.stdout = stdout
        self.stderr = stderr


    def run(self, command):
        pass


class DockerRunner(Runner):

    def __init__(self, working_dir='./', image_id='ubuntu', dockr=None, stdout=None, stderr=None):
        super(DockerRunner, self).__init__(working_dir, stdout, stderr)
        self.docker_client = dockr or docker.Client()
        self.image_id = image_id

    def make_config(self, image, command):
        config = {'Image': image,
                'Cmd': command,
                'AttachStdin': False,
                'AttachStdout': False,
                'AttachStderr': False,
                'Tty': False,
                'Privileged': False,
                'Memory': 0}
        return config

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
        return self.inspect()['State']['ExitCode'] == 0

    def get_stdout(self, container):
        self.wait(container)
        return self.docker_client.logs(container, stdout=True, stderr=False,
                                       stream=False, timestamps=False)

    def get_stderr(self, container):
        self.wait(container)
        return self.docker_client.logs(container, stdout=False, stderr=True,
                                       stream=False, timestamps=False)

    def run(self, command):
        volumes = {self.WORKING_DIR: {}}
        binds = {self.working_dir: self.WORKING_DIR}
        config = self.make_config(self.image_id, command)
        config['Volumes'] = volumes
        config['WorkingDir'] = self.WORKING_DIR
        try:
            cont = self.docker_client.create_container_from_config(config)
        except APIError as e:
            logging.ERROR('Image %s not found:' % self.image_id)
        try:
            self.docker_client.start(container=cont, binds=binds)
        except APIError:
            logging.ERROR('Failed to run container')
        return cont


class NativeRunner(Runner):

    def __init__(self, working_dir='./', stdout=None, stderr=None):
        super(NativeRunner, self).__init__(working_dir, stdout, stderr)

    def run(self, command):
        pass


if __name__=='__main__':
    command = ['bash', '-c', 'grep -r chr > output.txt']
    runner = DockerRunner()
    container = runner.run(command)
    print runner.get_stdout(container)
    print runner.get_stderr(container)