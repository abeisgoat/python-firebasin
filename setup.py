#!/usr/bin/env python

from distutils.core import setup

setup(name='Firebasin',
      version='0.1',
      description='Websocket client for Firebase',
      author='Abraham Haskins',
      author_email='abeisgreat@abeisgreat.com',
      url='http://www.github.com/abeisgreat/python-firebasin',
      packages=['firebasin'],
      license='MIT',
      keywords=['python firebase firebasin'],
      requires=['ws4py']
     )