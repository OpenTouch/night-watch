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

from nw.core.NwExceptions import TaskNotFound, TaskConfigInvalid, ProviderConfigInvalid, ActionConfigInvalid


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
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))

class TasksHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        getLogger(__name__).info('Received request {method} {path}'.format(method=self.request.method, path=self.request.path))

    def get(self):
        tasks = []
        for task in self._nw_task_manager.getTasks().itervalues():
            tasks.append(task.toDict())
        self.write(json.dumps(tasks))
            
    def put(self, action):
        try:
            # TODO: try/except around actions and return list success/failed
            data = json.loads(self.request.body.decode('utf-8'))
            if action == 'pause':
                for task in data:
                    self._nw_task_manager.pauseTask(task.get('name'))
            elif action == 'resume':
                for task in data:
                    self._nw_task_manager.resumeTask(task.get('name'))
            elif action == 'reload':
                self._nw_task_manager.reloadTask(task.get('name'))
            else:
                self.set_status(501)
                self.write(json.dumps({"error_msg":"Action {} is not allowed. Allowed actions: pause | resume | reload".format(action)}))
                
            self.write(json.dumps({'status':'success'}))
                
        except Exception, e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))
            
            
class TaskHandler(RequestHandler):
    def initialize(self, nw_task_manager):
        self._nw_task_manager = nw_task_manager
        getLogger(__name__).info('Received request {method} {path}'.format(method=self.request.method, path=self.request.path))

    def set_default_headers(self):
        self.set_header('server', 'Night-Watch')
        
    def get(self, task_name, action=None):
        try:
            task = self._nw_task_manager.getTask(task_name)
            self.write(json.dumps(task.toDict()))
        except TaskNotFound as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(404)
            self.write(json.dumps({"error_msg":e.message}))
        except Exception as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))
    
    def post(self):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            filename = data["filename"]
            task_config = data["tasks"]
            tasks_added = self._nw_task_manager.addTasks(task_config, filename)
            self.write(json.dumps([task.toDict() for task in tasks_added]))
        except (TaskConfigInvalid, ProviderConfigInvalid, ActionConfigInvalid) as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(501)
            self.write(json.dumps({"error_msg":e.message}))
        except Exception as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))
            
    def put(self, task_name, action):
        try:
            if action == 'pause':
                self._nw_task_manager.pauseTask(task_name)
            elif action == 'resume':
                self._nw_task_manager.resumeTask(task_name)
            elif action == 'reload':
                self._nw_task_manager.reloadTask(task_name)
            else:
                self.set_status(501)
                self.write(json.dumps({"error_msg":"Action {} is not allowed. Allowed actions: pause | resume | reload".format(action)}))
            
            self.write(json.dumps(self._nw_task_manager.getTask(task_name).toDict()))
            
        except TaskNotFound as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(404)
            self.write(json.dumps({"error_msg":e.message}))
        except Exception as e:
            getLogger(__name__).error('Error while handling {method} {path}: {error}'.format(method=self.request.method, path=self.request.path, error=e.message), exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error_msg":e.message}))