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
from datetime import datetime
import operator

from nw.core import ProvidersManager
from nw.core import ActionsManager
from nw.core.NwExceptions import TaskConfigInvalid

# List of supported conditions
_operator_dict = {
                   '=': operator.eq,
                   'equals': operator.eq,
                   '>': operator.gt,
                   'greater': operator.gt,
                   '<': operator.lt,
                   'lower': operator.lt,
                   '!=': operator.ne,
                   'different': operator.ne
                  }

class Task():
    """
    Constructor
    """
    #def __init__(self, nw_task_manager, name, period_success, period_retry, period_failed, retries, providers, actions_failed, actions_success):
    def __init__(self, name, nw_task_manager, config, from_filename):
        self._nw_task_manager = nw_task_manager
        
        self.yaml_config = config
        self.from_yaml_filename = from_filename
        
        self.name = name
        
        # Number of retries before performing the actions
        self.retries = self.yaml_config.get('retries')
        if self.retries is None:
            getLogger(__name__).info('No retries parameter defined for Task "{}", do not use retries (action(s) are perform as soon as the task fails)'.format(self.name))
            self.retries = 0

        # Define the number of remaining retries to the number of retries allowed for this task
        self._remaining_retries = self.retries
                             
        self.period_success = self.yaml_config.get('period_success')
        if self.period_success is None:
            raise TaskConfigInvalid('Mandatory parameter period_success is not provided to task "{}"'.format(self.name))
        
        self.period_retry = self.yaml_config.get('period_retry')
        if self.retries > 0 and self.period_retry is None:
            raise TaskConfigInvalid('Mandatory parameter period_retry is not provided to task "{}"'.format(self.name))
        
        self.period_failed = self.yaml_config.get('period_failed')
        if self.period_failed is None:
            raise TaskConfigInvalid('Mandatory parameter period_failed is not provided to task "{}"'.format(self.name))
        
        # Define the task period to period_success at init
        self.period = self.period_success
        
        if self.yaml_config.get('providers') is None:
            raise TaskConfigInvalid('Mandatory parameter providers is not provided to task "{}"'.format(self.name))
        self.providers = self._loadProviders(self.yaml_config.get('providers'))
        getLogger(__name__).info('Number of providers: {}'.format(len(self.providers)))

        self.actions_failed = []
        if self.yaml_config.get('actions_failed') and type(self.yaml_config.get('actions_failed')) is dict:
            self.actions_failed = self._loadActions(self.yaml_config.get('actions_failed'))
        else:
            getLogger(__name__).warning('No action(s) defined for Task "{}" if this task failed.'.format(self.name))

        self.actions_success = []
        if self.yaml_config.get('actions_success') and type(self.yaml_config.get('actions_success')) is dict:
            self.actions_success = self._loadActions(self.yaml_config.get('actions_success'))
        else:
            getLogger(__name__).warning('No action(s) defined for Task "{}" if this task back to normal.'.format(self.name))
            
        # Boolean used to know if the task already failed in the previous iteration (allows to perform actions only the first time the issue failed)
        self._task_failed = False
        # Boolean used to know if the task is enabled or not (i.e. job is running or paused in scheduler)
        self._task_enabled = True

    """
    Public methods
    """
    def run(self):
        failed_providers = []
        success_providers = []
        for provider in self.providers:
            try:
                # Collect the metric's value from the provider
                value = provider.get('provider').process()
                getLogger(__name__).debug('Task "{}": used task provider "{}" to retrieve the value and got {}'.format(self.name, provider.get('class'), value))
            except:
                getLogger(__name__).error('Provider "{}" raised an error while collecting value for task "{}". Not able to process this task.'.format(provider.get('class'), self.name), exc_info=True)
                self._storeProviderHistory(provider, None, False)
            else:
                if self._is_condition_conform(provider, value):
                    success_providers.append(provider)
                else:
                    failed_providers.append(provider)
                
                self._storeProviderHistory(provider, value, True)
        if failed_providers:
            getLogger(__name__).debug('{} on {} providers collected values are valid for task "{}", task failed'.format(len(success_providers), len(self.providers), self.name))
            # At least one task failed
            if self._remaining_retries > 0:
                if self._remaining_retries == self.retries:
                    # Update task period to period_retry in scheduler
                    self._updateTaskPeriod(self.period_retry)
                # The task failed, but we retry as many times as specified in task configuration (retries parameter) before performing the action(s)
                getLogger(__name__).info('Task "{}" failed, but retry again the task {} times before performing the action(s)'.format(self.name, self._remaining_retries))
                self._remaining_retries -= 1 # Condition is not conform, decrement the counter of remaining retries
            elif self._task_failed:
                # If the task already failed previously, actions have already been treated (to not process again the actions)
                getLogger(__name__).info('Task "{}" still fails. Actions have already been processed (do not process again the actions)'.format(self.name))
            else:
                # Task is not conform, execute the action(s)
                self._task_failed = True
                # Update task period to period_failed in scheduler
                self._updateTaskPeriod(self.period_failed)
                getLogger(__name__).warning('Task "{}" just failed, process the actions_failed'.format(self.name))
                log_message = "when the task failed"
                for provider in failed_providers:
                    self._makeAction(self.actions_failed, log_message, False, [provider.get('condition')], [provider.get('threshold')], [provider.get('last_collected_values')[0].get('value')])
                        
        else: # Task is conform
            if self._remaining_retries != self.retries:
                getLogger(__name__).debug('Set back the remaining retries_counter ({}) to the required retries number ({}) for task "{}".'.format(self._remaining_retries, self.retries, self.name))
                self._remaining_retries = self.retries
                # Update task period from period_retry to period_success in scheduler
                self._updateTaskPeriod(self.period_success)
            elif self._task_failed:
                self._task_failed = False
                # Update task period from period_failed to period_success in scheduler
                self._updateTaskPeriod(self.period_success)
                getLogger(__name__).info('Task "{}" is back to normal, process the actions_success'.format(self.name))
                log_message = "when the task is back to normal"
                for provider in success_providers:
                    self._makeAction(self.actions_success, log_message, True, [provider.get('condition')], [provider.get('threshold')], [provider.get('last_collected_values')[0].get('value')])
            else:
                getLogger(__name__).debug('Task "{}" is still normal.'.format(self.name))
            
    def disableTask(self):
        if self._task_enabled:
            getLogger(__name__).debug('Disable task "{}".'.format(self.name))
            self._task_enabled = False
            return True
        else:
            getLogger(__name__).warning('Tried to disable task "{}" but it is already disabled.'.format(self.name))
            return False
            
    def enableTask(self):
        if not self._task_enabled:
            getLogger(__name__).debug('Enable task "{}".'.format(self.name))
            self._task_enabled = True
            return True
        else:
            getLogger(__name__).warning('Tried to enable task "{}" but it is already enabled.'.format(self.name))
            return False
            
    def isEnabled(self):
        return self._task_enabled
            
    def isSuccess(self):
        return not self._task_failed
                    
    def updateTaskPeriod(self, new_period):
        if new_period != self.period:
            getLogger(__name__).debug('Update task period from {} to {} for task "{}"'.format(self.period, new_period, self.name))
            self.period = new_period
            return True
        else:
            getLogger(__name__).warning('Tried to update task "{}" to period {}, but period is already {}.'.format(self.name, new_period, self.period))
            return False
            
    def toDict(self):
        return {
                'status': {
                    'name': self.name,
                    'is_enabled': self._task_enabled,
                    'period': self.period,
                    'retries': self.retries,
                    'remaining_retries': self._remaining_retries,
                    'is_failed': self._task_failed,
                    'providers': self._ProviderToDict()
                    },
                'config': self.yaml_config
                }
                
    def toYamlDict(self):
        self.yaml_config
            
    def __str__(self):
        return ("Task {task_name}:\n" +\
                "    - is enabled: {enabled}\n" +\
                "    - period: {period}\n" +\
                "    - retries: {retries}\n" +\
                "    - remaining_retries: {remaining_retries}\n" +\
                "    - is_failed: {task_failed}"
                ).format(task_name=self.name, enabled=self._task_enabled, period=self.period, retries=self.retries, remaining_retries=self._remaining_retries, task_failed=self._task_failed)
    
    
    """
    Private methods
    """
    def _loadActions(self, actions):
        loadedActions = []
        for action_name, action_options in actions.iteritems():
            a = ActionsManager.getActionClass(action_name)
            loadedActions.append(a(action_options))
        return loadedActions

    def _loadProviders(self, providers):
        loadedProviders = []
        for provider in providers:
            for provider_name, provider_options in provider.iteritems():
                # Check if provider config is valid
                condition = provider_options.get('condition')
                if condition is None:
                    raise TaskConfigInvalid('Mandatory parameter condition is not provided to task "{}"'.format(self.name))
                if not _operator_dict.has_key(condition):
                    raise TaskConfigInvalid('Parameter condition "{condition}" provided to task "{task_name}" is not allowed. Allowed conditions are: {allowed_contitions}'.format(condition=condition, task_name=self.name, allowed_contitions=_operator_dict.keys()))
                threshold = provider_options.get('threshold')
                if threshold is None:
                    raise TaskConfigInvalid('Mandatory parameter threshold is not provided to task "{}"'.format(self.name))
                
                p = ProvidersManager.getProviderClass(provider_name)
                loadedProviders.append({
                                        'class': provider_name,
                                        'condition': condition,
                                        'threshold': threshold,
                                        'last_collected_values': [],
                                        'provider': p(provider_options.get('provider_options'))
                                        })
        return loadedProviders
    
    def _storeProviderHistory(self, provider, value, status):
        provider.get('last_collected_values').insert(0, {
                                                          'time': str(datetime.now()),
                                                          'value': value,
                                                          'is_success': status
                                                          })
        # TODO: configure max number of history
        if len(provider.get('last_collected_values')) > 5:
            provider.get('last_collected_values').pop()
    
    def _ProviderToDict(self):
        p = []
        for provider in self.providers:
            p.append({
                        'class': provider.get('provider_name'),
                        'condition': provider.get('condition'),
                        'threshold': provider.get('threshold'),
                        'last_collected_values': provider.get('last_collected_values')
                      })
        return p
                
    def _makeAction(self, actions_to_do, log_message, state, conditions, thresholds, values):
        if (actions_to_do):
            for action in actions_to_do:
                try:
                    getLogger(__name__).info('Process the action "' + action.__class__.__name__ + '" for task "' + self.name + '" "' + log_message)
                    action.process(state, conditions, thresholds, values)
                except:
                    getLogger(__name__).error('Action "' + action.__class__.__name__ + '" for task "' + self.name + '" "' + log_message +'" raised an error while processing', exc_info=True)
        else:
            getLogger(__name__).warning('No action is defined for this task ' + self.name + '" "' + log_message)      

    def _is_condition_conform(self, provider, value):
        # TODO: keep a few history of provider's collected values
        log_msg = 'Task "{task_name}": provider "{provider_name}" returned {value}, expected: {condition} {threshold}'.format(task_name=self.name, provider_name=provider.get('class'), value=value, condition=provider.get('condition'), threshold=provider.get('threshold'))
        if _operator_dict[provider.get('condition')](value, provider.get('threshold')):
            getLogger(__name__).debug(log_msg)
            return True
        else:
            getLogger(__name__).warning(log_msg)
            return False
                    
    def _updateTaskPeriod(self, new_period):
        if new_period != self.period:
            self._nw_task_manager.updateTaskPeriod(self.name, new_period)
        else:
            getLogger(__name__).warning('Tried to update task "{}" to period {} but period is already {}.'.format(self.name, new_period, self.period))