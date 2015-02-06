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

import os, sys, time
from logging import getLogger

from nw.core.Task import Task
from nw.core.NwConfiguration import getNwConfiguration
from nw.core.Scheduler import Scheduler
from nw.core.Utils import isYamlFile, loadYamlFile

class TaskManager:
    """
    Constructor
    """
    def __init__(self):
        self.tasks = {}
        self._scheduler = None
        
    """
    Public methods
    """
    def start(self):
        # Load tasks from the config files located in the config task folder
        if not self.tasks:
            self._loadTasks()
            self._scheduleTasks()
        self._scheduler.start()
        getLogger(__name__).info('TaskManager started')
        
    def reload(self):
        getLogger(__name__).info('Reloading TaskManager...')
        if self._scheduler:
            getLogger(__name__).debug('Clean current jobs from scheduler')
            self._scheduler.stop(wait=False)
            self._scheduler.removeAllJobs()
            getLogger(__name__).debug('Clear tasks')
            self.tasks.clear()
        self.start()
        getLogger(__name__).info('TaskManager reloaded')
    
    def stop(self):
        # Stop the scheduler
        if self._scheduler != None:
            self._scheduler.stop()
            getLogger(__name__).info('TaskManager stopped')
            

    def getTasks(self):
        return self.tasks
    
    def getTask(self, task_name):
        return self.tasks.get(task_name, None)
                
    
    def pauseTask(self, task_name):
        task = self.tasks.get(task_name, None)
        if task:
            # Update _task_enabled value in Task object
            task_updated = task.disableTask()
            if task_updated:
                # Pause the task in scheduler
                getLogger(__name__).info('Pause task "' + task.name)
                self._scheduler.pauseJob(task.name)
                return True
            else:
                getLogger(__name__).warning('Not able to pause task "' + task.name)
                return False
        else:
            getLogger(__name__).warning('Not able to pause task "' + task_name + '" , task is not found.')
            return False
    
    def resumeTask(self, task_name):
        task = self.tasks.get(task_name, None)
        if task:
            # Update _task_enabled value in Task object
            task_updated = task.enableTask()
            if task_updated:
                # Resume the task in scheduler
                getLogger(__name__).info('Resume task "' + task.name)
                self._scheduler.resumeJob(task.name)
                return True
            else:
                getLogger(__name__).warning('Not able to resume task "' + task.name)
                return False
        else:
            getLogger(__name__).warning('Not able to resume task "' + task_name + '" , task is not found.')
            return False
    
    def updateTaskPeriod(self, task_name, new_period):
        task = self.tasks.get(task_name, None)
        if task:
            # Update task period value in Task object
            task_updated = task.updateTaskPeriod(new_period)
            if task_updated:
                # Change the task periodicity in scheduler
                getLogger(__name__).info('Reschedule task "' + task.name + '" to period ' + task.period)
                # Update scheduler job so that it redefines periodicity of calls to task.run for task task.name
                self._scheduler.rescheduleJob(task.period, task.name)
                return True
            else:
                getLogger(__name__).warning('Not able to reschedule task "' + task.name + '" to period ' + new_period)
                return False
        else:
            getLogger(__name__).warning('Not able to reschedule task "' + task_name + '" to period ' + new_period + ', task is not found.')
            return False
            
    
    """
    Private methods
    """ 
    def _loadTasks(self):
        getLogger(__name__).debug('Loading tasks...')
        tasks_location = getNwConfiguration().tasks_location
        
        tasks_files = []
        try:
            for f in os.listdir(tasks_location):
                if os.path.isfile(os.path.join(tasks_location,f)) and isYamlFile(f):
                    tasks_files.append(f)
        except Exception, e:
            getLogger(__name__).critical('The directory ' + tasks_location + ' is not reachable', exc_info=True)
            exit(-1)
        
        getLogger(__name__).debug('List of task config files to load: ' + str(tasks_files))
        # Load all the tasks' config files
        for task_file in tasks_files:
            try:
                getLogger(__name__).info('Load task config file from ' + task_file)
                config = loadYamlFile(os.path.join(tasks_location,task_file))
            except Exception, e:
                getLogger(__name__).critical('Could not read task config file from ' + task_file + '. Reason is: ' + e.message, exc_info=True)
                exit(-1)
                
            # Instantiate a Task for every task in the current task config file
            for task_name, task in config.iteritems():
                getLogger(__name__).debug('Load task "' + task_name + '"')
                try:
                    t = Task(nw_task_manager = self,
                             name = task_name,
                             period_success = task.get('period_success'),
                             period_retry = task.get('period_retry'),
                             period_failed = task.get('period_failed'),
                             retries = task.get('retries'), 
                             providers = task.get('providers'),
                             actions_failed = task.get('actions_failed'),
                             actions_success = task.get('actions_success'))
                    
                    if self.tasks.has_key(t.name)   :
                        getLogger(__name__).warning('A task named "' + task_name + '" has already been loaded and is overwritten by the task from task config file ' + task_file)
                    self.tasks[t.name] = t
                # TODO: add a better error management (specific errors for invalid configuration, missing required parameters, provider/action initialization problem,...)
                except Exception, e:
                    # TBD: Exit program with critical error or execute the successfully loaded tasks anyway?
                    getLogger(__name__).critical('Could not load task "' + task_name + '" from task config file ' + task_file + '. Reason is: ' + str(e.message), exc_info=True)
                    sys.exit(2)
        getLogger(__name__).debug('Tasks loaded')
                        
    def _scheduleTasks(self):
        getLogger(__name__).debug('Scheduling tasks...')
        if not self._scheduler:
            self._scheduler = Scheduler()
        for key, task in self.tasks.iteritems():
            getLogger(__name__).info('Schedule task "' + key + '"')
            # Add job to the scheduler so that it calls task.run every task.period
            self._scheduler.addJob(task.period, task.run, task.name)
            time.sleep(0.5)
        getLogger(__name__).debug('Tasks scheduled')