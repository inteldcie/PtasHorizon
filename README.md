# PtasHorizon
plugin panels for Horizon dashboard to do sever level monitoring, and reporting leveraging the OpenStack Ceilometer with Intel PTAS meters

###Dependency
1. For the Ceilometer IPMI agent was upstreamed at begining of year 2015, so your openstack version must be Kilo or after to use this demo code.

2. Make sure you have run the Ceilometer IPMI agent on each of your physical nodes, in order to collect the new PTAS meters: <br/>
  ./ceilometer-agent-ipmi &

3. The panels are based on horizon panels, so please make sure you have read this horizon doc, and understand the mechanism:
http://docs.openstack.org/developer/horizon/topics/tutorial.html

### Install
1. Copy the files under horizon directory into your server's horizon folder, the path is /opt/stack/horizon if you use DevStack.
2. There might be some file conflicts in foloder horizon/openstack_dashboard/enabled if you created your own panels before, so you need to change the file name in order to resolve the conflict.

3. Restart the apache2 service to make these changes take effect.

4. Then visit horizon dashboard, you will find a new panel named "PTAS".

