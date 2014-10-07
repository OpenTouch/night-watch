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

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import re

class Scheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler({
            'apscheduler.job_defaults.coalesce': 'true',
        })

    def addJob(self, policy, task):
        comp = re.compile("^([0-9]*)([smhd])?$")
        match = comp.match(policy)
        policy = match.groups()
        if (policy[0] == '' or policy[0] == None):
            raise Exception ("The periodicity of your task is not defined.")
        else:
            period = int(policy[0])

        @self.scheduler.scheduled_job('interval', seconds=period)
        def timed_job():
            task()

    def start(self):
        self.scheduler.start()
