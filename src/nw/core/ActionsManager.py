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

from logging import getLogger
from importlib import import_module
import os

from nw.core.NwConfiguration import getNwConfiguration
from nw.core.Utils import loadYamlFile


'''
This module manages loading of Actions' modules and Actions' configuration file.
'''

_action_package = 'nw.actions' # Name of the package where are located the Actions.
_loadedActions = {} # Actions modules are loaded only if required. Once loaded, they are stored in _loadedActions.
_actionConfig = {} # Actions configuration (if exists) is loaded only once for each module and only if required. Once loaded, they are stored in _actionConfig.

        
def getActionClass(action_name):
    '''
    Load the Action module and return the Action's class to be instantiated by the Task
    '''
    p = _loadAction(action_name)
    # Note: currently, ActionManager expects that the name of the action's class to load is the action's name. 
    # Class name will have to be passed in parameter if we want to specify which class has to be loaded from the action
    return getattr(p, action_name)

def getActionConfig(action_name):
    '''
    Load the Action's config (if exist) and return the config as Python dict (to be used by the Actions' instances).
    If no config file is available for this Action, None is returned.
    
    Notes: 
        - Action's config files are optional. Some Actions might not need to be configured through config files (the configuration
            through the tasks config files can be enough).
        - Each parameter of Action's configuration file can be overwritten by each task in the tasks config files.
        - The Action's config files are expected to be stored in config.actions_location section of the main Night Watch's config file.
        - The name of the action's config file is expected to be {action's name}.py
    '''
    # Load the action's config (if exist)
    return _loadActionConfig(action_name)


def _loadAction(action_name):
    # If the action module is not already loaded, load it
    if not _loadedActions.has_key(action_name):
        getLogger(__name__).debug('Load action "' + action_name + '"')
        _loadedActions[action_name] = import_module(_action_package + '.' + action_name)
    else:
        getLogger(__name__).debug('Action "' + action_name + '" is already loaded')
    return _loadedActions[action_name]

def _loadActionConfig(action_name):
    # If the Action's config is not already loaded, check if a config exist for this Action and load it
    if not _actionConfig.has_key(action_name):
        # build the path of the Action to load by concatenating the actions_location config section from main config file with the {name of the action to load}.yml
        path_config_file = os.path.join(getNwConfiguration().actions_location, action_name + '.yml')
        getLogger(__name__).debug('Try to load config file for action "' + action_name + '" from location ' + path_config_file)
        if os.path.exists(path_config_file):
            _actionConfig[action_name] = loadYamlFile(path_config_file)
            getLogger(__name__).info('Config file for action "' + action_name + '" successfully loaded from location ' + path_config_file)
        else:
            # No config file available for this Action, store None so that the ActionsManager does not try to load again the config file for this Action
            _actionConfig[action_name] = None
            getLogger(__name__).info('No config file found for action "' + action_name + '"')
    else:
        getLogger(__name__).debug('Config file for action "' + action_name + '" is already loaded')
    return _actionConfig[action_name]
