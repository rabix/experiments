import os
from cliche.ref_resolver import from_url


def gen_cli(tool, job):
    print tool
    print job


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
