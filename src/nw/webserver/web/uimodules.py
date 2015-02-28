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

from tornado.web import UIModule

class TasksTable(UIModule):
    def render(self, tasks):
        return self.render_string(
            "uitemplates/tasks-table.html", tasks=tasks)

class TaskTableItem(UIModule):
    def render(self, task):
        return self.render_string(
            "uitemplates/task-table-item.html", task=task)

class TaskList(UIModule):
    def render(self, task, show_config = False):
        return self.render_string(
            "uitemplates/task-list.html", task=task, show_config=show_config)