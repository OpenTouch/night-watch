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


class NightWatchHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        self.set_header('Content-Type', 'application/json'); 
        getLogger(__name__).info('Received request {method} {path}'.format(method=self.request.method, path=self.request.path))

    def get(self, action):
        if action == 'status':
            if self._nw_task_manager.isReloading():
                status = "Reloading" 
            elif self._nw_task_manager.isRunning():
                status = "Running"
            else:
                status = "Stopped"
            self.write(json.dumps({'status':status}))
        else:
            self.set_status(501)
            self.write(json.dumps({"error_msg":"Action {} is not allowed. Allowed actions: status".format(action)}))

    def put(self, action):
        try:
            if action == 'pause':
                self._nw_task_manager.stop()
                return self.get('status')
            elif action == 'resume':
                self._nw_task_manager.start()
                return self.get('status')
            elif action == 'reload':
                self._nw_task_manager.reload()
                self.write(json.dumps({'status':'reloaded'}))
            else:
                self.set_status(501)
                self.write(json.dumps({"error_msg":"Action {} is not allowed. Allowed actions: pause | resume | reload".format(action)}))
        except Exception, e:
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))

class TasksHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        getLogger(__name__).info('Received request {method} {path}'.format(method=self.request.method, path=self.request.path))

    def get(self, task_name=None, action=None):
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
            
    def put(self, task_name, action):
        try:
            if action == 'pause':
                self._nw_task_manager.pauseTask(task_name)
                self.write(json.dumps(self._nw_task_manager.getTask(task_name).toDict()))
            elif action == 'resume':
                self._nw_task_manager.resumeTask(task_name)
                self.write(json.dumps(self._nw_task_manager.getTask(task_name).toDict()))
            #TODO: implement reload Task
            #elif action == 'reload':
            #    self._nw_task_manager.reloadTask(task_name)
            #    self.write(json.dumps(self._nw_task_manager.getTask(task_name).toDict()))
            else:
                self.set_status(501)
                self.write(json.dumps({"error_msg":"Action {} is not allowed. Allowed actions: pause | resume | reload".format(action)}))
        except Exception, e:
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))