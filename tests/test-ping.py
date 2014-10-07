#!/usr/bin/env python2.7
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

from nw.providers.Ping import Ping
from nw.core.NwConfiguration import getNwConfiguration
from nw.core import Log


# Read the Night Watch main config file from /etc/night-watch/night-watch.yml
config_file = '/etc/night-watch/night-watch.yml'

# Load the NW config file (required so that the Provider can load its config file)
config = getNwConfiguration()
config.read(config_file)
# Reconfigure the logger now that we loaded the logging config from NW config file
Log.reconfigure(config.logging)

#===============================================================================
# Test returned code
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'count': 5,
          'timeout': 15
         }
# call ping provider
pingProvider = Ping(config)
ping_status = pingProvider.process()
print "Test returned code: " + str(ping_status)

#===============================================================================
# Test ping response
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'ping_response',
          'count': 3,
          'timeout': 5
         }
# call ping provider
pingProvider = Ping(config)
ping_response = pingProvider.process()
print "Test ping response: "
print ping_response

#===============================================================================
# Test nb packets transmitted
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'pkt_transmitted',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
pkt_transmitted = pingProvider.process()
print "Test nb packets transmitted: " + str(pkt_transmitted)

#===============================================================================
# Test nb packets received
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'pkt_received',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
pkt_received = pingProvider.process()
print "Test nb packets received: " + str(pkt_received)

#===============================================================================
# Test nb packets loss
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'pkt_loss',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
pkt_loss = pingProvider.process()
print "Test packets loss rate: " + str(pkt_loss)

#===============================================================================
# Test ping average response time
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'ping_avg',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
ping_avg = pingProvider.process()
print "Test ping average response time: " + str(ping_avg)

#===============================================================================
# Test ping min response time
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'ping_min',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
ping_min = pingProvider.process()
print "Test ping min response time: " + str(ping_min)

#===============================================================================
# Test ping max response time
#===============================================================================
config = {
          'ping_addr': 'www.google.com',
          'requested_data': 'ping_max',
          'count': 3
         }
# call ping provider
pingProvider = Ping(config)
ping_max = pingProvider.process()
print "Test ping max response time: " + str(ping_max)
