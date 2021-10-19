from datetime import datetime
import os
import paramiko
import json
import time
import configparser
import re
import random
import socket
from functools import partial

from socket import timeout

import multiprocessing as mp
from multiprocessing import Pool
from multiprocessing import get_context

from modules.evaluation import (
    prepare,
    evaluate,
    evaluate2,
    summarize
)

from modules.resolveasn import (
    loadNlnogMeta
)

from modules.archive import archive

# This is maybe the fix for random EOFError
'''import logging
from logging import NullHandler
logging.getLogger('paramiko.transport').addHandler(NullHandler())'''

startTime = datetime.now()

##############################################################
# Reading from the Config File
config = configparser.ConfigParser()
config.read('config.ini')

##############################################################
# Functions for later use


def runTrcrt(command, target, af, msm_id, protocol, hostname):
    trcrt_set = {}

    try:
        # Connect
        if config['general']['debug'] == "True":
            print(hostname + ": Creating Socket with bind")
        # Create socket for correct bind
        source_ip = config['nlnog']['source_ip']
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((source_ip, 0))
        sock.connect((hostname, 22))

        if config['general']['debug'] == "True":
            print(hostname + ": opening client")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if config['general']['debug'] == "True":
            print(hostname + ": configuring ssh key")
        # Locate private key file
        pkey_file = open(os.path.expanduser(config['nlnog']['pkey_file']))
        pkey = paramiko.RSAKey.from_private_key(pkey_file, "nlnog")

        if config['general']['debug'] == "True":
            print(hostname + ": Connecting")
        # Connect to remote host
        client.connect(hostname, username="rgnet", pkey=pkey, timeout=180, sock=sock)

        if config['general']['debug'] == "True":
            print(hostname + ": Connected, command to be executed: " + command)

        sleeptime = 0.001
        outdata, errdata = b'', b''
        try:
            if config['general']['debug'] == "True":
                print(hostname + ": opening ssh_transp")
            ssh_transp = client.get_transport()
            if config['general']['debug'] == "True":
                print(hostname + ": opening session channel")
            chan = ssh_transp.open_session()
            chan.settimeout(900)
            # 15 minutes
            # chan.setblocking(0)
            trcrt_set["timestamp"] = str(int(time.time()))
            if config['general']['debug'] == "True":
                print(hostname + ": executing command")
            chan.exec_command(command)
            if config['general']['debug'] == "True":
                print(hostname + ": waiting for output")

            timer = 0
            while timer < 900:  # monitoring process
                # Reading from output streams
                while chan.recv_ready():
                    outdata += chan.recv(1000) #.decode('UTF-8')
                while chan.recv_stderr_ready():
                    errdata += chan.recv_stderr(1000) #.decode('UTF-8')
                if chan.exit_status_ready():  # If completed
                    break

                timer = timer + sleeptime
                time.sleep(sleeptime)

            if timer == 900:
                print(hostname + ": Timeout while waiting for output!")

            if config['general']['debug'] == "True":
                print(hostname + ": received output")
            out_raw = outdata.decode('UTF-8')
            trcrt_arr = outdata.decode('UTF-8').splitlines()

            trcrt_set["fw"] = "?"
            trcrt_set["mver"] = "?"
            trcrt_set["lts"] = "?"
            trcrt_set["endtime"] = int(time.time())
            trcrt_set["dst_name"] = target
            trcrt_set["dst_addr"] = target
            trcrt_set["src_addr"] = "?"
            trcrt_set["proto"] = protocol
            trcrt_set["af"] = int(af)
            trcrt_set["size"] = "?"
            trcrt_set["paris_id"] = "?"

            trcrt_set["result"] = []

            for line in trcrt_arr:
                if "traceroute" in line:
                    pass

                else:
                    # hop = re.search(r'\n\s(\d+)', line).group()
                    hop = int(re.search(r'\d+', line).group())
                    lineres = {}
                    lineres["hop"] = hop
                    lineres["result"] = []
                    if int(af) == 4:
                        # ip_rtt = re.findall(r'\((\d+.\d+.\d+.\d+)\)((?:\s*(?:!H)*(?:!N)*(?:!P)*(?:!S)*(?:!F)*(?:!X)*(?:!V)*(?:!C)*\s*(?:\d+.\d+ ms))+)', line)
                        ip_rtt = re.findall(
                            r'\((\S*)\)((?:\s*(?:!H)*(?:!N)*(?:!P)*(?:!S)*(?:!F)*(?:!X)*(?:!V)*(?:!C)*\s*(?:\d+.\d+ ms))+)',
                            line)
                    elif int(af) == 6:
                        ip_rtt = re.findall(
                            r'\((\S*)\)((?:\s*(?:!H)*(?:!N)*(?:!P)*(?:!S)*(?:!F)*(?:!X)*(?:!V)*(?:!C)*\s*(?:\d+.\d+ ms))+)',
                            line)

                    else:
                        exit("Wrong IP Version, cant read traceroute")

                    for hit in ip_rtt:
                        rtt = re.findall(r'(\d+.\d+)', hit[1])
                        for ms in rtt:
                            ms_set = {}
                            ms_set["from"] = hit[0]
                            ms_set["rtt"] = ms
                            lineres["result"].append(ms_set)

                    nores = re.findall(r'\*', line)
                    for hit2 in nores:
                        ms_set = {}
                        ms_set["x"] = "*"
                        lineres["result"].append(ms_set)

                    trcrt_set["result"].append(lineres)

            trcrt_set["msm_id"] = int(msm_id)
            trcrt_set["prb_id"] = hostname
            trcrt_set["msm_name"] = "?"
            trcrt_set["from"] = hostname
            trcrt_set["type"] = "traceroute"
            trcrt_set["group_id"] = "?"
            trcrt_set["stored_timestamp"] = str(int(time.time()))
            if config['general']['debug'] == "True":
                print(hostname + ": trcrt_set done")
        except timeout as error:
            if config['general']['debug'] == "True":
                print(hostname + ": Timeout: ran into timeout while waiting for output! Errormsg: " + str(error))
            else:
                pass
        finally:
            if config['general']['debug'] == "True":
                print(hostname + ": Closing ssh_transp")
            ssh_transp.close()
    except OSError as error:
        if config['general']['debug'] == "True":
            print(hostname + ": OSError: Could not connect to ring node, aborting! Errormsg: " + str(error))
        else:
            pass

    except EOFError as error:
        if config['general']['debug'] == "True":
            print(hostname + ": EOFError: Could not connect to ring node, aborting! Errormsg: " + str(error))
        else:
            pass

    except paramiko.ssh_exception.SSHException as error:
        if config['general']['debug'] == "True":
            print(hostname + ": SSHException: Could not connect to ring node, aborting! Errormsg: " + str(error))
        else:
            pass

    finally:
        try:
            if config['general']['debug'] == "True":
                print(hostname + ": Closing ssh client")
            client.close()
            sock.close()
            if config['general']['debug'] == "True":
                print(hostname + ": Connection closed!")
        except UnboundLocalError as error:
            print(hostname + ": UnboundLocalError: Could not close socket or client, is already closed! Errormsg: " + str(error))


    return trcrt_set


