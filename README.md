# PtasHorizon
plugin panels for Horizon dashboard to do sever level monitoring, and reporting leveraging the OpenStack Ceilometer with Intel PTAS meters

###Instructions
Make sure you have run the Ceilometer IPMI agent on each of your physical nodes:<br/>
./ceilometer-agent-ipmi &

<br/>
The panels are based on horizon panels, so please make sure you have read this horizon doc, and understand the mechanism:
http://docs.openstack.org/developer/horizon/topics/tutorial.html

### Install
Copy the files under horizon directory into your server's horizon folder, the path is /opt/stack/horizon if you use DevStack.
There might be some file conflicts in foloder horizon/openstack_dashboard/enabled if you created your own panels before, so you need to change the file name in order to resolve the conflict.

Restart the apache2 service to make these changes take effect.

Then visit horizon dashboard, you will find a new panel named "PTAS".

