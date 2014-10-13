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

from logging import getLogger
import psycopg2, psycopg2.extras

class DatabaseRequest(Provider):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by DatabaseRequest provider
    _mandatory_parameters = [
                        'database_type', # type of databse requirred for the request : 'postgresqk', 'mysql'
                        'machine_addr', # machine where is the database
                        'database_name', # name of the database
                        'user_database', # user used to connect of the database
                        'password_database', # password used to connect to the database
                        'request' # request used for your monitoring
                        ]
    
    def __init__(self, options):
        Provider.__init__(self, options)

    def process(self):
        database_type = self._config.get('database_type')
        if (database_type == "postgresql"):
            getLogger(__name__).info(database_type + "is selected")
            con = psycopg2.connect(host=self._config.get('machine_addr'), database=self._config.get('database_name'), user=self._config.get('user_database'), password=self._config.get('password_database'))
            cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(self._config.get('request'))
            result = cur.fetchone()
            con.commit()
            if result == "" and result == None:
                getLogger(__name__).info("The database request for " + self._config.get('database_name') + " is failed.")
                return "NOK"
            else:
                getLogger(__name__).info("The database request for " + self._config.get('database_name') + " is success.")
                return "OK"
        elif (database_type == "mysql"):
            getLogger(__name__).info(database_type + "is selected")
        else: 
            getLogger(__name__).error(database_type + " is not a type of database known.")

    
    # This function is called by __init__ of the abstract Provider class, it verify during the object initialization if the Provider' configuration is valid.
    def _isConfigValid(self):
        Provider._isConfigValid(self)
        return True
    
    
