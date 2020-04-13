#!/bin/python3

# PortNanny
# Amith Mathew

# Usage
# portnanny daemon --config config.yaml
# portnanny interactive --port=303
# portnanny interactive --port=303 --kill


import psutil
import argparse
import logging
import sys
from pprint import pprint
import time
import yaml
import threading

DEFAULT_DAEMON_INTERVAL=30

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
    pass



def daemon_loop(configfile):
    interval = DEFAULT_DAEMON_INTERVAL # Default interval
    while True:
        with open(configfile, 'r') as fd:
            config = yaml.full_load(fd)
            interval = config['interval']
            logging.debug("Daemon interval is %d", interval)
            for i in config['ports']:
                logging.debug("Checking port %s", i['port'])
                proclist = get_procs(i['port'])
                logging.info("Total processes found listening on port %s: %s", i['port'], len(proclist))
                validproclist = [p for p in proclist if i['name'] in p['procpath']]
                logging.info("Valid processes found listening on port %s: %s", i['port'], len(validproclist))
                if len(validproclist) == 0:
                    if len(proclist) <> 0:
                        if i['kill'] is True:
                            logging.debug("Kill action is True, and non-valid processes exist.")
                            kill_processes(proclist)
                            logging.info("Non-valid processes killed. Running the provided command-line.")
                            logging.debug("Commandline is %s", i'[commandline'])
                            restart_process(i)
                        else:
                            logging.info("Kill action is False, but non-valid processes exist.")
                            logging.info("Logging and moving on.")
                    else:
                        logging.info("Restarting process.")
                        logging.debug("Commandline is %s", i['commandline'])
                        restart_process(i)
                else:
                    logging.info("Found %s valid processes running on port %s", len(validprocs), i['port'])
                    logging.debug("Valid processes are %s", validprocs)
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
