# Copyright (c) 2015 Alcatel-Lucent Enterprise
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
from tornado.web import RequestHandler


class MainHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        
    def get(self):
        self.render("index.html", 
                    Tasks = self._nw_task_manager.getTasks())

class StatusHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        
    def get(self):
        self.render("status.html", 
                    Tasks = self._nw_task_manager.getTasks())

class TaskHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        
    def get(self):
        task_name = self.get_argument('task_name')
        getLogger(__name__).info('Get task "{}"'.format(task_name))
        self.render("task.html", 
                    Task = self._nw_task_manager.getTasks().get(task_name))