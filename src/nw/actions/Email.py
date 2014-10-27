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

from nw.actions.Action import Action

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import os
from logging import getLogger


class Email(Action):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by Email action
    _mandatory_parameters = [
                        'email_from_addr',
                        'email_to_addrs'
                        ]
    
    _optional_parameters = [
                        'smtp_srv_url', # SMTP server url is optional, localhost is used if url is not provided
                        'smtp_srv_port', # SMTP port is optional, smtplib uses the default SMTP port if port is not provided
                        'smtp_srv_login',
                        'smtp_srv_password',
                        'smtp_srv_tls',
                        'smtp_srv_tls_keyfile',
                        'smtp_srv_tls_certfile',
                        'email_cc_addrs',
                        'email_subject',
                        'email_header',
                        'services_monitored',
                        'email_content_success',
                        'email_content_failed',
                        'email_signature'
                         ]
    
    def __init__(self, task_options):
        Action.__init__(self, task_options)
        
        # If SMTP server url is not provided, use localhost
        if not self._config.get('smtp_srv_url'):
            getLogger(__name__).info('Option "smtp_srv_url" is not provided to action Email, use default SMTP server (localhost)')
        self.smtp_srv_url = self._config.get('smtp_srv_url') or 'localhost'


    def process(self, state, conditions, thresholds, values):
        # TODO: improve the Email action (add template, options,...)
        # Send an email
        try:
            # Connect to the SMTP server
            self.smtp = smtplib.SMTP(self.smtp_srv_url, 
                                    self._config.get('smtp_srv_port'))
            
            # Use TLS connection if required
            if self._config.get('smtp_srv_tls'):
                getLogger(__name__).debug('Use SSL')
                self.smtp.starttls(self._config.get('smtp_srv_tls_keyfile'), self._config.get('smtp_srv_tls_certfile'))
                
            # Use credentials if required
            if self._config.get('smtp_srv_login') and self._config.get('smtp_srv_password'):
                getLogger(__name__).debug('Login to the SMTP server with credentials ' + self._config.get('smtp_srv_login') + ':' + self._config.get('smtp_srv_password'))
                self.smtp.login(self._config.get('smtp_srv_login'), self._config.get('smtp_srv_password'))
                
            # Build email header
            # Add 'From' header
            header  = 'From: %s\n' % self._config.get('email_from_addr')
            # Add 'To' header
            if type(self._config.get('email_to_addrs')) is list:
                emails_list = ""
                for email in self._config.get('email_to_addrs'):
                    emails_list += email + ", "
                header += 'To: %s\n' % emails_list
            elif type(self._config.get('email_to_addrs')) is str:
                header += 'To: %s\n' % self._config.get('email_to_addrs')
            # Add 'Cc' header (if needed)
            if self._config.get('email_cc_addrs'):
                if type(self._config.get('email_cc_addrs')) is list:
                    emails_list_cc = ""
                    for email in self._config.get('email_cc_addrs'):
                        emails_list_cc += email + ", "
                    header += 'To: %s\n' % emails_list_cc
                elif type(self._config.get('email_cc_addrs')) is str:
                    header += 'Cc: %s\n' % self._config.get('email_cc_addrs')
            # Add 'Subject' header
            subject = self._config.get('email_subject') or ''
            header += 'Subject: %s\n\n' % subject
            
            # Build email message (concatenate email header and email body)

            message = "Hello, \n\n"
            message += self._config.get('email_header') + ".\n\n"

            if state == True:
                message += self._config.get('email_content_success') + " " + self._config.get('services_monitored') + ".\n\n" 
            else:
                message += self._config.get('email_content_failed') + " " + self._config.get('services_monitored') + ".\n\n" 

            message += self._constructResultMessage(conditions, thresholds, values)

            message += self._config.get("email_signature")

            message = header + message
            
            # Send the email
            self.smtp.sendmail(self._config.get('email_from_addr'), self._config.get('email_to_addrs'), message)  
            getLogger(__name__).info('Email sent')
            
            # Close the connection with the SMTP
            self.smtp.quit()
            
        except smtplib.SMTPConnectError:
            getLogger(__name__).error('Not able to connect to SMTP server. Please check action Email configuration', exc_info=True)
            raise
        except smtplib.SMTPAuthenticationError:
            getLogger(__name__).error('Not able to connect to SMTP server because of an authentication issue. Please check SMTP credentials in action Email configuration', exc_info=True)
            raise
        except:
            getLogger(__name__).error('Unable to send email', exc_info=True)
            raise
    
    
    # This function is called by __init__ of the abstract Action class, it verify during the object initialization if the Action' configuration is valid.
    def _isConfigValid(self):
        Action._isConfigValid(self)
        # If certificate files are provided, check if they exist
        if self._config.get('smtp_srv_tls_keyfile') and not os.path.exists(self._config.get('smtp_srv_tls_keyfile')):
            getLogger(__name__).error('Option "smtp_srv_tls_keyfile" is provided to action Email, but the file is not accessible. Please check Email configuration.')
            return False
        if self._config.get('smtp_srv_tls_certfile') and not os.path.exists(self._config.get('smtp_srv_tls_certfile')):
            getLogger(__name__).error('Option "smtp_srv_tls_certfile" is provided to action Email, but the file is not accessible. Please check Email configuration.')
            return False
        return True

    def _constructResultMessage(self, conditions, thresholds, values):
        i = 0
        for value in values:
            separator = " than "
            if (conditions[i] == "equals" and conditions[i] == "different"):
                separator = " to "
            resultMessage = "The condition is : " + str(conditions[i]) + separator + str(thresholds[i]) + ".\n\n"
            resultMessage += "The result of the monitor request is : " + str(value) + ".\n\n"
            i = i + 1
        return resultMessage