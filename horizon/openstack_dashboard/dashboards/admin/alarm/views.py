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
    template_name = 'admin/alarm/alarms.html'
    def get_data(self, request, context, *args, **kwargs):
        meters = ["hardware.ipmi.node.cups","hardware.ipmi.node.inlet_temperature","hardware.ipmi.node.inlet_temperature","hardware.ipmi.node.outlet_temperature"];
        operators = ['gt', 'gt', 'lt', 'gt']
        thresholds = [80, 32, 18, 40]
        
        context['meters'] = meters;
        context['operators'] = operators;
        context['thresholds'] = thresholds
        #alist = ceilometer.alarms_list(request)
        hypervisors = []
        try:
            hypervisors = api.nova.hypervisor_list(request)
            hypervisors.sort(key=utils.natural_sort('hypervisor_hostname'))
        except Exception:
            exceptions.handle(request,
                _('Unable to retrieve hypervisor information.'))
        alist = ceilometer.ceilometerclient(request).alarms.list(q=None); 
        pos = 0;
        #check if the alarm for the meters is already set, if not then create a new one
        for meter in meters:    
            for hypervisor in hypervisors:
                hasAlarm = False
                for alarm in alist:
                    odict = alarm.to_dict()
                    
                    if(odict['threshold_rule']['meter_name'] == meter 
                       and odict['threshold_rule']['query'][0]['field'] == 'resource_id' 
                       and odict['threshold_rule']['query'][0]['value'] == hypervisor.hypervisor_hostname
                       and odict['threshold_rule']['comparison_operator'] == operators[pos]) :
                        hasAlarm = True
                if(hasAlarm == False):
                    threshold  = thresholds[pos]
                    kwargs = {'name':operators[pos] + ' threshold for ' + meter + ' of ' + hypervisor.hypervisor_hostname, 
                              'description':'alarm when ' + meter + ' '+operators[pos]+' ' + '%d' %threshold, 
                              'type':'threshold', 'enabled':True,
                              'period' : 300,
                              'repeat_actions' : True,
                              'threshold_rule' : {'threshold': threshold, 'meter_name': meter, 
                                                'comparison_operator': operators[pos], 
                                                'query':[{'field':'resource_id','value':hypervisor.hypervisor_hostname}]}}
                    ceilometer.ceilometerclient(request).alarms.create(**kwargs)    
            pos = pos + 1
        #query the current alarm list
        alist = ceilometer.ceilometerclient(request).alarms.list(q=None); 
        alarms_map = {}
        for alarm in alist:
             odict = alarm.to_dict()
             key = odict['threshold_rule']['meter_name'] + odict['threshold_rule']['comparison_operator']
             alarms_map[key] = odict
        context['alarms'] = []
        for d,x in alarms_map.items():
            x['threshold_rule']['threshold'] = int(x['threshold_rule']['threshold'])
            context['alarms'].append(x)
        def comp(x, y):
            return cmp(x['threshold_rule']['meter_name'],y['threshold_rule']['meter_name'])
        context['alarms'].sort(cmp = comp)
        return context 
    
class AlarmUpdate(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        ret = {}
        meter_name = request.GET.get('meter', None)
        threshold = request.GET.get('threshold', None)
        operator = request.GET.get('operator', None)
        
        if(meter_name == None or threshold == None or operator == None):
            ret['status'] = -1
            ret['message'] = 'parameters error: no empty data accepted'
        else:
            alist = ceilometer.ceilometerclient(request).alarms.list(q=None);
            kwargs = {'threshold_rule':{'threshold': threshold}, 
                      'repeat_actions':True} 
            for alarm in alist:
                odict = alarm.to_dict()
                if(odict['threshold_rule']['meter_name'] == meter_name 
                       and odict['threshold_rule']['query'][0]['field'] == 'resource_id' 
                       and odict['threshold_rule']['comparison_operator'] == operator) :
                    ceilometer.ceilometerclient(request).alarms.update(odict['alarm_id'], **kwargs)
            ret['status'] = 0
        
        return HttpResponse('<script>window.location.href="/admin/alarm/";</script>',
            content_type='text/html')

