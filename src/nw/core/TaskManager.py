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
from nw.core.TaskLoader import TaskLoader
from nw.core.Scheduler import Scheduler
from nw.core import ActionsManager, ProvidersManager
from nw.core.NwExceptions import TaskFileIOError, TaskNotFound, TaskFileInvalid

class TaskManager:
    """
    Constructor
    """
    def __init__(self):
        self.tasks = {}
        self._task_loader = TaskLoader()
        self._scheduler = Scheduler()
        self._started = False
        self._reloading = False
        
    """
    Public methods
    """
    def start(self):
        if self.isRunning():
            raise Exception ("TaskManager is already running")
        # Load tasks from the config files if not already loaded
        self._init()
        self._scheduler.start()
        self._started = True
        getLogger(__name__).info('TaskManager started')
        
    def reload(self):
        getLogger(__name__).info('Reloading TaskManager...')
        if not self.isRunning():
            raise Exception ("TaskManager is not running, can't reload")
        if self.isReloading():
            raise Exception ("TaskManager is already reloading...")
        # Reload TaskManager
        self._reloading = True
        if self._scheduler:
            self._scheduler.removeAllJobs()
        self.tasks.clear()
        ProvidersManager.clearProviderConfig()
        ActionsManager.clearActionConfig()
        self._init()
        self._reloading = False
        getLogger(__name__).info('TaskManager reloaded')
    
    def stop(self, wait=True):
        if self._scheduler == None:
            raise Exception ("Scheduler is not defined, can't stop TaskManager")
        if not self.isRunning():
            raise Exception ("TaskManager is already stopped")
        if self.isReloading():
            raise Exception ("TaskManager is reloading, can't stop during reload")
        # Stop the scheduler
        self._scheduler.stop(wait)
        self._started = False
        getLogger(__name__).info('TaskManager stopped')
            
    def isRunning(self):
        return self._started
            
    def isReloading(self):
        return self._reloading
    

    def getTasks(self):
        return self.tasks
    
    def getTask(self, task_name):
        return self.tasks.get(task_name, None)
                
    
    def pauseTask(self, task_name):
        task = self.tasks.get(task_name, None)
        if not task:
            getLogger(__name__).warning('Not able to pause task "{}", task is not found.'.format(task_name))
            raise Exception ('Not able to pause task "{}", task is not found.'.format(task_name))
        # Update _task_enabled value in Task object
        task_updated = task.disableTask()
        if task_updated:
            # Pause the task in scheduler
            getLogger(__name__).info('Pause task "{}"'.format(task.name))
            self._scheduler.pauseJob(task.name)
        else:
            getLogger(__name__).warning('Not able to pause task "{}"'.format(task.name))
            raise Exception ('Not able to pause task "' + task.name)
    
    def resumeTask(self, task_name):
        task = self.tasks.get(task_name, None)
        if not task:
            getLogger(__name__).warning('Not able to resume task "{}", task is not found.'.format(task_name))
            raise Exception ('Not able to resume task "{}", task is not found.'.format(task_name))
        # Update _task_enabled value in Task object
        task_updated = task.enableTask()
        if task_updated:
            # Resume the task in scheduler
            getLogger(__name__).info('Resume task "{}"'.format(task.name))
            self._scheduler.resumeJob(task.name)
        else:
            getLogger(__name__).warning('Not able to resume "{}"'.format(task.name))
            raise Exception ('Not able to resume "{}"'.format(task.name))
    
    def updateTaskPeriod(self, task_name, new_period):
        task = self.tasks.get(task_name, None)
        if not task:
            getLogger(__name__).warning('Not able to reschedule task "{}", task is not found.'.format(task_name))
            raise Exception ('Not able to reschedule task "{}", task is not found.'.format(task_name))
        # Update task period value in Task object
        task_updated = task.updateTaskPeriod(new_period)
        if task_updated:
            # Change the task periodicity in scheduler
            getLogger(__name__).info('Reschedule task "' + task.name + '" to period ' + str(task.period))
            # Update scheduler job so that it redefines periodicity of calls to task.run for task task.name
            self._scheduler.rescheduleJob(task.period, task.name)
        else:
            getLogger(__name__).warning('Not able to reschedule task "' + task.name + '" to period ' + str(new_period))
            raise Exception ('Not able to reschedule task "' + task.name + '" to period ' + str(new_period))
            
    
    """
    Private methods
    """     
    def _init(self):
        # Load tasks from the config files located in the config task folder
        if not self.tasks:
            self._loadAllTasks()
            self._scheduleTasks()
        getLogger(__name__).info('Tasks loaded')
        
    def _loadAllTasks(self):
        getLogger(__name__).debug('Loading tasks...')
        tasks_config_files = self._task_loader.loadAllTasks()
        # Instantiate a Task for every task in the current task config file
        for tasks_filename, tasks_config in tasks_config_files.iteritems():
            for task_name, task_config in tasks_config.iteritems():
                getLogger(__name__).debug('Instantiate task "{}"'.format(task_name))
                t = Task(nw_task_manager = self,
                         name = task_name,
                         config = task_config,
                         from_filename = tasks_filename)
                if self.tasks.has_key(t.name)   :
                    getLogger(__name__).warning('A task named "{}" has already been loaded and is overwritten by the task from task config file '.format(task_name, tasks_filename))
                self.tasks[t.name] = t
        getLogger(__name__).debug('Tasks loaded')
                        
    def _scheduleTasks(self):
        getLogger(__name__).debug('Scheduling tasks...')
        for key, task in self.tasks.iteritems():
            getLogger(__name__).info('Schedule task "' + key + '"')
            # Add job to the scheduler so that it calls task.run every task.period
            self._scheduler.addJob(task.period, task.run, task.name)
            time.sleep(0.5)
        getLogger(__name__).debug('Tasks scheduled')