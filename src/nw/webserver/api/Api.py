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
import json
from tornado.web import RequestHandler


class TasksHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager

    def get(self, task_name=None, action=None):
        getLogger(__name__).info('Received request {method} {path}'.format(method=self.request.method, path=self.request.path))
        if task_name:
            task = self._nw_task_manager.getTask(task_name)
            if task:
                self.write(json.dumps(task.toDict()))
            else:
                self.set_status(404)
                self.write(json.dumps({}))
        else:
            tasks = []
            for task_name, task in self._nw_task_manager.getTasks().iteritems():
                tasks.append(task.toDict())
            self.write(json.dumps(tasks))