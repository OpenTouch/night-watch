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
import nw.core

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
    
    def __init__(self, name, period_success, period_retry, period_failed, retries, providers, actions_failed, actions_success):
        self.name = name
        
        if period_success is None:
            raise ValueError('Mandatory parameter period_success is not provided to task "' + name + '"')
        self.period_success = period_success
        
        if retries is not None and period_retry is None:
            raise ValueError('Mandatory parameter period_retry is not provided to task "' + name + '"')
        self.period_retry = period_retry
        
        if period_failed is None:
            raise ValueError('Mandatory parameter period_failed is not provided to task "' + name + '"')
        self.period_failed = period_failed
        
        # Define the task period to period_success at init
        self.period = period_success
        
        # Number of retries before performing the actions
        if retries is None:
            getLogger(__name__).info('No retries parameter defined for Task "' + self.name + '", do not use retries (action(s) are perform as soon as the task fails)')
            self.retries = 0
        else:
            self.retries = retries
        self._remaining_retries = self.retries
        
        if providers is None:
            raise ValueError('Mandatory parameter providers is not provided to task "' + name + '"')
        self.providers = []
        self.provider_names = []
        self.provider_conditions = []
        self.provider_thresholds = []
        self.provider_values = []
        self._loadProviders(self.providers, providers)
        self.numberOfProvidersFailed = 0
        self.numberOfProviders = len(self.providers)
        getLogger(__name__).info('Number of providers:' + str(self.numberOfProviders))

        self.actions_failed = []
        if actions_failed and type(actions_failed) is dict:
            self._loadActions(self.actions_failed, actions_failed)
        else:
            getLogger(__name__).warning('No action(s) defined for Task "' + self.name + '" if this task failed.')

        self.actions_success = []
        if actions_success and type(actions_success) is dict:
            self._loadActions(self.actions_success, actions_success)
        else:
            getLogger(__name__).warning('No action(s) defined for Task "' + self.name + '" if this task back to normal.')
            
        # Boolean used to know if the task already failed in the previous iteration (allows to perform actions only the first time the issue failed)
        self._task_failed = False

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
        condition = self.provider_conditions[i]
        threshold = self.provider_thresholds[i]
        self.provider_value[i] = value
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
            getLogger(__name__).info('Update task period from ' + self.period + ' to ' + new_period)
            self.period = new_period
            nw.core.TaskManager.getTaskManager().updateTaskPeriod(self)