import io
from setuptools import setup, find_packages


setup(
    name="cliche",
    version="0.1",
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['cliche = cliche.cli:main',
                            'rabix = executors.cli:main'],
    },
    install_requires=[
        x.strip() for x in
        io.open('requirements.txt')
    ],
    long_description=io.open('README.md').read(),
    zip_safe=False,
    test_suite='tests',
    license='GPLv3'
)
