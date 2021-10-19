import subprocess
import shlex
import configparser

from modules.util import *

config = configparser.ConfigParser()
config.read('config.ini')

dir = config['general']['peering_testbed_dir']
ptb_asn = config['general']['ptb_asn']

if dir[-1] != "/":
    dir = dir+"/"


def announce_prefix(prefix):
    cmd = 'sudo ' + dir + 'peering prefix announce -m ' + config['general']['mux'] + ' ' + prefix
    log("announce_prefix", "DEBUG", cmd)
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    proc.communicate()  # Fetching result


def withdraw_prefix(prefix):
    cmd = 'sudo ' + dir + 'peering prefix withdraw -m ' + config['general']['mux'] + ' ' + prefix
    log("withdraw_prefix", "DEBUG", cmd)
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    proc.communicate()  # Fetching result


def announce_poisoned_prefix(prefix, asn):
    if len(asn) == 2 and type(asn) is list:
        poison = " -p " + str(asn[0]) + " -p " + str(ptb_asn) + " -p " + str(asn[1]) + " -p " + str(ptb_asn)
    elif len(asn) == 1 and type(asn) is list:
        poison = asn[0]
    else:
        log("announce_poisoned_prefix", "DEBUG", "AS List must be of type list and of len 1 or 2, it currently is: " + str(asn))
        raise ListError("AS List must be of type list and of len 1 or 2")

    cmd = 'sudo ' + dir + 'peering prefix announce -m ' + config['general']['mux'] + poison + ' ' + prefix
    log("announce_poisoned_prefix", "DEBUG", cmd)
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    proc.communicate()  # Fetching result


def check_announce_v4(prefix):
    announced = bool(False)

    cmd = 'sudo ' + dir + 'peering bgp adv '+config['general']['mux']
    log("check_announce_v4", "DEBUG", cmd)
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result
    for line in out.decode().split('\n'):
        log("check_announce_v4", "DEBUG", line)
        if config['general']['debug'] == "True":
            print(line)
        if prefix in line:
            announced = bool(True)
            return announced
        else:
            continue

    return announced


def check_announce_v6(prefix):
    announced = bool(False)

    cmd = 'sudo ' + dir + 'peering bgp6 adv '+config['general']['mux']
    log("check_announce_v6", "DEBUG", cmd)
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result
    for line in out.decode().split('\n'):
        log("check_announce_v6", "DEBUG", line)
        if config['general']['debug'] == "True":
            print(line)
        if prefix in line:
            announced = bool(True)
            return announced
        else:
            continue

    return announced

