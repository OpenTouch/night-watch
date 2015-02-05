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

import logging

from nw.core.Utils import loadYamlFile


class NwConfiguration:
    
    def read(self, config_file):
        
        logger = logging.getLogger()
        
        # Open general config file
        try:
            config = loadYamlFile(config_file)
        except Exception, e:
            logger.critical('Could not read config file from ' + config_file + '. Reason is: ' + e.message, exc_info=True)
            exit(-1)

        # Parse config file
        try:
            # stores logging section directly as Python dictionary (directly usable to configure Python logging module)
            self.logging = None
            if config.has_key('logging'):
                self.logging = config['logging']
    
            # store config paths
            self.tasks_location = config['config']["tasks_location"]
            self.providers_location = config['config']["providers_location"]
            self.actions_location = config['config']["actions_location"]
            
            # webserver configuration
            self.is_webserver_enabled = config['config'].get("webserver_enabled", False)
            if self.is_webserver_enabled:
                self.webserver_port = config['config'].get("webserver_port", 8888)
                self.webserver_debug = config['config'].get("webserver_debug", False)
        
            logger.info('Configuration parsed')
            logger.debug(str(self))
            
        except KeyError, e:
            logger.critical('Configuration section "' + e.message + '" is missing, please check config file "' + config_file + '"', exc_info=True)
            exit(-1)
            
    def __str__(self):
        return 'Night-Watch configuration: \n' + \
            'Config files locations:\n' + \
            'tasks location: {0}\n'.format(self.tasks_location) + \
            'providers location: {0}\n'.format(self.providers_location) + \
            'actions location: {0}\n'.format(self.actions_location)

conf = NwConfiguration()

def getNwConfiguration():
    return conf
