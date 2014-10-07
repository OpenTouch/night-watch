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

import requests
from logging import getLogger

# List of data the HttpRequest Provider can return (set in Provider's config field 'requested_data').
# If the Provider is configured with another requested_data, an exception is raised.
# If no requested_data is configured for HttpRequest Provider, status is used by default.
_data_available = [
                   'status', # returns the HTTP status code (integer)
                   'content' # returns the response content (json object is returned if the request response is json, string is returned otherwise)
                  ]

# List of HTTP methods supported by HttpRequest Provider. 
# If the Provider is configured with another method, an exception is raised.
# If no method is configured for HttpRequest Provider, GET is used by default.
_HTTP_methods = {
                   'GET':       requests.get,
                   'POST':      requests.post,
                   'PUT':       requests.put,
                   'DELETE':    requests.delete,
                   'HEAD':      requests.head,
                   'OPTIONS':   requests.options
                  }

# List of authentication methods supported by HttpRequest Provider. 
# If the Provider is configured with another method, an exception is raised.
# If no authentication method is configured but user and password are set for HttpRequest Provider, basic authentication is used by default.
_authentication_methods = {
                   'basic':       requests.auth.HTTPBasicAuth,
                   'digest':      requests.auth.HTTPDigestAuth
                  }

class HttpRequest(Provider):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by HttpRequest provider
    _mandatory_parameters = [
                        'url' # URL on which the HTTP request will be performed
                        ]
    
    _optional_parameters = [
                        'requested_data', # (string) Requested data (default is 'status' which returns the HTTP status code). See _data_available for available options.
                        'method', # (string) HTTP method to use (if not provided, default is 'GET'). See _HTTP_methods for available options.
                        'body', # (string/dict) body of the HTTP request, for POST/PUT requests.
                        'cookies', # (dict) List of cookies to use in the HTTP request (expects a dictionary of keys=cookies name / values=cookies value)
                        'headers', # (dict) List of headers to use in the HTTP request (expects a dictionary of keys=header name / values=header value)
                        'authentication_method', # (string) Authentication method to use for the HTTP request (optional). Supported authentication methods are "basic" and "digest". If user and password are provided and authentication_method is not provided, "basic" authentication method is used by default.
                        'user', # (string) User name to use for authentication of the HTTP request.
                        'password', # (string) User password to use for authentication of the HTTP request.
                        'allow_redirects' # (boolean) Disable redirection handling.
                         ]
    
    def __init__(self, options):
        Provider.__init__(self, options)
        
        # Extract some options from the _config variable (easier to manage)
        self.url = self._config.get('url')
        
        if not self._config.get('method'):
            getLogger(__name__).info('Option "method" is not provided to provider HttpRequest, use default method (GET)')
        self.method = self._config.get('method') or 'GET'
        
        if self._config.get('body') != None:
            self.body = self._config.get('body')
        else:
            self.body = None
        
        if self._config.get('cookies') and type(self._config.get('cookies')) is dict:
            self.cookies = self._config.get('cookies')
        else:
            self.cookies = None
        
        if self._config.get('headers') and type(self._config.get('headers')) is dict:
            self.headers = self._config.get('headers')
        else:
            self.headers = None
        
        self.user = self._config.get('user') or None
        self.password = self._config.get('password') or None
        if self.user and self.password:
            if not self._config.get('authentication_method'):
                getLogger(__name__).info('Option "authentication_method" is not provided to provider HttpRequest, use default method (basic)')
            self.authentication_method = self._config.get('authentication_method') or 'basic'
        else:
            self.authentication_method = None
            
        if self._config.get('allow_redirects') != None and type(self._config.get('allow_redirects')) is bool:
            self.allow_redirects = self._config.get('allow_redirects')
        else:
            self.allow_redirects = True
        
        # TODO: add more actions (regexp on response body, headers,...)
        # Load requested data (default is 'status')
        self.requested_data = self._config.get('requested_data') or "status"


    def process(self):
        # Perform the request
        response = self._performRequest()
        if not response:
            # response is not defined because an error occurred in _performRequest, return None
            return None
        else:
            # TODO: add more actions
            if (self.requested_data == "status"):
                return response.status_code
            if (self.requested_data == "content"):
                try:
                    return response.json()
                except:
                    return response.content
  
  
    def _performRequest(self):
        try:
            getLogger(__name__).debug('Perform http request ' + self.method + ' ' + self.url + ', allow redirects: ' + str(self.allow_redirects) + \
                                      ', body: ' + str(self.body) + ', headers: ' + str(self.headers) + ', cookies: ' + str(self.cookies) + \
                                      ', authentication_method: ' + str(self.authentication_method) + ', user: ' + str(self.user) + ', password: ' + str(self.password))
            # use authentication for the request if requested
            auth = None
            if self.authentication_method:
                auth = _authentication_methods[self.authentication_method](self.user, self.password)
            # Perform the HTTP request using the requested parameters
            return _HTTP_methods[self.method](self.url, data=self.body, headers=self.headers, cookies=self.cookies, auth=auth, allow_redirects=self.allow_redirects)
        # TODO: better management of requests exceptions (timeout, toomanyredirects, dns issue,...)
        except Exception:
            getLogger(__name__).error('The url specified in your config file is not known by the DNS. Please check your url.', exc_info=True)
    
    
    # This function is called by __init__ of the abstract Provider class, it verify during the object initialization if the Provider' configuration is valid.
    def _isConfigValid(self):
        Provider._isConfigValid(self)
        # If requested_data is provided, check if it is managed by HttpRequest provider
        if self._config.get('requested_data') and not (self._config.get('requested_data') in _data_available):
            getLogger(__name__).error('Parameter requested_data "' + self._config.get('requested_data') + '" provided to provider HttpRequest is not allowed. Allowed conditions are: ' + str(_data_available))
            return False
        # If method is provided, check if it is managed by HttpRequest provider
        if self._config.get('method') and not _HTTP_methods.has_key(self._config.get('method')):
            getLogger(__name__).error('Parameter method "' + self._config.get('method') + '" provided to provider HttpRequest is not allowed. Allowed conditions are: ' + str(_HTTP_methods.keys()))
            return False
        # If authentication_method is provided, check if it is managed by HttpRequest provider
        if self._config.get('authentication_method') and not _authentication_methods.has_key(self._config.get('authentication_method')):
            getLogger(__name__).error('Parameter authentication_method "' + self._config.get('authentication_method') + '" provided to provider HttpRequest is not allowed. Allowed conditions are: ' + str(_authentication_methods.keys()))
            return False
        return True
