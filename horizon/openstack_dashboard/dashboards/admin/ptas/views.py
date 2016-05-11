#
# Copyright (c) 2015 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

### notes: this sample code is based on source code of horizon pannel: horizon/openstackdashboard/dashboards/admin/metering/
from django.views.generic import TemplateView  # noqa
from datetime import datetime  # noqa
from datetime import timedelta  # noqa

import json

from django.http import HttpResponse   # noqa
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon.utils import csvbase
from horizon import views

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer
from horizon.utils import functions as utils

meter_default = 'hardware.ipmi.node.temperature'

class IndexView(views.APIView):
    template_name = 'admin/ptas/index.html'
    
    
    
    def get_data(self, request, context, *args, **kwargs):
        all_meters = ceilometer.meter_list(request)
        ptasMeters = []
        ptasNames = []
        for meter in all_meters:
            if(meter.name.encode("utf-8").startswith("hardware.ipmi.node")):
                if(meter.name not in ptasNames):
                    ptasMeters.append(meter)
                    ptasNames.append(meter.name);
                    
        def comp(x, y):
            return cmp(x.name,y.name)
        
        ptasMeters.sort(cmp = comp)
        context["ptasMeters"] = ptasMeters
        
        hypervisors = []
        try:
            hypervisors = api.nova.hypervisor_list(request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(request,
                _('Unable to retrieve hypervisor information.'))
        
        context["hypervisors"] = hypervisors
        context['meter_default'] = meter_default;

        return context
          
class SamplesView(generic.TemplateView):   
    
    def _series_for_meter(self,aggregates,
                          resource_name,
                          meters,
                          stats_name
                          ):
        """Construct datapoint series for a meter from resource aggregates."""
        
        series = []
        for meter in meters:
            meter_name = meter.replace(".", "_")
            for resource in aggregates:
                if resource.get_meter(meter_name):
                #if getattr(resource, meter_name):
                    point = {'unit': '',
                             'name': meter_name,
                             'data': []}
                    for statistic in resource.get_meter(meter_name):
                    #for statistic in getattr(resource, meter_name):
                        date = statistic.duration_end[:19]
                        value = float(getattr(statistic, stats_name))
                        point['data'].append({'x': date, 'y': value})
                    point['unit'] = self._meter_dict[meter].unit
                    series.append(point)
        return series

    def get(self, request, *args, **kwargs):
        meters = request.GET.getlist('meter[]', [meter_default])
        date_options = request.GET.get('date_options', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        stats_attr = request.GET.get('stats_attr', 'avg')
        group_by = request.GET.get('group_by', None)
        host = request.GET.get('host', None)

        all_meters = ceilometer.meter_list(request);
        self._meter_dict = {}
        for item in all_meters:
            self._meter_dict[item.name] = item
        

        resources = self.query_data(request,
                                     date_from,
                                     date_to,
                                     date_options,
                                     group_by,
                                     meters, host)
        resource_name = 'resource_id'
        series = self._series_for_meter(resources,
                                        resource_name,
                                        meters,
                                        stats_attr)

        return HttpResponse(json.dumps(series), content_type='application/json')
        
        
        
    def query_data(self, request,
               date_from,
               date_to,
               date_options,
               group_by,
               meters,
               host,
               period=None,
               additional_query=None):
        date_from, date_to = self._calc_date_args(date_from,
                                         date_to,
                                         date_options)
        if not period:
            period = self._calc_period(date_from, date_to)
        if additional_query is None:
            additional_query = []
        if date_from:
            additional_query += [{'field': 'timestamp',
                              'op': 'ge',
                              'value': date_from}]
        if date_to:
            additional_query += [{'field': 'timestamp',
                              'op': 'le',
                              'value': date_to}]

        # TODO(lsmola) replace this by logic implemented in I1 in bugs
        # 1226479 and 1226482, this is just a quick fix for RC1


        query = []

        def filter_by_host_name(resource):
                """Function for filtering of the list of resources.

                Will pick the right resources according to currently selected
                meter.
                """
                if resource.resource_id == host:
                    return True
                return False

        ceilometer_usage = ceilometer.CeilometerUsage(request)
        try:
                resources = ceilometer_usage.resources_with_statistics(
                    query, meters, period=period, stats_attr=None,
                    additional_query=additional_query,
                    filter_func=filter_by_host_name)
        except Exception:
                resources = []
                exceptions.handle(request,
                                  _('Unable to retrieve statistics.'))
        print resources
        return resources


    def _calc_period(self, date_from, date_to):
        if date_from and date_to:
            if date_to < date_from:
                # TODO(lsmola) propagate the Value error through Horizon
                # handler to the client with verbose message.
                raise ValueError("Date to must be bigger than date "
                                 "from.")
                # get the time delta in seconds
            delta = date_to - date_from
            if delta.days <= 0:
                # it's one day
                delta_in_seconds = 3600 * 24
                number_of_samples = 6 * 24
            else:
                delta_in_seconds = delta.days * 24 * 3600 + delta.seconds
                number_of_samples = 400
                # Lets always show 400 samples in the chart. Know that it is
            # maximum amount of samples and it can be lower.
            
            period = delta_in_seconds / number_of_samples
        else:
            # If some date is missing, just set static window to one day.
            period = 3600 * 24
        return period


    def _calc_date_args(self, date_from, date_to, date_options):
        # TODO(lsmola) all timestamps should probably work with
        # current timezone. And also show the current timezone in chart.
        if (date_options == "other"):
            try:
                if date_from:
                    date_from = datetime.strptime(date_from,
                                                  "%Y-%m-%d")
                else:
                    # TODO(lsmola) there should be probably the date
                    # of the first sample as default, so it correctly
                    # counts the time window. Though I need ordering
                    # and limit of samples to obtain that.
                    pass
                if date_to:
                    date_to = datetime.strptime(date_to,
                                                "%Y-%m-%d")
                    # It return beginning of the day, I want the and of
                    # the day, so i will add one day without a second.
                    date_to = (date_to + timedelta(days=1) -
                               timedelta(seconds=1))
                else:
                    date_to = datetime.now()
            except Exception:
                raise ValueError("The dates haven't been "
                                 "recognized")
        else:
            try:
                date_from = datetime.now() - timedelta(days=int(date_options))
                date_to = datetime.now()
            except Exception:
                raise ValueError("The time delta must be an "
                                 "integer representing days.")
        return date_from, date_to


class DataView(generic.TemplateView):
    
    def get(self, request, *args, **kwargs):
        queryClient = ceilometer.ceilometerclient(request).samples
        limit = request.GET.get('limit', 1)
        currentHost = request.GET.get('host', '')
        q = []
        q.append({"field":"resource_id", "op":"eq", "value" : currentHost})
        ret = []
        meters = request.GET.getlist('meter[]', [meter_default])
        for meter_name in meters:
            data = queryClient.list(meter_name, q,  limit)
            point = {}
            point['name'] = meter_name
            point['data'] = []  
            unit = ''
            for item in data:
                point['data'].append({"y":item.counter_volume, "x":item.timestamp})
                unit = item.counter_unit
            point['unit'] = unit
            ret.append(point)
        return HttpResponse(json.dumps(ret), content_type='application/json')


