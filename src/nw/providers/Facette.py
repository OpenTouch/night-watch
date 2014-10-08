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

import sys
from logging import getLogger
from facette.client import Facette as FacetteClient



class Facette(Provider):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by Facette provider
    _mandatory_parameters = [
                        'facette_srv_url',
                        'source_name',
                        'metric_name',
                        ]
    
    _optional_parameters = [
                        'facette_srv_user',
                        'facette_srv_pwd',
                        'graph_name_filter', # Graph name is optional but recommended. It allows to reduce the list of graphs to loop for searching the requested metric. The filter can be the exact name of the graph or 'regexp:graph name pattern*'
                        'plot_range', # plot range is optional, -1h is used if plot_range is not provided
                        'plot_info' # plot info is optional, avg is used if plot_range is not provided
                         ]
    
    def __init__(self, options):
        Provider.__init__(self, options)
        # use UTF-8 encoding instead of unicode to support more characters
        reload(sys)
        sys.setdefaultencoding("utf-8")
        
        # If plot_range is not provided, use 1h by default
        self.plot_range = self._config.get('plot_range') or '-1h'
        # If plot_info is not provided, use avg by default
        self.plot_info = self._config.get('plot_info') or 'avg'
        
        # Instantiate the Facette client
        getLogger(__name__).debug('Instantiate facette server with url ' + self._config.get('facette_srv_url'))
        self.fc = FacetteClient(self._config.get('facette_srv_url'), 
                                user = self._config.get('facette_srv_user'), 
                                passwd = self._config.get('facette_srv_pwd'))
        # Required data to get the plot allowing to retrieve the required data are the graph id and the serie name. 
        # Search them from the provided data (metric and source name) by looping on all graphs available on Facette server.
        self.graph_id, self.serie_name = self._findGraph(self.fc, self._config.get('source_name'), self._config.get('metric_name'), self._config.get('graph_name_filter'))


    def process(self):
        try:
            plot = self.fc.library.graphs.plots.get(self.graph_id, self.plot_range)
        except Exception:
            getLogger(__name__).error('Error occurred while trying to get plots from graph with id ' + self.graph_id + '. Facette server may be down.', exc_info=True)
            raise
        if not plot:
            # Graph id may has changed (delete/recreate graph, facette server re-deployed,...) - try to find again the graph id and relaunch the process function (if a new graph is not found, an exception will be raised by _findGraph)
            getLogger(__name__).error('The plots from graph with id ' + self.graph_id + ' is not found. The graph may has been deleted... Try to find the new graph id and call again process')
            self.graph_id, self.serie_name = self._findGraph(self.fc, self._config.get('source_name'), self._config.get('metric_name'), self._config.get('graph_name_filter'))
            getLogger(__name__).info('Plot containing requested metric "' + self._config.get('metric_name') + '" for source "' + self._config.get('source_name') +'" has been found in graph with id ' + self.graph_id + '. Use this one from now on')
            return self.process()
        # Look for the plot serie containing the requested metric
        plot_serie = self._findPlotSerie(plot, self.serie_name)
        # Get the value from the requested metric and return it
        value = plot_serie.summary.summary.get(self.plot_info)
        getLogger(__name__).debug('Value is ' + str(value) + ' for requested metric "' + self._config.get('metric_name') + '". Read from graph with id ' + self.graph_id + ', serie name "' + self.serie_name + '"')
        return value
    
    
    def _findGraph(self, fc, source_name, metric_name, graph_name = None):
        # Search the name of the serie containing the requested metric from the requested source name.
        # Note: if a graph name is provided, we can filter on this name to reduce the number of graphs to look for the requested metric
        graph_list = fc.library.graphs.list(filter=graph_name)
        if not graph_list:
            if graph_name:
                err_msg = 'The graph with name "' + graph_name + '" is not found on Facette server'
            else:
                err_msg = 'No graphs found. Please check if Facette server is running and has graphs defined.'
            raise Exception(err_msg)
        # Look in the graph list which one has a serie containing the requested metric
        getLogger(__name__).debug('Search graph containing the metric "' + metric_name + '" for source "' + source_name + '" from "' + str(len(graph_list)) + ' graphs')
        for g in graph_list:
            getLogger(__name__).debug('Look for requested metric "' + metric_name + '" for source "' + source_name + '" in graph with id ' + g.id)
            graph = fc.library.graphs.get(g.id)
            # Find the serie containing the requested metric or serie name
            for group in graph.groups:
                getLogger(__name__).debug('Look for requested metric "' + metric_name + '" for source "' + source_name + '" in group named ' + group.name + '" from graph with id ' + g.id)
                for serie in group.series:
                    if serie.source == source_name and serie.metric == metric_name:
                        getLogger(__name__).debug('Requested metric "' + metric_name + '" for source "' + source_name + '" found in graph with id ' + g.id + ', related serie name is "' + serie.name + '"')
                        return g.id, serie.name
        # If no graph found, return an 
        raise Exception('No graph found for metric "' + metric_name + '" and source "' + source_name + '"')
    
    
    def _findPlotSerie(self, plot, serie_name):
        # Look for the plot serie containing the requested metric
        for serie in plot.series:
            if serie.name == serie_name:
                return serie
        # No serie found with the given name... This error should not happen, the serie name has been obtained during facette provider's initialization (otherwise an error should have been raised). 
        # It may occur if the serie has been removed from the graph.
        raise Exception('The plot serie "' + serie_name + '" containing the required metric is not found')
        
    
    # This function is called by __init__ of the abstract Provider class, it verify during the object initialization if the Provider' configuration is valid.
    def _isConfigValid(self):
        Provider._isConfigValid(self)
        # TODO: check validity of plot_range using a regexp
        # TODO: check validity of plot_info using a dict with allowed values
        return True
