from executors.runner import DockerRunner, NativeRunner
from nose.tools import nottest

def test_docker_runner():
    command = ['bash', '-c', 'grep -r chr > output.txt']
    runner = DockerRunner()
    runner.run(command)
    pass

@nottest
def test_native_runner():
    command = ['grep', '-r', 'chr']
    pass