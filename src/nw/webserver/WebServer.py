from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, RedirectHandler, Application, url

import os
import uimodules
from logging import getLogger
from nw.core import TaskManager
from nw.core import NwConfiguration
        
class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html", 
                    Tasks = TaskManager.getTasks())

class StatusHandler(RequestHandler):
    def get(self):
        self.render("status.html", 
                    Tasks = TaskManager.getTasks())

class TaskHandler(RequestHandler):
    def get(self):
        task_name = self.get_argument('task_name')
        getLogger(__name__).info('Get task "{}"'.format(task_name))
        self.render("task.html", 
                    Task = TaskManager.getTasks().get(task_name))
    
def make_app():
    return Application(
        handlers = [
            url(r"/", RedirectHandler,dict(url=r"/index.html")),
            url(r"/index.html", MainHandler),
            url(r"/status.html", StatusHandler),
            url(r"/task.html", TaskHandler),
        ],
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "assets"),
        ui_modules = uimodules,
        debug=NwConfiguration.getNwConfiguration().webserver_debug
    )

def start():
    getLogger(__name__).info("Start Night Watch's WebServer")
    application = make_app()
    application.listen(NwConfiguration.getNwConfiguration().webserver_port)
    IOLoop.instance().start()