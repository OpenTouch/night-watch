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


    def start(self):
        self.scheduler.start()
        getLogger(__name__).info('Start scheduler')


    def stop(self, wait=True):
        self.scheduler.shutdown(wait)
        getLogger(__name__).info('Stop scheduler')
        

    def addJob(self, policy, job_function, job_name):
        # Check that a job with the same name has not already be registered
        if self.jobs.has_key(job_name) and self.jobs.get(job_name) != None:
            raise Exception ('A job named "{}" has already been scheduled'.format(job_name))
        # Get the period trigger to use
        trigger = self._getTrigger(policy)
        # Add the job to the scheduler
        j = self.scheduler.add_job(job_function, name = job_name, max_instances = 1, trigger=trigger)
        getLogger(__name__).debug('Job "{}" has been added to scheduler, it has the id {}. It is scheduled every {}'.format(job_name, j.id, policy))
        # Store job if so that we can update it if needed
        self.jobs[job_name] = j.id


    def rescheduleJob(self, policy, job_name):
        # Check that the job with job_name well exist
        if not(self.jobs.has_key(job_name) or not(self.jobs.get(job_name))):
            raise Exception ('Job named "{}" can not be rescheduled because it is not registered in scheduler'.format(job_name))
        # Get the period trigger to use
        trigger = self._getTrigger(policy)
        # Reschedule the job with the new trigger
        getLogger(__name__).debug('Reschedule job "{}" having id {}'.format(job_name, self.jobs.get(job_name)))
        self.scheduler.reschedule_job(self.jobs.get(job_name), trigger=trigger)


    def pauseJob(self, job_name):
        # Check that the job with job_name well exist
        if not(self.jobs.has_key(job_name) or not(self.jobs.get(job_name))):
            raise Exception ('Job named "{}" can not be paused because it is not registered in scheduler'.format(job_name))
        getLogger(__name__).debug('Pause job "{}" having id {}'.format(job_name, self.jobs.get(job_name)))
        self.scheduler.pause_job(self.jobs.get(job_name))


    def resumeJob(self, job_name):
        # Check that the job with job_name well exist
        if not(self.jobs.has_key(job_name) or not(self.jobs.get(job_name))):
            raise Exception ('Job named "{}" can not be resumed because it is not registered in scheduler'.format(job_name))
        getLogger(__name__).debug('Resume job "{}" having id {}'.format(job_name, self.jobs.get(job_name)))
        self.scheduler.resume_job(self.jobs.get(job_name))


    def removeJob(self, job_name, keepJobEntry=False):
        # Check that the job with job_name well exist
        if not(self.jobs.has_key(job_name) or not(self.jobs.get(job_name))):
            raise Exception ('Job named "{}" can not be removed because it is not registered in scheduler'.format(job_name))
        getLogger(__name__).debug('Remove job "{}" from scheduler'.format(job_name))
        self.scheduler.remove_job(self.jobs.get(job_name))
        if not keepJobEntry:
            self.jobs.pop(job_name)
        
        
    def removeAllJobs(self):
        getLogger(__name__).debug('Remove all jobs from scheduler')
        for job_name in self.jobs.iterkeys():
            self.removeJob(job_name, True)
            self.jobs[job_name]=None


    def _getTrigger(self, policy):
        comp = re.compile("^([0-9]*)([smhd])?$")
        match = comp.match(policy)
        policy = match.groups()
        if (policy[0] == '' or policy[0] == None):
            raise Exception ("The periodicity of your task is not well defined.")
        else:
            period = int(policy[0])
        return IntervalTrigger(seconds=period)
