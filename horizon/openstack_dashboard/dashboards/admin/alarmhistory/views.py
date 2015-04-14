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


from django.views.generic import TemplateView  # noqa
from datetime import datetime  # noqa
from datetime import timedelta  # noqa

import json
import types

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

    
class IndexView(views.APIView):
    template_name = 'admin/alarmhistory/index.html'
    def get_data(self, request, context, *args, **kwargs):
        alist = ceilometer.ceilometerclient(request).alarms.list(q=None); 
        hostname = request.GET.get('hostname', '')
        meter = request.GET.get('meter', '')
        meters = ["hardware.ipmi.node.cups","hardware.ipmi.node.inlet_temperature","hardware.ipmi.node.outlet_temperature"];
        hypervisors = []
        try:
            hypervisors = api.nova.hypervisor_list(request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(request,
                _('Unable to retrieve hypervisor information.'))
        
        context["hypervisors"] = hypervisors
        context['currentHost'] = hostname
        context['meters'] = meters
        context['meter'] = meter;
        def filterBy(item):
            alarm = item.to_dict()
            c1 = c2  = False
            if(hostname != '' and alarm['threshold_rule']['query'][0]['value'] == hostname):
               c1 = True
            elif(hostname == ''):
               c1 = True 
            if(meter != '' and alarm['threshold_rule']['meter_name'] == meter):
               c2 = True
            elif(meter == ''):
               c2 = True
            return c1 and c2
        
        alist = filter(filterBy, alist)
        alarmHistorys = []
        
        for alarm in alist:
            alarmHistorys.extend(ceilometer.ceilometerclient(request).alarms.get_history(alarm.alarm_id))
            
        def filterByState(item):    
            try:        
                detail = json.loads(item.detail)
                item.detail = detail
                state = detail['state']
                return state == 'alarm' or state == 'ok' 
            except Exception:
                return False
        
        
        context['historys'] = filter(filterByState,alarmHistorys)
        def comp(x, y):
            return cmp(y.timestamp, x.timestamp)
        
        context['historys'].sort(cmp = comp)
        context['historys'] = context['historys'][:100]
        context['alarmMap'] = alist
        return context 