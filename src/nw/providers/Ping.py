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

from nw.providers.Provider import Provider

import subprocess
import re
from logging import getLogger

# /!\ Warning: this Provider uses the ping system command and has been designed for Linux (Debian Wheezy).

# List of data the Ping Provider can return (set in Provider's config field 'requested_data').
# If the Provider is configured with another requested_data, an exception is raised.
# If no requested_data is configured for Ping Provider, status is used by default.
_data_available = [
                   'status', # returns the status code (integer) of ping command execution: 0 = success, other = error occurred
                   'ping_response', # returns the whole std output of ping command (string)
                   'pkt_transmitted', # returns the number of packets transmitted (integer) (extracted from stdout of ping command using a regex)
                   'pkt_received', # returns the number of packets received (integer) (extracted from stdout of ping command using a regex)
                   'pkt_loss', # returns the number of packets loss (integer) (extracted from stdout of ping command using a regex)
                   'ping_avg', # returns the average ping time (in ms) (float) (extracted from stdout of ping command using a regex)
                   'ping_min', # returns the min ping time (in ms) (float) (extracted from stdout of ping command using a regex)
                   'ping_max' # returns the max ping time (in ms) (float) (extracted from stdout of ping command using a regex)
                  ]

class Ping(Provider):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by HttpRequest provider
    _mandatory_parameters = [
                        'ping_addr' # IP address or hostname of the machine to ping
                        ]
    
    _optional_parameters = [
                        'requested_data', # (string) Requested data (default is 'status' which returns the status code of ping command execution). See _data_available for available options.
                        'count', # (integer) -c option of ping: Stop after sending (and receiving) count ECHO_RESPONSE packets. If not defined, default value is 1.
                        'timeout' # (integer) -W option of ping: Time to wait for a response, in seconds. The option affects only timeout in absense of any responses, otherwise ping waits for two RTTs.
                        ]
    
    def __init__(self, options):
        Provider.__init__(self, options)
        
        # Build ping command
        self.ping_cmd = "ping"
        # Add -c option
        if not self._config.get('count'):
            getLogger(__name__).info('Option "count" is not provided to provider Ping, use default value (1)')
            self.count = 1
        else:
            self.count = self._config.get('count')
        self.ping_cmd += " -c " + str(self.count)
        
        # Add -W option if requested
        if self._config.get('timeout'):
            self.ping_cmd += " -W " + str(self._config.get('timeout'))
        
        # Add ping address
        self.ping_cmd += " " + self._config.get('ping_addr')
        
        # Load requested data (default is 'status')
        self.requested_data = self._config.get('requested_data') or "status"


    def process(self):
        if (self.requested_data == "status"):
            return self._getPingStatus()
        else:
            # TODO: better management of ping errors
            try:
                ping_data = self._performPing()
            except:
                return None # Ping error
            # Return the requested data
            if (self.requested_data == "ping_response"):
                return ping_data.ping_response
            if (self.requested_data == "pkt_transmitted"):
                return ping_data.pkt_transmitted
            if (self.requested_data == "pkt_received"):
                return ping_data.pkt_received
            elif (self.requested_data == "pkt_loss"):
                return ping_data.pkt_loss
            if (self.requested_data == "ping_avg"):
                return ping_data.ping_avg
            if (self.requested_data == "ping_min"):
                return ping_data.ping_min
            if (self.requested_data == "ping_max"):
                return ping_data.ping_max


    # Simply execute ping command to retrieve the command's returned code
    def _getPingStatus(self):
        getLogger(__name__).debug('Call ping command with the following options: ' + self.ping_cmd)
        returncode = subprocess.call(self.ping_cmd,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True)
        getLogger(__name__).debug('Ping command returned status code: ' + str(returncode))
        return returncode
  
  
    # Execute ping command and returned a PingData object in case of success
    def _performPing(self):
        getLogger(__name__).debug('Call ping command with the following options: ' + self.ping_cmd)
        (output, error) = subprocess.Popen(self.ping_cmd,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=True).communicate()
        if output:
            getLogger(__name__).debug('Ping command returned: ' + output)
            return PingData(output)
        else:
            getLogger(__name__).debug('Ping error: ' + error)
            raise Exception(error)
    
    
    # This function is called by __init__ of the abstract Provider class, it verify during the object initialization if the Provider' configuration is valid.
    def _isConfigValid(self):
        Provider._isConfigValid(self)
        # If requested_data is provided, check if it is managed by Ping provider
        if self._config.get('requested_data') and not (self._config.get('requested_data') in _data_available):
            getLogger(__name__).error('Parameter requested_data "' + self._config.get('requested_data') + '" provided to provider Ping is not allowed. Allowed conditions are: ' + str(_data_available))
            return False
        return True
    
    
class PingData:
    """
    Class extracting ping statistics data using regexps on ping command response.
    /!\ Warning: regexp used to extract information applies on string returned by ping command on Linux (tested on Debian Wheezy).
    Extracted data are:
      - ping_response = the whole output of ping command
      - pkt_transmitted = number of packets transmitted (integer)
      - pkt_received = number of packets received (integer)
      - pkt_loss = packet loss rate in percentage (float)
      - ping_min = ping minimum response time in milliseconds (float)
      - ping_avg = ping average response time in milliseconds (float)
      - ping_max = ping maximum response time in milliseconds (float)
      - ping_stdev = standard deviation of ping response time in milliseconds (float)
    """
    def __init__(self, ping_response):
        if not ping_response:
            raise Exception("Can't create PingData object without ping response data")
        self.ping_response = ping_response
        # Extract packets data from statistics section of Ping response
        result = re.search('(?P<pkt_transmitted>\d)\spackets\stransmitted,\s(?P<pkt_received>\d)?\s?\w*\sreceived,\s(?P<pkt_loss>[\d]*?\.?[\d]*)\%\spacket\sloss', self.ping_response)
        self.pkt_transmitted = int(result.group('pkt_transmitted'))
        self.pkt_received = int(result.group('pkt_received'))
        self.pkt_loss = float(result.group('pkt_loss'))
        # Extract time stats from statistics section of Ping response
        result = re.search('min\/avg\/max\/\w*\s=\s(?P<ping_min>[\d]*\.[\d]*)\/(?P<ping_avg>[\d]*\.[\d]*)\/(?P<ping_max>[\d]*\.[\d]*)\/(?P<ping_stddev>[\d]*\.[\d]*)', self.ping_response)
        self.ping_min = float(result.group('ping_min'))
        self.ping_avg = float(result.group('ping_avg'))
        self.ping_max = float(result.group('ping_max'))
        self.ping_stddev = float(result.group('ping_stddev'))
