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
import uuid

from nw.core.Task import Task
from nw.core.TaskLoader import TaskLoader
from nw.core.Scheduler import Scheduler
from nw.core import ActionsManager, ProvidersManager
from nw.core.NwExceptions import TaskFileIOError, TaskNotFound, TaskFileInvalid, TaskConfigInvalid

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
        try:
            if self._scheduler:
                self._scheduler.removeAllJobs()
            self.tasks.clear()
            ProvidersManager.clearProviderConfig()
            ActionsManager.clearActionConfig()
            self._init()
            self._reloading = False
            getLogger(__name__).info('TaskManager reloaded')
        except Exception as e:
            getLogger(__name__).error('TaskManager failed to reload, error: {}'.format(e.message), exc_info=True)
            self._reloading = False
            raise
    
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
    
    def getSuccessfulTasks(self):
        return [task for task in self.tasks.itervalues() if task.isSuccess()]
    
    def getEnabledTasks(self):
        return [task for task in self.tasks.itervalues() if task.isEnabled()]
    
    def getTask(self, task_name):
        if self.tasks.has_key(task_name):
            return self.tasks.get(task_name)
        else:
            raise TaskNotFound('Task with "{}" is not found'.format(task_name))
        
    
    """def getTaskFilename(self, task_name):
        return self.getTask(task_name).from_yaml_filename"""
    
    def addTasks(self, tasks_config, task_filename=str(uuid.uuid1())+'.yml'):
        loaded_tasks = self._loadTasksFromDict(tasks_config, task_filename)
        tasks_to_add = []
        tasks_to_update = {}
        for task in loaded_tasks:
            if self.tasks.has_key(task.name):
                getLogger(__name__).warning('A task named "{}" has already exist in file {} and will be overwritten'.format(task.name, task.from_yaml_filename))
                tasks_to_update[task.name] = task.yaml_config
            else:
                self.tasks[task.name] = task
                self._scheduleTask(task)
                tasks_to_add.append(task)
        if tasks_to_add:
            self._task_loader.addTasksInFiles(tasks_to_add)
        if tasks_to_update:
            self.updateTasks(tasks_to_update)
        return [self.getTask(task) for task in tasks_config.keys()]
                
    def updateTasks(self, tasks_config):
        # Make a first loop to check if config is valid (update is only applied if all tasks are valid)
        for task_name, task_config in tasks_config.iteritems():
            if not task_name:
                raise TaskConfigInvalid("Can't update tasks because some task provided tasks_config parameter is invalid: {}".format(task_config))
            if not self.tasks.has_key(task_name):
                raise TaskNotFound('Can\'t update tasks because provided task "{}" is not found. Abort update of all tasks.'.format(task_config.get('name')))
        
        tasks = self._loadTasksFromDict(tasks_config)
        for task in tasks:
            # Remove old task from scheduler
            self._scheduler.removeJob(task.name)
            # Remove the task from TaskManager
            deleted_task = self.tasks.pop(task.name)
            # Delete the task
            del deleted_task
            # Store the new task TaskManager
            self.tasks[task.name] = task
            # Add new task to scheduler
            self._scheduleTask(task)
        # Update the tasks in their config file
        self._task_loader.updateTasksInFiles(tasks)
                
    def deleteTasks(self, tasks_name):
        deleted_tasks = []
        for task_name in tasks_name:
            if self.tasks.has_key(task_name):
                # Remove the task from scheduler
                self._scheduler.removeJob(task_name)
                # Remove the task from TaskManager
                deleted_tasks.append(self.tasks.pop(task_name))
            else:
                getLogger(__name__).warning('Not able to delete task "{}", task is not found.'.format(task_name))
        # Remove the task from Yaml config file
        self._task_loader.removeTasksFromFiles(deleted_tasks)
        for task in task:
            # Delete the task
            del task
    
    def reloadTask(self, task_name):
        getLogger(__name__).info('Reload task "{}"'.format(task_name))
        task = self.getTask(task_name)
        task_config = self._task_loader.loadTaskFromFile(task.from_yaml_filename, task.name)
        loaded_task = self._loadTasksFromDict([task_config],task.from_yaml_filename)[0]
        # Remove the old task from scheduler
        self._scheduler.removeJob(task_name)
        # Remove the old task from TaskManager
        deleted_task = self.tasks.pop(task_name)
        del deleted_task
        # Store the new task in TaskManager
        self.tasks[task.name] = loaded_task
        # Add new task to scheduler
        self._scheduleTask(loaded_task)
    
    def pauseTask(self, task_name):
        getLogger(__name__).info('Pause task "{}"'.format(task_name))
        # Update _task_enabled value in Task object
        task_updated = self.getTask(task_name).disableTask()
        if task_updated:
            # Pause the task in scheduler
            self._scheduler.pauseJob(task_name)
        else:
            getLogger(__name__).warning('Not able to pause task "{}"'.format(task_name))
            raise Exception ('Not able to pause task "{}"'.format(task_name))
    
    def resumeTask(self, task_name):
        getLogger(__name__).warning('Resume task "{}"'.format(task_name))
        # Update _task_enabled value in Task object
        task_updated = self.getTask(task_name).enableTask()
        if task_updated:
            # Resume the task in scheduler
            self._scheduler.resumeJob(task_name)
        else:
            getLogger(__name__).warning('Not able to resume "{}"'.format(task_name))
            raise Exception ('Not able to resume "{}"'.format(task_name))
    
    def updateTaskPeriod(self, task_name, new_period):
        getLogger(__name__).info('Reschedule task "{}" to period {}'.format(task_name, new_period))
        # Update task period value in Task object
        task = self.getTask(task_name)
        task_updated = task.updateTaskPeriod(new_period)
        if task_updated:
            # Update scheduler job so that it redefines periodicity of calls to task.run for task task.name
            self._scheduler.rescheduleJob(task.period, task.name)
        else:
            getLogger(__name__).warning('Not able to reschedule task "{}" to period {}'.format(task.name, new_period))
            raise Exception ('Not able to reschedule task "{}" to period {}'.format(task.name, new_period))
            
    
    """
    Private methods
    """     
    def _init(self):
        # Load tasks from the config files located in the config task folder
        if not self.tasks:
            self._loadAllTasks()
            self._scheduleTasks()
        getLogger(__name__).info('Tasks loaded')
        
    def _loadTasksFromDict(self, tasks_config, tasks_filename):
        getLogger(__name__).debug('Loading tasks...')
        tasks = []
        # Instantiate a Task for every task in the provided tasks_config dictionary
        for task_name, task_config in tasks_config.iteritems():
            getLogger(__name__).debug('Instantiate task "{}"'.format(task_name))
            t = Task(nw_task_manager = self,
                     name = task_name,
                     config = task_config,
                     from_filename = tasks_filename)
            tasks.append(t)
        getLogger(__name__).debug('Tasks loaded')
        return tasks
        
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
                        
    def _scheduleTask(self, task):
        getLogger(__name__).debug('Schedule task "{}"'.format(task.name))
        # Add job to the scheduler so that it calls task.run every task.period
        self._scheduler.addJob(task.period, task.run, task.name)
        time.sleep(0.5)
                        
    def _scheduleTasks(self):
        getLogger(__name__).debug('Scheduling tasks...')
        for task in self.tasks.itervalues():
            self._scheduleTask(task)
        # Mostly for debug
        self._scheduler.print_jobs()
        getLogger(__name__).debug('{} tasks has been added to scheduler'.format(self._scheduler.getNbScheduledJobs()))