# Port Nanny
_Nanny those ports like you mean it._

## What does it do.
Port Nanny was written to monitor certain local ports, and make sure that the processes bound to those ports are the ones you want. If Port Nanny does not find the right process, or finds /no/ processes bound to the specified port, it can optionally kill any existing processes using that port and then run a user-specified command to startup the process you want.

`portnanny` can run in two modes -
* Interactive - where it lists all the processes it finds attached to a particular port specified on the command line. This is analogous to running netstat, and is nothing special, just an easy way for me to view port status.

* Daemon - where it requires a YAML configuration file, and runs continuously, monitoring and restarting port forwarding (or any other service or command really) as required.

## Background.
I have a bunch of services running on a VM in GCP. I would like these services (which include simple web pages served over HTTPS) to be accessible only from my home network. and no where else. I do not want to put in the effort to create a site-to-site VPN, and am instead using a service account and the gcloud command to forward a local port on a raspberry pi in my home network, to appropriate ports on the VM in GCP. Simple, cheap, and (I believe) secure.


## Command Line

### Base command

```
usage: portnanny [-h] [--loglevel {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
                 {daemon,interactive} ...

Port Nanny

positional arguments:
  {daemon,interactive}  portnanny can be run interactively, or in daemon mode.
    daemon              Daemon mode.
    interactive         Interactive mode

optional arguments:
  -h, --help            show this help message and exit
  --loglevel {CRITICAL,ERROR,WARNING,INFO,DEBUG}, -l {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Log Level.
```


### Interactive mode
```
usage: portnanny interactive [-h] --port PORT

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Port to check, if not using a configuration file.
```


### Daemon mode
```
usage: portnanny daemon [-h] --config CONFIG

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file.
```
