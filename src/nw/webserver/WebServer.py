from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, RedirectHandler, Application, url

import os
import uimodules
from logging import getLogger
from nw.core import TaskManager
        
class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html", 
                    Tasks = TaskManager.getTasks())

class StatusHandler(RequestHandler):
    def get(self):
        self.render("status.html", 
                    Tasks = TaskManager.getTasks())

class TaskHandler(RequestHandler):
    def get(self, task_name):
        self.render("task.html", 
                    Task = TaskManager.getTasks().get(task_name))
    
def make_app():
    return Application(
        handlers = [
            url(r"/", RedirectHandler,dict(url=r"/index.html")),
            url(r"/index.html", MainHandler),
            url(r"/status.html", StatusHandler),
            url(r"/task.html?name=([a-zA-Z\\s\\+]+)", TaskHandler),
        ],
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "assets"),
        ui_modules = uimodules,
        compiled_template_cache=False,
        debug=True
    )

def start():
    getLogger(__name__).info("Start Night Watch's WebServer")
    application = make_app()
    application.listen(8888)
    IOLoop.instance().start()