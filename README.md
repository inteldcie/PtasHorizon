# PtasHorizon
Reference UI to demonstrate dynamic data collection, reporting and trending of Intel Xeon E5-7 platform level telemetry and metrics in power, thermal and compute data.

###Dependency
1. Openstack version. 
    For the Ceilometer IPMI agent was upstreamed at begining of year 2015, so your openstack version must be Kilo or after to   use this demo code.

2. Your openstack must have Ceilometer running.
  Also, please make sure you have run the Ceilometer IPMI agent on each of your physical nodes, in order to collect the new PTAS meters: <br/>
  enable_service ceilometer-alarm-evaluator,ceilometer-alarm-notifier,ceilometer-aipmi

3. Make sure the ceilometer has the admin role to use alarm<br/>
  Create a ceilometer user that the Telemetry Service uses to authenticate with the Identity Service. Use the service tenant and give the user the admin role:
  <br/>\# keystone user-create --name=ceilometer --pass=CEILOMETER_PASS --email=ceilometer@example.com
  <br/>\# keystone user-role-add --user=ceilometer --tenant=service --role=admin

4. These demo code are based on horizon panels, so please read below horizon doc, make sure you understand the mechanism:
http://docs.openstack.org/developer/horizon/topics/tutorial.html

### Install
1. Copy the files under horizon directory into your server's horizon folder, the path is /opt/stack/horizon if you use DevStack.
2. There might be some file conflicts in foloder horizon/openstack_dashboard/enabled if you created your own panels before, so you need to change the file name in order to resolve the conflict.

3. Restart the apache2 service to make these changes take effect.

4. Then visit horizon dashboard, you will find a new panel named "PTAS".

