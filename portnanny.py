#!/bin/python3

# PortNanny - Nanny those ports like you mean it.
# Author: Amith Mathew, 2020.


import psutil
import argparse
import logging
import sys
from pprint import pprint
import time
import yaml
import subprocess
import shlex

DEFAULT_DAEMON_INTERVAL=30
MAX_PROCESSES=5 # Thread pool size to kill/restart processes.
PROC_STATUS_CHECK_CYCLES=1 # Number of cycles to keep checking output of process before failing. Set to arbitrarily high value to never retry.

def get_procs(port):
    ns = psutil.net_connections()
    n_list=[n for n in ns if n.laddr.port==port]
    logging.debug("net_connections list is %s", n_list)
    proclist = []
    for n in n_list:
        procdict = {}
        p = psutil.Process(n.pid)
        logging.debug('Processing %s', n)
        with p.oneshot():
            logging.debug('Process detail is %s', p)
            procdict['procname'] = p.name()
            procdict['pid']=n.pid if hasattr(n, 'pid') else None
            procdict['procpath']=p.exe()
            procdict['proccmdline']=p.cmdline()
            procdict['started']=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.create_time()))
            procdict['procstatus']=p.status()
            procdict['procuser']=p.username()
            procdict['connstatus']=n.status if hasattr(n, 'status') else None
            if hasattr(n, 'laddr'):
                procdict['listenaddr']=n.laddr.ip if hasattr(n.laddr, 'ip')  else None
            else:
                procdict['listenaddr']=None
            if hasattr(n, 'raddr'):
                procdict['remoteaddr']=n.raddr.ip if hasattr(n.raddr, 'ip') else None
                procdict['remoteport']=n.raddr.port if hasattr(n.raddr, 'port') else None
            else:
                procdict['remoteaddr'] = procdict['reportport'] = None
        proclist.append(procdict)
    logging.debug("Final proclist is %s", proclist)
    return proclist


def kill_processes(processlist):
    pass

def restart_process(config):
    logging.info("Running command line: %s", config['cmdline'])
    cmdargs = shlex.split(config['cmdline'])
    restart_call = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if restart_call.poll() is None:
        return restart_call
    else:
        logging.info("Execution complete. Output is %s", restart_call.stdout.read())
        logging.info("Error is %s", restart_call.stderr.read())
    return None


def daemon_loop(configfile):
    restart_pending_dict = {}
    while True:
        logging.debug("Restart Pending List is %s", restart_pending_dict)
        with open(configfile, 'r') as fd:
            config = yaml.full_load(fd)
            if 'interval' in config.keys():
                interval = config['interval']
            else:
                interval = DEFAULT_DAEMON_INTERVAL # Default interval
            if 'statuscheckcyclecount' in config.keys():
                proc_status_cycles = config['statuscheckcyclecount']
            else:
                proc_status_cycles = PROC_STATUS_CHECK_CYCLES # Default cycle count.
            logging.debug("Daemon interval is %d", interval)
            for i in config['ports']:
                logging.debug("Validating entry.")
                if type(i) is not dict or (not all(p in i.keys() for p in ['port', 'name', 'cmdline'])):
                    logging.warning("The following entry is missing one of the following keys - port, name, cmdline.")
                    logging.warning("The entry is: %s", i)
                    continue
                logging.debug("Checking port %s", i['port'])
                proclist = get_procs(i['port'])
                logging.info("Total processes found listening on port %s: %s", i['port'], len(proclist))
                validproclist = [p for p in proclist if i['name'] in p['procpath']]
                logging.info("Valid processes found listening on port %s: %s", i['port'], len(validproclist))


                if len(validproclist) == 0:
                    if i['port'] not in restart_pending_dict.keys():
                        if len(proclist) != 0:
                            if 'kill' in i.keys():
                                killflag = i['kill']
                            else:
                                killflag = False
                            if killflag is True:
                                logging.debug("Kill action is True, and non-valid processes exist.")
                                kill_processes(proclist)
                                logging.info("Non-valid processes killed. Running the provided command-line.")
                                logging.debug("Commandline is %s", i['cmdline'])
                                subprocess_d = restart_process(i)
                                if subprocess_d is not None:
                                    restart_pending_dict[i['port']] = { "spd": subprocess_d, "cyclecount": 0}
                            else: # i['kill']
                                logging.info("Kill action is False, but non-valid processes exist.")
                                logging.info("Logging and moving on.")
                        else: # len(proclist)
                            logging.info("Restarting process.")
                            logging.debug("Commandline is %s", i['cmdline'])
                            subprocess_d = restart_process(i)
                            if subprocess_d is not None:
                                restart_pending_dict[i['port']] = { "spd": subprocess_d, "cyclecount": 0}

                    else: # port in restart_pending_dict.keys()
                        d = restart_pending_dict[i['port']]
                        # Check if process completed.
                        if d['spd'].poll() is None:
                            if d['cyclecount']+1 > proc_status_cycles:
                                logging.warning("Restart for port %d did not complete within %d cycles. Aborting.", i['port'], proc_status_cycles)
                                del restart_pending_dict[i['port']]
                            else:
                                logging.info("Restart for port %d not yet complete this cycle.", i['port'])
                                restart_pending_dict[i['port']]['cyclecount'] = restart_pending_dict[i['port']]['cyclecount'] + 1
                        else:
                            logging.info("Execution complete. Return Code is %d. Output is %s", d['spd'].poll(), d['spd'].stdout.read())
                            logging.info("Error is %s", d['spd'].stderr.read())
                            del restart_pending_dict[i['port']]
                else: # len(validproclist)
                    logging.info("Found %s valid processes running on port %s", len(validproclist), i['port'])
                    logging.debug("Valid processes are %s", validproclist)
        logging.debug("Sleeping for %d seconds.\n\n", interval)
        time.sleep(interval)



def main():
    # ArgParse configuration
    parser = argparse.ArgumentParser(prog="portnanny",
                                     description="Port Nanny"
                                     )

    subparsers = parser.add_subparsers(help="portnanny can be run interactively, or in daemon mode.", dest="mode")

    daemon_parser = subparsers.add_parser("daemon", help="Daemon mode.")
    inter_parser = subparsers.add_parser("interactive", help="Interactive mode")



    # Global Args
    parser.add_argument('--loglevel', '-l',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log Level.",
                        action="store",
                        default="INFO"
    )

    # Daemon Args
    daemon_parser.add_argument('--config', '-c',
                        help="Path to configuration file.",
                        action="store",
                        required=True,
    )


    # Interactive Args
    inter_parser.add_argument('--port', '-p',
                        help="Port to check, if not using a configuration file.",
                        action="store",
                        required=True,
                        type=int
    )

    args = parser.parse_args()

    # Logging Configuration.
    LOGLEVEL = args.loglevel
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(processName)-8s - %(funcName)-12s - %(levelname)-8s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(LOGLEVEL)


    logging.debug("Received args: %s", args)

    if args.mode=="interactive":
        logging.debug("Interactive mode. Checking port %d", args.port)
        proclist = get_procs(args.port)
        if proclist != []:
            pprint(proclist)
        else:
            logging.info("Port %s is not in use.", args.port)
    elif args.mode=="daemon":
        logging.info("portnanny starting in Daemon mode.")
        logging.info("Processing configuration file %s", args.config)
        config = yaml.full_load(args.config)
        daemon_loop(args.config)




if __name__ == "__main__":
    main()
