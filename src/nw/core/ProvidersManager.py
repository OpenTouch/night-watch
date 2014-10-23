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
This module manages loading of Providers' modules and Providers' configuration file.
'''

_provider_package = 'nw.providers' # Name of the package where are located the providers.
_loadedProviders = {} # Providers modules are loaded only if required. Once loaded, they are stored in _loadedProviders.
_providerConfig = {} # Providers configuration (if exists) is loaded only once for each module and only if required. Once loaded, they are stored in _providerConfig.

        
def getProviderClass(provider_name):
    '''
    Load the Provider module and return the provider's class to be instantiated by the Task
    '''
    p = _loadProvider(provider_name)
    # Note: currently, ProviderManager expects that the name of the provider's class to load is the provider's name. 
    # Class name will have to be passed in parameter if we want to specify which class has to be loaded from the provider
    return getattr(p, provider_name)

def getProviderConfig(provider_name):
    '''
    Load the Provider's config (if exist) and return the config as Python dict (to be used by the Providers' instances).
    If no config file is available for this Provider, None is returned.
    
    Notes: 
        - Provider's config files are optional. Some Providers might not need to be configured through config files (the configuration
            through the tasks config files can be enough).
        - Each parameter of Provider's configuration file can be overwritten by each task in the tasks config files.
        - The Provider's config files are expected to be stored in config.providers_location section of the main Night Watch's config file.
        - The name of the provider's config file is expected to be {provider's name}.py
    '''
    # Load the provider's config (if exist)
    if _loadProviderConfig(provider_name):
        return _loadProviderConfig(provider_name).copy()
    else:
        return None


def _loadProvider(provider_name):
    # If the provider module is not already loaded, load it
    if not _loadedProviders.has_key(provider_name):
        getLogger(__name__).debug('Load provider "' + provider_name + '"')
        _loadedProviders[provider_name] = import_module(_provider_package + '.' + provider_name)
    else:
        getLogger(__name__).debug('Provider "' + provider_name + '" is already loaded')
    return _loadedProviders[provider_name]

def _loadProviderConfig(provider_name):
    # If the provider's config is not already loaded, check if a config exist for this provider and load it
    if not _providerConfig.has_key(provider_name):
        # if the folder which will contain the log file don't exists, create it
        path_config_file = os.path.join(getNwConfiguration().providers_location, provider_name + '.yml')
        getLogger(__name__).debug('Try to load config file for provider "' + provider_name + '" from location ' + path_config_file)
        if os.path.exists(path_config_file):
            _providerConfig[provider_name] = loadYamlFile(path_config_file)
            getLogger(__name__).info('Config file for provider "' + provider_name + '" successfully loaded from location ' + path_config_file)
        else:
            # No config file available for this Provider, store None so that the ProvidersManager does not try to load again the config file for this Provider
            _providerConfig[provider_name] = None
            getLogger(__name__).info('No config file found for provider "' + provider_name + '"')
    else:
        getLogger(__name__).debug('Config file for provider "' + provider_name + '" is already loaded')
    return _providerConfig[provider_name]
