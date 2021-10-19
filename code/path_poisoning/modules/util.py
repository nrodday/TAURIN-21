import smtplib
from csv import DictReader

import requests
import json
import subprocess
import shlex
import pickle
import re
import socket
import binascii
import ipaddress
import struct
import logging
import time
import configparser
import random

config = configparser.ConfigParser()
config.read('config.ini')

logfile = "log/bush_" + str(int(time.time())) + ".log"
logging.basicConfig(filename=logfile, format="%(levelname)s %(asctime)s: %(message)s", datefmt='%m/%d/%Y %H:%M:%S')
logging.getLogger().setLevel(config['general']['logging'])
logger = logging.getLogger("log")


class ListFullError(Exception):
    pass


class PrefixError(Exception):
    pass


class AnnounceError(Exception):
    pass


class ListError(Exception):
    pass


class Breakpoint1(Exception):
    pass


class Breakpoint2(Exception):
    pass


class MeasurementError(Exception):
    pass


class TunnelError(Exception):
    pass


def checksudo():
    cmd = "sudo -l"
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result

    rights = bool(False)

    for line in out.decode().split('\n'):
        if "NOPASSWD: ALL" in line:
            rights = bool(True)
        else:
            continue

    return rights


# I know, pretty weak check of installation, but if I use specific commands like apt, this script would only
# be available to debian users. At least it helps most of the time. In other cases an exception would be thrown anyway.
def checkzmap():
    cmd = "sudo zmap -h"
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result

    installed = bool(False)

    for line in out.decode().split('\n'):
        if "command not found" in line:
            installed = bool(False)
        else:
            installed = bool(True)

    return installed


def checktunnel():
    status = bool(False)
    iface = config['general']['interface']
    mac = config['general']['gateway_mac']

    cmd = "ip neigh"
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result

    for line in out.decode().split('\n'):
        if "REACHABLE" in line and iface in line and mac in line:
            status = bool(True)

    return status


def createhitlist(version, fresh):
    try:
        if fresh == "True" or fresh == "true":
            if version == 4:
                hitlist_v4 = parse_ant_v4()
                pickle.dump(hitlist_v4, open("data/hitlist_v4.p", "wb"))
            elif version == 6:
                hitlist_v6 = set(line.strip() for line in open('data/hitlist_v6.txt'))
                pickle.dump(hitlist_v6, open("data/hitlist_v6.p", "wb"))
    except PermissionError:
        print("Something went wrong!")
        pass

    #Todo Download fresh hitlist if too old or not existing and dump it to filesystem
    hitlist = pickle.load(open("data/hitlist_v" + str(version) + ".p", "rb"))

    return hitlist


def parse_ant_v4():
    hitlist = dict()
    filename1 = "internet_address_verfploeter_hitlist_it91w-20200710.fsdb"
    filename2 = "internet_address_hitlist_it91w-20200710.fsdb"

    try:
        file1 = set(line.strip() for line in open('tmp/' + filename1))

        for line in file1:
            regex = "(\S+)\t(\S{2,})"

            content = re.findall(regex, line)

            if len(content) > 0:
                print(content)
                for x in content:
                    network = x[0]

                    hostlist = x[1].split(",")
                    # print(hostlist)
                    # print(network)

                    hitlist[network] = hostlist

        del file1

        file2 = set(line.strip() for line in open('tmp/' + filename2))

        for line in file2:
            regex = "(\S+)\t"
            content = re.findall(regex, line)
            if len(content) > 0:
                print(content)
                host = content[0][-2:]
                net = content[0][0:6] + "00"
                if net in hitlist:
                    if host not in hitlist[net]:
                        hitlist[net].append(host)
                else:
                    hitlist[net] = [host]

        del file2

        with open('tmp/hitlist_v4.txt', 'w') as file:
            for line in hitlist:
                file.write(str(line) + " : " + str(hitlist[line]) + '\n')

        pickle.dump(hitlist, open("data/hitlist_v4.p", "wb"))

    except PermissionError:
        pass

    return hitlist


def ripeaslist(write=False):
    aslist = []
    next = "https://atlas.ripe.net/api/v2/probes/?format=json"
    # next = "https://atlas.ripe.net/api/v2/probes/?format=json&page=333"
    while next is not None:
        try:
            with requests.get(next, timeout=600) as request:
                if request.status_code == 200:
                    data = json.loads(request.content.decode('utf-8'))
                    next = data['next']
                    print(next)

                    for result in data['results']:
                        if result['asn_v4'] not in aslist and isinstance(result['asn_v4'], int):
                            # print(result['asn_v4'])
                            aslist.append(result['asn_v4'])
                        if result['asn_v6'] not in aslist and isinstance(result['asn_v6'], int):
                            # print(result['asn_v6'])
                            aslist.append(result['asn_v6'])
                else:
                    raise requests.exceptions.ConnectionError("Could not connect to atlas.ripe.net!")
        except requests.exceptions.ConnectionError:
            print("Could not connect to stat.ripe.net!")

        if write:
            try:
                with open('data/aslist.txt', 'w') as file:
                    for asn in aslist:
                        file.write(str(asn) + '\n')
            except FileNotFoundError as error:
                quit("File cant be found because of " + str(error))

    return aslist


def log(function="bush", level="DEBUG", message="message"):
    logger.setLevel(level)
    if isinstance(level, int):
        lvl = level
    elif isinstance(level, str):
        lvl = getattr(logging, level)
    else:
        lvl = level

    msg = str(function) + ": " + str(message)
    print(msg)
    logger.log(level=lvl, msg=msg)


def checkRelation(as1, as2):
    try:
        relations = pickle.load(open("data/relations.p", "rb"))
    except FileNotFoundError:
        print("Creating new relationship dictionary!")
        relations = dict()

        filedir = config['general']['tiermeta']
        new_filename = "tierlist_" + filedir.split('serial-2/')[1].split('.')[0]

        with open('data/' + new_filename + '.csv', "r", newline='') as result_csv:
            csv_dict_reader = DictReader(result_csv)

            for row in csv_dict_reader:
                provider = row['provider']
                customer = row['customer']

                if provider not in relations:
                    relations[provider] = list()
                    relations[provider].append(customer)
                elif customer not in relations[provider]:
                    relations[provider].append(customer)

                if customer not in relations:
                    relations[customer] = list()
                    relations[customer].append(provider)
                elif provider not in relations[customer]:
                    relations[customer].append(provider)

        pickle.dump(relations, open("data/relations.p", "wb"))

    relationship = bool(False)

    try:
        if str(as1) in relations[str(as2)] or str(as2) in relations[str(as1)]:
            relationship = bool(True)
    except KeyError:
        log("bushetal.py", "DEBUG", "checkRelation: " + "One of the ASs was not found in relationship source!")

    log("bushetal.py", "DEBUG", "checkRelation: " + str(as1) + "-" + str(as2) + ": " + str(relationship))
    return relationship


def messageoperator(error):
    gmail_user = config['general']['gmail_user']
    gmail_password = config['general']['gmail_password']

    sent_from = gmail_user
    to = config['general']['operators'].split(",")
    subject = 'DR Measurement Notification'
    body = "Something went wrong during the measurement! \n\nErrormessage: " + error

    email_text = 'Subject: {}\n\n{}'.format(subject, body)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except ValueError:
        print('Something went wrong...')