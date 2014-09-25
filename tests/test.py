import os
import copy
from executors.runner import DockerRunner, NativeRunner
from nose.tools import nottest, raises
from tests import mock_app_bad_repo, mock_app_good_repo

@nottest
def test_docker_runner():
    command = ['bash', '-c', 'grep -r chr > output.txt']
    runner = DockerRunner()
    runner.run(command)
    pass

@nottest
def test_native_runner():
    command = ['grep', '-r', 'chr']
    pass


@raises(Exception)
def test_provide_image_bad_repo():
    tool = copy.deepcopy(mock_app_bad_repo)
    runner = DockerRunner(tool['tool'])
    runner.provide_image()


def test_provide_image_good_repo():
    tool = copy.deepcopy(mock_app_good_repo)
    runner = DockerRunner(tool['tool'])
    runner.provide_image()

