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

import os, sys
from logging import getLogger

from nw.core.Task import Task
from nw.core.NwConfiguration import getNwConfiguration
from nw.core.Scheduler import Scheduler
from nw.core.Utils import isYamlFile, loadYamlFile

tasks = {}

def start():
    # Load tasks from the config files located in the config task folder
    _loadTasks()
    scheduler = Scheduler()
    for key, task in tasks.iteritems():
        getLogger(__name__).info('Schedule task "' + key + '"')
        # Add job to the scheduler so that it calls task.tun every task.period
        scheduler.addJob(task.period, task.run)
    scheduler.start()
        
                
def _loadTasks():
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
                    # TODO: add security checks to verify that mandatory task fields are provided
                    t = Task(name = task_name,
                        period = task.get('period'),
                        retries = task.get('retries'), 
                        providers = task.get('providers'), 
                        #provider_options = task.get('provider_options') or {}, 
                        #condition = task.get('condition'), 
                        #threshold = task.get('threshold'), 
                        actions_failed = task.get('actions_failed'),
                        actions_success = task.get('actions_success'))
                    
                    if tasks.has_key(t.name)   :
                        getLogger(__name__).warning('A task named "' + task_name + '" has already been loaded and is overwritten by the task from task config file ' + task_file)
                    tasks[t.name] = t
                # TODO: add a better error management (specific errors for invalid configuration, missing required parameters, provider/action initialization problem,...)
                except Exception, e:
                    # TBD: Exit program with critical error or execute the successfully loaded tasks anyway?
                    print "Error occurred during the Night Watch starting..."
                    getLogger(__name__).critical('Could not load task "' + task_name + '" from task config file ' + task_file + '. Reason is: ' + e.message, exc_info=True)
                    sys.exit(2)
