#!/usr/bin/env python
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import logging

class PyTest(TestCommand, object):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run(self):
        try:
            import cv2
            import em_stitch
            self.distribution.install_requires = [i for i in self.distribution.install_requires if not i.startswith('em_stitch')]
        except ImportError:
            pass
        print(self.distribution.install_requires)
        super(PyTest, self).run()

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import shlex
        import pytest
        self.pytest_args += " --cov=rendermodules --cov-report html "\
                            "--junitxml=test-reports/test.xml"
        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        logging.basicConfig(format=FORMAT)
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


with open('test_requirements.txt', 'r') as f:
    test_required = f.read().splitlines()

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()

setup(name='render-modules',
      use_scm_version=True,
      description='A set of python modules for doing higher level processing steps used '
                  ' render, developed for processing array tomography and EM images.'
                  'see http://github.com/saalfeldlab/render',
      author='Sharmishtaa Seshamani, Forrest Collman, Russel Torres, Gayathri Mahalingam, Sam Kinn',
      author_email='forrestc@alleninstitute.org',
      url='https://github.com/AllenInstitute/render-modules/',
      packages=find_packages(),
      package_data={'':['*.bsh','LICENSE','README.rst','*.md', 'rendermodules/point_match_optimization/*.html']},
      install_requires=required,
      setup_requires=['flake8','setuptools_scm'],
      tests_require=test_required,
      cmdclass={'test': PyTest})
