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

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, RedirectHandler, Application, url

import os
from logging import getLogger
from nw.webserver.web import uimodules
from nw.webserver.web import Web
from nw.webserver.api import Api
from nw.core import NwConfiguration

class Webserver:
    def __init__(self, task_manager):
        self._nw_task_manager = task_manager
        self._tornado_webserver = None
        
    def make_app(self):
        return Application(
            handlers = [
                url(r"/", RedirectHandler,dict(url=r"/index.html")),
                url(r"/index.html", Web.MainHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/status.html", Web.StatusHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/task.html", Web.TaskHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/night-watch/(?P<action>status|pause|resume|reload)", Api.NightWatchHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/tasks", Api.TasksHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/tasks/(?P<action>pause|resume|reload)", Api.TasksHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/task", Api.TaskHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/task/(?P<task_name>[^/]+)", Api.TaskHandler, dict(nw_task_manager=self._nw_task_manager)),
                url(r"/api/v1/task/(?P<task_name>[^/]+)/(?P<action>pause|resume|reload)", Api.TaskHandler, dict(nw_task_manager=self._nw_task_manager)),
            ],
            template_path = os.path.join(os.path.dirname(__file__), "web/templates"),
            static_path = os.path.join(os.path.dirname(__file__), "web/static"),
            ui_modules = uimodules,
            debug=NwConfiguration.getNwConfiguration().webserver_debug
        )

    def start(self):
        getLogger(__name__).debug("Initializing Night Watch's WebServer...")
        application = self.make_app()
        application.listen(NwConfiguration.getNwConfiguration().webserver_port)
        self._tornado_webserver = IOLoop.instance()
        getLogger(__name__).info("Start Night Watch's WebServer")
        self._tornado_webserver.start()

    def stop(self):
        getLogger(__name__).info("Stop Night Watch's WebServer")
        self._tornado_webserver.stop()