def run_nlnog(**kwargs):
    loadNlnogMeta()

    timestamp = kwargs.get('timestamp', time.time())

    # Command assembly
    # check which protocol should be used and determine parameter
    args = ""

    af = kwargs.get('af', config['traceroute']['af'])
    args = args + "-" + af

    protocol = kwargs.get('prococol', config['traceroute']['protocol'])
    args = args + " -M " + protocol
    port = kwargs.get('port', config['traceroute']['port'])
    if protocol == "TCP" or protocol == "UDP":
        args = args + " -p " + port
    args = args + " -q " + kwargs.get('packets', config['traceroute']['packets'])
    args = args + " -N " + kwargs.get('paris', config['traceroute']['paris'])
    args = args + " -f " + kwargs.get('first_hop', config['traceroute']['first_hop'])
    dont_fragment = kwargs.get('dont_fragment', config['traceroute']['dont_fragment'])
    if dont_fragment == "True" or dont_fragment == "true":
        args = args + " -F"
    args = args + " -m " + kwargs.get('max_hops', config['traceroute']['max_hops'])

    description = kwargs.get('description', config['traceroute']['description'])
    size = kwargs.get('packet_size', config['traceroute']['packet_size'])
    target = kwargs.get('target', config['traceroute']['target'])

    command = 'traceroute ' + args + ' ' + target + ' ' + size
    version = int(kwargs.get('af', config['traceroute']['af']))

    try:
        nlnogmeta = open('data/nlnogmeta.json')
        #nlnogmeta = open('data/nlnogmeta_short.json')

    except FileNotFoundError:
        if config['general']['debug'] == "True":
            print("Could not open nlnogmeta.json, downloading new one")
        loadNlnogMeta()
        nlnogmeta = open('data/nlnogmeta.json')
        #nlnogmeta = open('data/nlnogmeta_short.json')

    nlnogmeta = json.load(nlnogmeta)

    starttime1 = datetime.now()
    skip = kwargs.get('skip', config['nlnog']['skip'])

    if skip == "True" or skip == "true":
        msm_id = kwargs.get('msm_id', config['nlnog']['msm_id'])
        print("Skipped creation of new measurement! Using ID " + msm_id)

        filename = "nlnog_" + str(msm_id) + '.json'
        try:
            loadeddata = open('archive/'+filename)
            msm_mp = json.load(loadeddata)
        except FileNotFoundError:
            exit("Could not open old measurement file, aborting")

    else:
        msm_id = int(time.time())
        # Pick random nodes of requested count
        requested = kwargs.get('requested', config['nlnog']['requested'])

        if int(requested) < len(nlnogmeta) and int(requested) != 0:
            randomints = []

            while len(randomints) < int(requested):
                rand = random.randint(1, len(nlnogmeta))
                if rand in randomints:
                    pass
                else:
                    randomints.append(rand)

            nodelist = []
            counter = 1
            for node in nlnogmeta:
                if counter in randomints:
                    nodelist.append(node)
                    counter = counter + 1
                else:
                    counter = counter + 1
        else:
            if config['general']['debug'] == "True":
                print("More nodes requested than available or 0 for all!")
            nodelist = []
            for node in nlnogmeta:
                nodelist.append(node)

        if config['general']['debug'] == "True":
            print(nodelist)
            print("Node count: "+str(len(nodelist)))

        func = partial(runTrcrt, command, target, af, msm_id, protocol)

        proc_count = int(config['nlnog']['parallel'])

        with Pool(processes=proc_count) as p:
            results = p.map(func, nodelist, chunksize=1)
            # clean up once all tasks are done
            p.terminate()
            p.join()

        msm_mp = []

        for result in results:
            if len(result) > 0:
                msm_mp.append(result)
            else:
                pass

        # Storing file in archive
        archive("nlnog", target, msm_mp, command, msm_id, description, requested)

        print("Done! Wrote measurement information of ring nodes into data/nlnog_"+str(msm_id)+".json")

    probe_count, data = prepare(msm_mp, "nlnog", af)

    # If Debug is true
    if config['general']['debug'] == "True":
        # Test printing python dict in json look
        json_object = json.dumps(data, indent = 4)
        print(json_object)

    # evaluate the gathered information
    evaluate(data, msm_id, "nlnog", af, probe_count, timestamp)

    # Measurement Summary
    summarize(msm_id, "nlnog", startTime, probe_count)


    endtime1 = datetime.now()
    if config['general']['debug'] == "True":
        print("Multiprocess: "+str(endtime1-starttime1))

    return msm_id
