# Copyright (c) 2014 Alcatel-Lucent Enterprise
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from setuptools import find_packages
from setuptools import setup

long_description = """\
The Night Watch Daemon is in charge of executing monitoring tasks: it collects data from different sources (Providers) and performs some Action(s) if the collected data does not match a given criteria.
The tasks are configured through config files. Each task is configured:
    - to run with a given periodicity,
    - to use a Provider with given option, responsible to collect the monitored data,
    - to match a criteria for the data,
    - to run Action(s) if the collected data does not match the criteria.
The Providers and Actions are available as plugins, and new ones can easy be implemented and added to the Night Watch Daemon.
"""

pkgdir = {'': 'src'}

setup(
    name = 'night-watch',
    version = '1.0',
    description = 'Night Watch: monitors metrics and acts if the metrics does not have the expected value.',
    keywords = 'monitoring event alarm',
    long_description = long_description,
    author = 'Alcatel-Lucent Enterprise Personal Cloud R&D',
    author_email = 'dev@opentouch.net',
    url = 'https://github.com/OpenTouch/night-watch',
    package_dir=pkgdir,
    packages=find_packages('src', exclude=['bin']),
    include_package_data=True,
    scripts=['bin/night-watch'],
    platforms = ['All'],
    license = 'Apache 2.0',
)
