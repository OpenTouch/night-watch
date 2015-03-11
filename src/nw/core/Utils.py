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

import yaml

def str2num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
    
def str2bool(s):    
    return s.lower() in ("true", "yes")
    
def isYamlFile(f):    
    return f.endswith(".yml") or f.endswith(".yaml")

def loadYamlFile(f):
    if isYamlFile(f):
        with open(f, "r") as yml:
            return yaml.load(yml)
    else:
        raise Exception('The file "{}" is not a yaml file.'.format(f))

def writeYamlFile(data, f):
    if isYamlFile(f):
        with open(f, "w") as yml:
            Dumper = yaml.SafeDumper
            Dumper.ignore_aliases = lambda self, data: True
            yaml.dump(data, yml, default_flow_style=False, explicit_start=True, explicit_end=True, Dumper=Dumper)
            return True
    else:
        raise Exception('File name does not have yaml extension: {}.'.format(f))
