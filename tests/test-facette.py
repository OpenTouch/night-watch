#!/usr/bin/env python2.7
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

from nw.providers.Facette import Facette
from nw.core.NwConfiguration import getNwConfiguration
from nw.core import Log


# Read the Night Watch main config file from /etc/night-watch/night-watch.yml
config_file = '/etc/night-watch/night-watch.yml'

# Load the NW config file (required so that the Provider can load its config file)
config = getNwConfiguration()
config.read(config_file)
# Reconfigure the logger now that we loaded the logging config from NW config file
Log.reconfigure(config.logging)

config = {
          'facette_srv_url': 'http://demo.facette.io',
          'facette_srv_user': '',
          'facette_srv_pwd': '',
          'source_name': 'host1.example.net',
          'metric_name': 'load.midterm',
         }
                        
# Call facette
facette = Facette(config)
result = facette.process()
print result
