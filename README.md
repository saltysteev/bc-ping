# bc-ping
A self hosted ping monitoring script to check status of remote hosts/ip with a status page

## overview
I was looking for just a simple up/down ping monitor that tells me if it's up or down and some timestamps. Either they were too expensive, or too loaded with unnecessary features. I couldn't believe some companies are charging $50-$100 **a month** to just check the uptime of just a handfull of hosts. So I starting writing this and now my company uses it as our daily ping monitor.

Simply, what it does is do a heartbeat (ICMP ping) to a host IP (or domain) and displays the results it in a Bootstrap styled status page. It tells you how long it's been either online, or offline, and also reports how long a host was down in an event log.

## requirements
You can use PIP and and the requirements.txt file
`pip install -r requirements.txt`

Or manually install the required modules `pythonping` and `dicttoxml`.

## running the monitor
Simply run `ping.py`. It was developed to run as a service so it doesn't have any console output, you can use NSSM for setting this up.
It will output the results as an XML file to wherever it is determined in the INI. 

## config file
The `config.ini` file included holds directory information as well as the interval. You can change this to match your environment.

## status page
Everything in the www directory works on a self hosted environment, but be warned it will not work with the file:// protocol. 
