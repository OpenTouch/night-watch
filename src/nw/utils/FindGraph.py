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

import sys
from nw.core import Log
import logging
from facette.client import Facette

def _checkMetricAvailability(fc, source_name, metric_name):
    test_metric = fc.catalog.metrics.get(metric_name)
    if source_name in test_metric.sources:
        logging.getLogger().info("Metric " + metric_name + " is well available for host " + source_name)
        return True
    else:
        return False

def _findGraphName(fc, source_name, metric_name):
    graph_list = fc.library.graphs.list(filter=None)
    # Look in the graph list which one has a serie containing the requested metric
    logging.getLogger(__name__).info('Search graph containing the metric "' + metric_name + '" for source "' + source_name + '" from "' + str(len(graph_list)) + ' graphs')
    for g in graph_list:
        #logging.getLogger(__name__).info('Look for requested metric "' + metric_name + '" for source "' + source_name + '" in graph with id ' + g.id + ' named "' + g.name + '"')
        graph = fc.library.graphs.get(g.id)
        # Find the serie containing the requested metric or serie name
        for group in graph.groups:
            #logging.getLogger(__name__).debug('Look for requested metric "' + metric_name + '" for source "' + source_name + '" in group named ' + group.name + '" from graph with id ' + g.id + ' named "' + g.name + '"')
            for serie in group.series:
                if serie.source == source_name and serie.metric == metric_name:
                    logging.getLogger(__name__).info('Requested metric "' + metric_name + '" for source "' + source_name + '" found in graph with id ' + g.id + ' named "' + g.name + '", related serie name is "' + serie.name + '"')
                    return serie.name
    # If no graph found, return an 
    logging.getLogger(__name__).info('No graph found for metric "' + metric_name + '" and source "' + source_name + '"')


if __name__ == "__main__":
    LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)-8s] [%(threadName)-10s] [%(module)s]: %(message)s'
    LEVEL = 'INFO'
    # set the default log level
    log_config = {
        'version': 1,
        'formatters': {
            'standard': {
                'format': LOG_FORMAT
            },
        },
        'handlers': {
            'console': {
                'level':'DEBUG',    
                'class':'logging.StreamHandler',
            },  
        },
        'loggers': {
            '__main__': {                  
                'handlers': ['console'],        
                'level': LEVEL,  
                'propagate': False  
            }
        },
        'root': {
            'level': 'ERROR',
            'handlers': ['console']
            }
    }
    Log.reconfigure(log_config)

    # use UTF-8 encoding instead of unicode to support more characters
    reload(sys)
    sys.setdefaultencoding("utf-8")
    
    srv = "http://demo.facette.io/"
    usr = ""
    pwd = ""
    fc = Facette(srv, usr, pwd)

    # argument in command line
    args = list(sys.argv)
    if len(args) != 3:
        logging.getLogger(__name__).error("You must give exactly two arguments. The first argument is the source name and the second argument is the metric name")
        sys.exit(2)


    source_name = args[1]       # ex: "host1.example.net"
    metric_required = args[2]   # ex: "load.midterm"
    
    if _checkMetricAvailability(fc, source_name, metric_required):
        _findGraphName(fc, source_name, metric_required)
