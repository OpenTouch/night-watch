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
from nw.core.Utils import loadYamlFile
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
                return loadYamlFile(os.path.join(self.tasks_location, tasks_filename))
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
        
        
    def write(self, tasks_config, task_filename):
        # TODO: implement writers
        pass
    
    """
    Private methods
    """
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
    
    def _checkTasksFile(self, filename):
        if not os.path.isfile(os.path.join(self.tasks_location,filename)):
            raise TaskFileIOError("Task file {} does not exist in folder {}, or does not have appropriate rights".format(filename, self.tasks_location))
        return True