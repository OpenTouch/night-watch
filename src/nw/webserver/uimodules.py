from tornado.web import UIModule

class Task(UIModule):
    def render(self, task, show_config = False):
        return self.render_string(
            "module-task.html", task=task, show_config=show_config)