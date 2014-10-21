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
from apscheduler.triggers.interval import IntervalTrigger
import re
from logging import getLogger

class Scheduler:
    def __init__(self):
        self.jobs = {}
        self.scheduler = BackgroundScheduler({
            'apscheduler.job_defaults.coalesce': 'true',
        })


    def addJob(self, policy, job_function, job_name):
        # Check that a job with the same name has not already be registered
        if self.jobs.has_key(job_name):
            raise Exception ('A job named "' + job_name + '" has already been scheduled')
        # Get the period trigger to use
        trigger = self._getTrigger(policy)
        # Add the job to the scheduler
        j = self.scheduler.add_job(job_function, name = job_name, max_instances = 1, trigger=trigger)
        getLogger(__name__).debug('Job "' + job_name +'" has been added to scheduler, it has the id ' + j.id + '. It is scheduled every ' + policy)
        # Store job if so that we can update it if needed
        self.jobs[job_name] = j.id


    def rescheduleJob(self, policy, job_name):
        # Check that the job with job_name well exist
        if not(self.jobs.has_key(job_name)):
            raise Exception ('Job named "' + job_name + '" can not be rescheduled because it is not registered in scheduler')
        # Get the period trigger to use
        trigger = self._getTrigger(policy)
        # Reschedule the job with the new trigger
        getLogger(__name__).debug('Reschedule job "' + job_name +'" having id ' + self.jobs.get(job_name))
        self.scheduler.reschedule_job(self.jobs.get(job_name), trigger=trigger)


    def start(self):
        self.scheduler.start()
        getLogger(__name__).info('Start scheduler')


    def stop(self):
        self.scheduler.shutdown()
        getLogger(__name__).info('Stop scheduler')


    def _getTrigger(self, policy):
        comp = re.compile("^([0-9]*)([smhd])?$")
        match = comp.match(policy)
        policy = match.groups()
        if (policy[0] == '' or policy[0] == None):
            raise Exception ("The periodicity of your task is not well defined.")
        else:
            period = int(policy[0])
        return IntervalTrigger(seconds=period)
