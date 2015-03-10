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

import os
from logging import getLogger

from nw.core.NwConfiguration import getNwConfiguration
from nw.core.Utils import loadYamlFile, writeYamlFile
from nw.core.NwExceptions import TaskNotFound, TaskFileIOError, TaskFileInvalid


class TaskLoader:
    """
    Constructor
    """
    def __init__(self):
        getLogger(__name__).debug('Initializing TaskLoader...')
        self.tasks_location = getNwConfiguration().tasks_location
            
    """
    Public methods
    """
    def loadTaskFile(self, tasks_filename):
        getLogger(__name__).info('Load tasks file {}'.format(tasks_filename))
        if self._checkTasksFile(tasks_filename):
            try:
                return loadYamlFile(self._buildTasksFilePath(tasks_filename))
            except:
                raise TaskFileInvalid("Task file {} is not a valid yaml file".format(tasks_filename))
            
    def loadTaskFromFile(self, tasks_filename, taskname):
        tasks_file = self.loadTaskFile(tasks_filename)
        getLogger(__name__).debug('Load task "{}" from file {}'.format(taskname, tasks_filename))
        if taskname in tasks_file.keys():
            return tasks_file.get(taskname)
        else:
            raise TaskNotFound("Task with name {} not found in file {}".format(taskname, tasks_filename))
        
    def loadAllTasks(self):
        tasks = {}
        tasks_files = self._listTasksFiles()
        # Load all the tasks' config files
        for task_filename in tasks_files:
            tasks[task_filename] = self.loadTaskFile(task_filename)
        return tasks
            
    def addTaskInFile(self, task):
        getLogger(__name__).info('Add task "{}" in file {}'.format(task.name, task.from_yaml_filename))
        try:
            tasks_file = self.loadTaskFile(task.from_yaml_filename)
        except TaskFileIOError:
            # the file does not already exist, it will be created
            tasks_file = {}
        tasks_file[task.name] = task.yaml_config
        self.writeTasksFile(tasks_file, task.from_yaml_filename)
            
    def addTasksInFiles(self, tasks):
        getLogger(__name__).info('Add tasks "{}"'.format([task.name for task in tasks]))
        tasks_files_to_add = self._sortTasksByTasksFilename(tasks)
        for tasks_filename, tasks in tasks_files_to_add.iteritems():
            getLogger(__name__).debug('Add tasks "{}" in file {}'.format([task.name for task in tasks], task.from_yaml_filename))
            try:
                tasks_file = self.loadTaskFile(tasks_filename)
            except TaskFileIOError:
                # the file does not already exist, it will be created
                tasks_file = {}
            for task in tasks:
                tasks_file[task.name] = task.yaml_config
            self.writeTasksFile(tasks_file, tasks_filename)
            
    def updateTaskInFile(self, task):
        getLogger(__name__).info('Update task "{}" in file {}'.format(task.name, task.from_yaml_filename))
        tasks_file = self.loadTaskFile(task.from_yaml_filename)
        tasks_file[task.name] = task.yaml_config
        self.writeTasksFile(tasks_file, task.from_yaml_filename)
            
    def updateTasksInFiles(self, tasks):
        getLogger(__name__).info('Update tasks "{}"'.format([task.name for task in tasks]))
        tasks_files_to_update = self._sortTasksByTasksFilename(tasks)
        for tasks_filename, tasks in tasks_files_to_update.iteritems():
            tasks_file = self.loadTaskFile(tasks_filename)
            for task in tasks:
                tasks_file[task.name] = task.yaml_config
            getLogger(__name__).debug('Overwrite file {} with updated tasks {}'.format(tasks_filename, [task.name for task in tasks]))
            self.writeTasksFile(tasks_file, tasks_filename)
        
    def removeTaskFromFile(self, task):
        getLogger(__name__).info('Delete task "{}" from file {}'.format(task.name, task.from_yaml_filename))
        tasks_file = self.loadTaskFile(task.from_yaml_filename)
        tasks_file.pop(task.name)
        if len(tasks_file) > 0:
            return self.writeTasksFile(tasks_file, task.from_yaml_filename)
        else:
            # If there are no longer tasks in tasks file, delete it
            getLogger(__name__).debug('Tasks file {} has no longer tasks, delete it'.format(task.from_yaml_filename))
            self.deleteTasksFile(task.from_yaml_filename)
        
    def removeTasksFromFiles(self, tasks):
        getLogger(__name__).info('Delete tasks "{}"'.format([task.name for task in tasks]))
        tasks_files_to_update = self._sortTasksByTasksFilename(tasks)
        for tasks_filename, tasks in tasks_files_to_update.iteritems():
            tasks_file = self.loadTaskFile(tasks_filename)
            for task in tasks:
                tasks_file.pop(task.name)
            if len(tasks_file) > 0:
                getLogger(__name__).debug('Overwrite file {} with deleted tasks {}'.format(tasks_filename, [task.name for task in tasks]))
                return self.writeTasksFile(tasks_file, tasks_filename)
            else:
                # If there are no longer tasks in tasks file, delete it
                getLogger(__name__).debug('Tasks file {} has no longer tasks, delete it'.format(tasks_filename))
                self.deleteTasksFile(tasks_filename)
        
    def deleteTasksFile(self, tasks_filename):
        getLogger(__name__).info('Delete tasks file {}'.format(tasks_filename))
        if self._checkTasksFile(tasks_filename):
            os.remove(self._buildTasksFilePath(tasks_filename))
        
    def writeTasksFile(self, tasks_config, task_filename):
        return writeYamlFile(tasks_config, self._buildTasksFilePath(task_filename))
    
    """
    Private methods
    """
    def _buildTasksFilePath(self, tasks_filename):
        return os.path.join(self.tasks_location, tasks_filename)
    
    def _listTasksFiles(self):
        tasks_files = []
        try:
            for f in os.listdir(self.tasks_location):
                tasks_files.append(f)
        except Exception, e:
            getLogger(__name__).error("Can't load tasks files, directory {} is not reachable".format(self.tasks_location), exc_info=True)
            raise TaskFileIOError
        getLogger(__name__).debug('List of tasks files in folder {}: {}'.format(self.tasks_location, tasks_files))
        return tasks_files
    
    def _sortTasksByTasksFilename(self, tasks):
        tasks_files = {}
        for task in tasks:
            if not tasks_files.has_key(task.from_yaml_filename):
                tasks_files[task.from_yaml_filename] = [task]
            else:
                tasks_files.get(task.from_yaml_filename).append(task)
        return tasks_files
    
    def _checkTasksFile(self, filename):
        if not os.path.isfile(self._buildTasksFilePath(filename)):
            raise TaskFileIOError("Task file {} does not exist in folder {}, or does not have appropriate rights".format(filename, self.tasks_location))
        return True