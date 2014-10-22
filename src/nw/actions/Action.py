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

from nw.core import ActionsManager

from logging import getLogger

'''
This class represents an 'Abstract' Action.
All the Actions should extend this class and overload:
    - __init__ (constructor) to handle Action's initialization based on the configuration,
    - 'process' method so that it process the expected action according to the Action's configuration.
    - _mandatory_parameters and _optional_parameters attributes, allowing to verify that the Action's configuration is valid.
The Action's configuration comes from:
    - the Action's configuration file, loaded using the ActionsManager (if the file exists),
    - "task_options" argument of __init__ function, corresponding to options defined in the tasks configuration files for the Action.
    NOTE: the options coming from the "task_options" argument overwrite the options coming from the Action's configuration file.

The Actions can overload the method '_isConfigValid' to add other verifications on their configuration.        
'''
class Action:
    
    '''
    The Actions must overload _mandatory_parameters and _optional_parameters to list the parameters it require / manage (list of strings).
    '''
    _mandatory_parameters = []
    _optional_parameters = []
    
    def __init__(self, task_options):
        '''
        Handle Action's configuration:
        - stores the Action's configuration file (loaded using the ActionsManager) if the file exists,
        - use "task_options" argument provided by the tasks (coming from the tasks configuration files using this Action) to 
            overwrite the configuration read from Action's configuration file.
        '''
        # Read Action's config file
        self._config = ActionsManager.getActionConfig(self.__class__.__name__)
        if task_options and type(task_options) is dict:
            # If Action's config file has been loaded, overwrite its config with task options
            if self._config and type(self._config) is dict:
                self._config.update(task_options)
            # If the Action does not have a config file, the options are the one coming from task options
            else:
                self._config = task_options
        # Check if the configuration is valid for the Action (if not, raise an exception)
        if not self._isConfigValid():
            raise Exception('Invalid configuration for action "' + self.__class__.__name__ + '"')
        else:
            getLogger(__name__).debug('Configuration for action "' + self.__class__.__name__ + '" is valid. Config is: ' + str(self._config))
        
    def process(self):
        '''
        Abstract method which has to be overloaded by each Action so that it collects and returns the expected metric, 
        according to the Action' configuration.
        '''
        pass
    
    def _isConfigValid(self):
        '''
        Method which verify if the Action's configuration is valid:
            - check if the mandatory parameters are provided (raise an Exception if that is not the case),
            - check if the optional parameters are provided (otherwise write a log),
            - check if the provided parameters are managed by the Action (otherwise write a log).
        The Actions must overload _mandatory_parameters and _optional_parameters to list the parameters it require / manage.
        
        The Actions can overload this function to add other verifications on their configuration.
        If they return False, an Exception is raised by Action class during __init__.
        '''
        # Check if all the mandatory parameters are provided, otherwise raise an exception
        for param in self._mandatory_parameters:
            if not self._config.has_key(param):
                raise AttributeError('Invalid configuration for Action "' + self.__class__.__name__ + '": mandatory parameter "' + param + '" is not provided. Please check Action/task configurations.')
        
        # Check if all the optional parameters are provided, otherwise write a log
        for param in self._optional_parameters:
            if not self._config.has_key(param):
                getLogger(__name__).info('Optional parameter "' + param + '" is not provided to Action "' + self.__class__.__name__ + '"')
        
        # Check if the provided parameters are in the mandatory or optional Action's parameter list. If not, the parameter is unknown to the Action, write a log
        for param in self._config.keys():
            if param not in self._mandatory_parameters and param not in self._optional_parameters:
                getLogger(__name__).warning('The provided parameter "' + param + '" is not managed by Action "' + self.__class__.__name__ + '".')
        
        return True
        
