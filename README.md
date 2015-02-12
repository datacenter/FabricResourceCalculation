Fabric Resource Calculation
====================

To calculation the resource per fabric node

#Installation:
Install the ACI SDK acicobra-1.0.1_0e-py2.7.egg.
Here is the documentation for the ACI SDK package:
https://developer.cisco.com/media/apicDcPythonAPI_v0.1/install.html

#How to use:

All the codes support three different input methods: wizard, yaml and cli.

1. wizard: configure a mo by following a wizard. Usage: 
<br>python policyTCAM.py wizard
<br>To get the help info: python policyTCAM.py wizard –h

2. yaml: configure a mo with a config file (yaml format). Usage:
<br>python policyTCAM.py yaml policyTCAM.yaml
<br>To get the help info: python policyTCAM.py yaml –h
<br>There is a sample of yaml file. Please check out the argument format from the sample yaml file.

3. cli: configure a mo based on you python arguments.  It contains key arguments and optional arguments. Flags are used in order to call the optional arguments. Usage:
<br>python policyTCAM.py cli 172.31.216.100 admin ins3965! -n 101 102 -t '5 mins' 
<br>To get the help info: python policyTCAM.py cli –h


#What are those codes:
createMo.py: the basic class/module. It also contains useful functions that help programmers for writing their customized scripts.

