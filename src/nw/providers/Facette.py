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

import sys, re
from logging import getLogger
from facette.client import Facette as FacetteClient


# List of data the Facette Provider can return (set in Provider's config field 'requested_data').
# If the Provider is configured with another requested_data, an exception is raised.
# If no requested_data is configured for Facette Provider, raw_value is used by default.
_data_available = [
                   'raw_value', # directly returns the value obtained from Facette server according to plot_info parameter
                   'ratio' # returns a ratio computed from several metrics values within the same graph, according to the configuration of 'metrics_names_list_numerator' and 'metrics_names_list_denominator'. Ratio is computed as follow: sum(metrics in metrics_names_list_numerator) / sum(metrics in metrics_names_list_denominator)
                  ]

# List of plot_info supported by Facette Provider. 
# If the Provider is configured with another plot_info, an exception is raised.
# If no plot_info is configured for Facette Provider, 'avg' is used by default.
_plot_infos = [
                   'min',
                   'max',
                   'last',
                   'avg'
                ]

# Regex for plot_range supported by Facette Provider. 
# If the Provider is configured with a plot_range which doesn't match this regex, an exception is raised.
# If no plot_range is configured for Facette Provider, '-300s' is used by default.
_plot_range_pattern = "^-[\d]+[smhdy]|mo$"

