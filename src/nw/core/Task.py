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
        self.providers = []
        self.provider_names = []
        self.provider_conditions = []
        self.provider_thresholds = []
        self.provider_values = []
        self._loadProviders(self.providers, self.yaml_config.get('providers'))
        self.numberOfProvidersFailed = 0
        self.numberOfProviders = len(self.providers)
        getLogger(__name__).info('Number of providers:' + str(self.numberOfProviders))

        self.actions_failed = []
        if self.yaml_config.get('actions_failed') and type(self.yaml_config.get('actions_failed')) is dict:
            self._loadActions(self.actions_failed, self.yaml_config.get('actions_failed'))
        else:
            getLogger(__name__).warning('No action(s) defined for Task "{}" if this task failed.'.format(self.name))

        self.actions_success = []
        if self.yaml_config.get('actions_success') and type(self.yaml_config.get('actions_success')) is dict:
            self._loadActions(self.actions_success, self.yaml_config.get('actions_success'))
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
        self.numberOfProvidersFailed = 0
        i = 0
        for provider in self.providers:
            try:
                # Collect the metric's value from the provider
                value = provider.process()
                getLogger(__name__).debug('Task "' + self.name + '": used task provider "' + self.provider_names[i] + '" to retrieve the value and got ' + str(value))
            except:
                getLogger(__name__).error('Provider "' + self.provider_names[i] + '" raised an error while collecting value for task "' + self.name + '". Not able to process this task.', exc_info=True)
            else:
                self._is_condition_conform(value, provider, i)
                if i == self.numberOfProviders - 1:
                    # Check if the value obtained from the provider is conform to the condition defined in the task config
                    if self.numberOfProvidersFailed == self.numberOfProviders:
                        if self._remaining_retries > 0:
                            if self._remaining_retries == self.retries:
                                # Update task period to period_retry in scheduler
                                self._updateTaskPeriod(self.period_retry)
                            # The task failed, but we retry as many times as specified in task configuration (retries parameter) before performing the action(s)
                            getLogger(__name__).info('Task "' + self.name + '" failed, but retry again the task ' + str(self._remaining_retries) + ' times before performing the action(s)')
                            self._remaining_retries -= 1 # Condition is not conform, decrement the counter of remaining retries
                        elif self._task_failed:
                            # If the task already failed previously, actions have already been treated (to not process again the actions)
                            getLogger(__name__).info('Task "' + self.name + '" still fails. Actions have already been processed (do not process again the actions)')
                        else:
                            # Task is not conform, execute the action(s)
                            self._task_failed = True
                            # Update task period to period_failed in scheduler
                            self._updateTaskPeriod(self.period_failed)
                            getLogger(__name__).warning('Task "' + self.name + '" just failed, process the actions_failed')
                            log_message = "when the task failed"
                            self._makeAction(self.actions_failed, log_message, False, self.provider_conditions, self.provider_thresholds, self.provider_values)
                                
                    else: # Task is conform
                        if self._remaining_retries != self.retries:
                            getLogger(__name__).debug('Set back the remaining retries_counter (' + str(self._remaining_retries) + ') to the required retries number (' + str(self.retries) + ') for task "' + self.name + '".')
                            self._remaining_retries = self.retries
                            # Update task period from period_retry to period_success in scheduler
                            self._updateTaskPeriod(self.period_success)
                        elif self._task_failed:
                            self._task_failed = False
                            # Update task period from period_failed to period_success in scheduler
                            self._updateTaskPeriod(self.period_success)
                            getLogger(__name__).info('Task "' + self.name + '" is back to normal, process the actions_success')
                            log_message = "when the task is back to normal"
                            self._makeAction(self.actions_success, log_message, True, self.provider_conditions, self.provider_thresholds, self.provider_values)
                        else:
                            getLogger(__name__).debug('Task "' + self.name + '" is still normal.')
            i = i + 1
            
    def disableTask(self):
        if self._task_enabled:
            getLogger(__name__).debug('Disable task "' + self.name + '".')
            self._task_enabled = False
            return True
        else:
            getLogger(__name__).warning('Tried to disable task "' + self.name + '" but it is already disabled.')
            return False
            
    def enableTask(self):
        if not self._task_enabled:
            getLogger(__name__).debug('Enable task "' + self.name + '".')
            self._task_enabled = True
            return True
        else:
            getLogger(__name__).warning('Tried to enable task "' + self.name + '" but it is already enabled.')
            return False
            
    def isEnabled(self):
        return self._task_enabled
            
    def isSuccess(self):
        return not self._task_failed
                    
    def updateTaskPeriod(self, new_period):
        if new_period != self.period:
            getLogger(__name__).debug('Update task period from ' + str(self.period) + ' to ' + str(new_period) + ' for task ' + self.name)
            self.period = new_period
            return True
        else:
            getLogger(__name__).warning('Tried to update task "' + self.name + '" to period ' + str(new_period) + ' but period is already ' + str(self.period) + '.')
            return False
            
    def toDict(self):
        return {
                'name': self.name,
                'is_enabled': self._task_enabled,
                'period': self.period,
                'retries': self.retries,
                'remaining_retries': self._remaining_retries,
                'is_failed': self._task_failed
                }
            
    def toYamlDict(self):
        return {
                self.name: self.yaml_config
                }
            
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
    def _loadActions(self, actions_loaded, actions):
        for action_name, action_options in actions.iteritems():
            a = ActionsManager.getActionClass(action_name)
            actions_loaded.append(a(action_options))

    def _loadProviders(self, providers_loaded, providers):
        for provider in providers:
            for provider_name, provider_options in provider.iteritems():
                self.provider_names.append(provider_name)
                condition = provider_options.get('condition')
                if condition is None:
                    raise ValueError('Mandatory parameter condition is not provided to task "' + self.name + '"')
                if not _operator_dict.has_key(condition):
                    raise ValueError('Parameter condition "' + condition + '" provided to task "' + self.name + '" is not allowed. Allowed conditions are: ' + str(_operator_dict.keys()))
                self.provider_conditions.append(condition)
                threshold = provider_options.get('threshold')
                if threshold is None:
                    raise ValueError('Mandatory parameter threshold is not provided to task "' + self.name + '"')
                self.provider_thresholds.append(threshold)
                p = ProvidersManager.getProviderClass(provider_name)
                providers_loaded.append(p(provider_options.get('provider_options')))
                
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

    def _is_condition_conform(self, value, provider, i):
        if (i == 0):
            self.provider_values = []
        condition = self.provider_conditions[i]
        threshold = self.provider_thresholds[i]
        self.provider_values.append(value)
        log_msg = 'Task "' + self.name + '": provider ' + self.provider_names[i] + ' returned ' + str(value) + ', expected: ' + condition + ' ' + str(threshold)
        if _operator_dict[condition](value, threshold):
            if (self.numberOfProvidersFailed > 0):
                self.numberOfProvidersFailed = self.numberOfProvidersFailed - 1
            getLogger(__name__).debug(log_msg)
        else:
            self.numberOfProvidersFailed = self.numberOfProvidersFailed + 1
            getLogger(__name__).warning(log_msg)
                    
    def _updateTaskPeriod(self, new_period):
        if new_period != self.period:
            self._nw_task_manager.updateTaskPeriod(self.name, new_period)
        else:
            getLogger(__name__).warning('Tried to update task "' + self.name + '" to period ' + str(new_period) + ' but period is already ' + str(self.period) + '.')