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

import logging.config
import os

DEFAULT_LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)-8s] [%(threadName)-10s] [%(module)s]: %(message)s'
DEFAULT_LEVEL = logging.INFO


def init():
    '''
    This function set the default Log level. The default logger is used before night-watch.yml config file has been read, 
    allowing to debug problems during configuration load.
    The default logger is also used in the case the section 'logging' is not provided / empty in night-watch.yml config file, 
    or if it couln't be parsed by the logging.dict() function.
    '''
    # set the default log level
    logging.basicConfig(level=DEFAULT_LEVEL, format=DEFAULT_LOG_FORMAT)
    
def reconfigure(config):
    """
    Setup logging configuration from the logging section provided in the night-watch.yml config file.
    This function is called after night-watch.yml config file has been read, providing the logging config section as a Python dictionary.
        Note: the logging section must be a dictionary parsable by the logging.dictConfig() function
        (see https://docs.python.org/2/library/logging.config.html#logging-config-dict-connections).
    """
    if config:
        # For each handlers using files, check if the folder used exists. If not, try to create the folder(s) 
        #  (in the case the folder couldn't be created, the config can't be loaded and the default logger is kept)
        if config.has_key('handlers'):
            for handler_name, handler_config in config['handlers'].iteritems():
                if handler_config.has_key('filename'):
                    try:
                        # if the folder which will contain the log file don't exists, create it
                        path_log_file = os.path.dirname(handler_config['filename'])
                        if path_log_file != '' and not os.path.exists(path_log_file):
                            os.makedirs(path_log_file, 700)
                    except Exception:
                        logging.getLogger().error('Unable to access/create log folder ' + path_log_file + ' for handler ' + handler_name + ', continue with default logger', exc_info=True)
                        return
        
        try:    
            # Load the log configuration
            logging.config.dictConfig(config)
            logging.getLogger(__name__).info('Logging config successfully loaded')
        except Exception:
            logging.getLogger().error('Unable to load the logging configuration, continue with default logger.\n' \
                                      'Please check logging section of night-watch.yml config file.\n' \
                                      'The logging section must be a dictionary parsable by the logging.dictConfig() function (see https://docs.python.org/2/library/logging.config.html#logging-config-dict-connections)', exc_info=True)
            return
    
    else: # config section not defined
        logging.getLogger().info('No logging section defined in night-watch.yml config file, continue with default logger')