class Facette(Provider):
    
    # Overload _mandatory_parameters and _optional_parameters to list the parameters required by Facette provider
    _mandatory_parameters = [
                        'facette_srv_url', # (string) URL of the Facette server to use
                        'source_name', # (string) Name of the source (host) for which the value will collected from Facette graph
                        ]
    
    _optional_parameters = [
                        'requested_data', # (string) Requested data (default is 'raw_value' which returns the value obtained from Facette server). See _data_available for available options.
                        'facette_srv_user', # (string) User name for Facette server API authentication
                        'facette_srv_pwd', # (string) User password for Facette server API authentication
                        'graph_name_filter', # (string) Facette graph name is optional but recommended. It allows to reduce the list of graphs to loop for searching the requested metric. The filter can be the exact name of the graph or 'regexp:graph name pattern*'
                        'metric_name', # (string) Name of the metric to get from the Facette graph (mandatory if requested_data is 'raw_value')
                        'metrics_names_list_numerator', # (array of strings) List of metrics names to get from the graph and to use in the numerator for computing the ratio (mandatory if requested_data is 'ratio')
                        'metrics_names_list_denominator', # (array of strings) List of metrics names to get from the graph and to use in the denominator for computing the ratio (mandatory if requested_data is 'ratio')
                        'plot_range', # (string) plot range is optional, -300s is used by default if plot_range is not provided
                        'plot_info' # (string) plot info is optional, avg is used by default if plot_range is not provided
                         ]
    
    def __init__(self, options):
        Provider.__init__(self, options)
        # use UTF-8 encoding instead of unicode to support more characters
        reload(sys)
        sys.setdefaultencoding("utf-8")
        
        # Load requested data (default is 'raw_value')
        self.requested_data = self._config.get('requested_data') or "raw_value"
        
        # If plot_range is not provided, use -300s by default
        self.plot_range = self._config.get('plot_range') or '-300s'
        # If plot_info is not provided, use avg by default
        self.plot_info = self._config.get('plot_info') or 'avg'
        
        # Compute the list of metrics names requested according to requested_data
        if self.requested_data == "raw_value":
            self.metrics_names_list = [self._config.get('metric_name')]
        else:
            self.metrics_names_list = self._config.get('metrics_names_list_numerator') + self._config.get('metrics_names_list_denominator')
            # Remove duplicates metrics from metrics_names_list (some metrics can be both on numerator and denominator, removing the duplicates avoid to search twice the same metric's serie)
            self.metrics_names_list = list(set(self.metrics_names_list))
        
        # Instantiate the Facette client
        getLogger(__name__).debug('Instantiate Facette client with url ' + self._config.get('facette_srv_url'))
        self.fc = FacetteClient(self._config.get('facette_srv_url'), 
                                user = self._config.get('facette_srv_user'), 
                                passwd = self._config.get('facette_srv_pwd'))
        
        # Required data to get the plot allowing to retrieve the required data are the graph id and the series names. 
        # Search them from the provided data (metrics_names_list and source_name) by looping on all graphs available on Facette server.
        self.graph_id, self.series_names = self._findGraph(self.fc, self._config.get('source_name'), self.metrics_names_list, self._config.get('graph_name_filter'))


    def process(self):
        try:
            plot = self.fc.library.graphs.plots.get(self.graph_id, self.plot_range)
        except Exception:
            getLogger(__name__).error('Error occurred while trying to get plots from graph with id ' + self.graph_id + '. Facette server may be down.', exc_info=True)
            raise
        if not plot:
            # Graph id may has changed (delete/recreate graph, facette server re-deployed,...) - try to find again the graph id and relaunch the process function (if a new graph is not found, an exception will be raised by _findGraph)
            getLogger(__name__).error('The plots from graph with id ' + self.graph_id + ' is not found. The graph may has been deleted... Try to find the new graph id and call again process')
            self.graph_id, self.series_names = self._findGraph(self.fc, self._config.get('source_name'), self.metrics_names_list, self._config.get('graph_name_filter'))
            getLogger(__name__).info('Plot containing requested metrics "' + str(self.metrics_names_list) + '" for source "' + self._config.get('source_name') +'" has been found in graph with id ' + self.graph_id + '. Use this one from now on')
            return self.process()
        
        if self.requested_data == 'raw_value':
            # Get the value from the requested metric and return it
            value = self._getMetricValueFromPlot(self, plot, self.series_names[self._config.get('metric_name')], self.plot_info)
            getLogger(__name__).debug('Value is ' + str(value) + ' for requested metric "' + self._config.get('metric_name') + '". Read from graph with id ' + self.graph_id + ', serie name "' + self.series_names[self._config.get('metric_name')] + '"')
            return value
        
        elif self.requested_data == 'ratio':
            numerator_values = []
            denominator_values = []
            for metric_numerator in self._config.get('metrics_names_list_numerator'):
                # Get the value from the current metric
                value = self._getMetricValueFromPlot(plot, self.series_names[metric_numerator], self.plot_info)
                # Add the value to the numerator array
                numerator_values.append(value)
            for metric_denominator in self._config.get('metrics_names_list_denominator'):
                # Get the value from the current metric
                value = self._getMetricValueFromPlot(plot, self.series_names[metric_denominator], self.plot_info)
                # Add the value to the numerator array
                denominator_values.append(value)
            # Compute the ratio
            getLogger(__name__).debug('Compute ratio from following values: ' + str(numerator_values) + ' / ' + str(denominator_values))
            ratio = sum(numerator_values) / sum(denominator_values)
            getLogger(__name__).debug('Ratio value is ' + str(ratio) + ' for requested metrics (' + str(self._config.get('metrics_names_list_numerator')) + ') / (' + str(self._config.get('metrics_names_list_denominator')) + '). Read from graph with id ' + self.graph_id)
            return ratio
    
    
    def _findGraph(self, fc, source_name, metrics_names_list, graph_name = None):
        # Search the graph and the name of the series containing the requested metrics from the requested source name.
        # Note: if a graph name is provided, we can filter on this name to reduce the number of graphs to look for the requested metrics
        graph_list = fc.library.graphs.list(filter=graph_name)
        if not graph_list:
            if graph_name:
                err_msg = 'The graph with name "' + graph_name + '" is not found on Facette server'
            else:
                err_msg = 'No graphs found. Please check if Facette server is running and has graphs defined.'
            raise Exception(err_msg)
        # Look in the graph list which one has a serie containing the requested metric
        getLogger(__name__).debug('Search graph containing the metrics "' + str(metrics_names_list) + '" for source "' + source_name + '" from "' + str(len(graph_list)) + ' graphs')
        metrics_series_names = {}
        for g in graph_list:
            graph = fc.library.graphs.get(g.id)
            # Find the serie containing the requested metric or serie name
            for group in graph.groups:
                for serie in group.series:
                    if serie.source == source_name and serie.metric in metrics_names_list:
                        getLogger(__name__).debug('Requested metric "' + serie.metric + '" for source "' + source_name + '" has been found in group named ' + group.name + '" from graph with id ' + g.id + ', related serie name is "' + serie.name + '"')
                        metrics_series_names[serie.metric] = serie.name
            # Once the loop on groups is finished, if metrics_series_names is defined it means that metrics have been found in this graph
            if metrics_series_names:
                if len(metrics_series_names.keys()) == len(metrics_names_list):
                    # All the metrics have been found in this graph, return the graph id and the dictionary mapping the metrics names to the series names
                    return g.id, metrics_series_names
                else:
                    # Some metrics have not been found in the graph 
                    raise Exception('Only the following metrics where found in graph with id ' + str(g.id) + ': ' + str(metrics_series_names.keys()))
                    
        # If no graph found, raise an exception
        raise Exception('No graph found for metrics "' + str(metrics_names_list) + '" and source "' + source_name + '"')
    
    
    def _findPlotSerie(self, plot, serie_name):
        # Look for the plot serie containing the requested metric
        for serie in plot.series:
            if serie.name == serie_name:
                return serie
        # No serie found with the given name... This error should not happen, the serie name has been obtained during facette provider's initialization (otherwise an error should have been raised). 
        # It may occur if the serie has been removed from the graph.
        raise Exception('The plot serie "' + serie_name + '" containing the required metric is not found')
    
    
    def _getMetricValueFromPlot(self, plot, metric_name, plot_info):
        # Look for the plot serie containing the requested metric
        plot_serie = self._findPlotSerie(plot, metric_name)
        # Get the value from the requested metric and return it
        return plot_serie.summary.summary.get(plot_info)
        
    
    # This function is called by __init__ of the abstract Provider class, it verify during the object initialization if the Provider' configuration is valid.
    def _isConfigValid(self):
        Provider._isConfigValid(self)
        # If requested_data is provided, check if it is managed by Facette provider
        if self._config.get('requested_data') and not (self._config.get('requested_data') in _data_available):
            getLogger(__name__).error('Parameter requested_data "' + self._config.get('requested_data') + '" provided to provider Facette is not allowed. Allowed conditions are: ' + str(_data_available))
            return False
        # If requested_data is 'raw_data', check that 'metric_name' mandatory parameter is well provided
        if (not self._config.get('requested_data') or self._config.get('requested_data') == 'raw_data') and not self._config.get('metric_name'):
            getLogger(__name__).error('Parameter metric_name is not provided. Parameter metric_name is mandatory if requested_data parameter is "raw_data".')
            return False
        # If requested_data is 'ratio', check that 'metrics_names_list_numerator' and 'metrics_names_list_denominator' mandatory parameters are well provided
        if self._config.get('requested_data') == 'ratio' and ((not self._config.get('metrics_names_list_numerator') or type(self._config.get('metrics_names_list_numerator')) is not list) and (not self._config.get('metrics_names_list_denominator') or type(self._config.get('metrics_names_list_denominator')) is not list)):
            getLogger(__name__).error('Parameter metrics_names_list_numerator and / or metrics_names_list_denominator are not provided. Parameter metrics_names_list_numerator and metrics_names_list_denominator are mandatory if requested_data parameter is "ratio".')
            return False
        # Check validity of plot_range using a regexp
        if self._config.get('plot_range') and not(re.match(_plot_range_pattern, self._config.get('plot_range'))):
            getLogger(__name__).error('Parameter plot_range "' + self._config.get('plot_range') + '" provided to provider Facette is not allowed. plot_range must match the regex ' + str(_plot_range_pattern))
            return False
        # If plot_info is provided, check if it is managed by Facette provider
        if self._config.get('plot_info') and not (self._config.get('plot_info') in _plot_infos):
            getLogger(__name__).error('Parameter plot_info "' + self._config.get('plot_info') + '" provided to provider Facette is not allowed. Allowed plot_info are: ' + str(_plot_infos))
            return False
        
        return True
