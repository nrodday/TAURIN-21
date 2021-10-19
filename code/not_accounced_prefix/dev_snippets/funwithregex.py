from datetime import datetime
import shlex
import subprocess

import paramiko
import time
import configparser
import os
import json
import re
#from hlavacek_nlnog import getNlnogMeta
import multiprocessing as mp
from multiprocessing import Pool, Manager, Process

##############################################################
# Reading from the Config File
config = configparser.ConfigParser()
config.read('config.ini')

def runTrcrt(hostname):
    trcrt_set = {}
    trcrt_set["timestamp"] = str(int(time.time()))
    # Connect
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Locate private key file
    pkey_file = open(os.path.expanduser(config['nlnog.account']['pkey_file']))
    pkey = paramiko.RSAKey.from_private_key(pkey_file, "nlnog")

    # Connect to remote host
    client.connect(hostname, username="rgnet", pkey=pkey)

    # Prepare Command
    epoch_time = int(time.time())
    filename = 'trcrt_' + str(epoch_time) + '.txt'

    # check which protocol should be used and determine parameter
    if config['nlnog.traceroute']['protocol'] == "icmp_echoscan":
        trcrttype = "-I"
    else:
        trcrttype = ""

    command = 'traceroute ' + config['nlnog.traceroute']['target'] + " -m " + config['nlnog.traceroute']['max_hops'] + " " + trcrttype

    print("Command to be executed on "+ hostname +": " + command)

    sleeptime = 0.001
    outdata, errdata = b'', b''
    ssh_transp = client.get_transport()
    chan = ssh_transp.open_session()
    # chan.settimeout(3 * 60 * 60)
    chan.setblocking(0)

    chan.exec_command(command)
    while True:  # monitoring process
        # Reading from output streams
        while chan.recv_ready():
            outdata += chan.recv(1000) #.decode('UTF-8')
        while chan.recv_stderr_ready():
            errdata += chan.recv_stderr(1000) #.decode('UTF-8')
        if chan.exit_status_ready():  # If completed
            break
        time.sleep(sleeptime)
    retcode = chan.recv_exit_status()
    ssh_transp.close()

    # print(outdata)
    # print(errdata)

    out_raw = outdata.decode('UTF-8')
    trcrt_arr = outdata.decode('UTF-8').splitlines()

    trcrt_set["fw"] = "?"
    trcrt_set["mver"] = "?"
    trcrt_set["lts"] = "?"
    trcrt_set["endtime"] = str(int(time.time()))
    trcrt_set["dst_name"] = config['nlnog.traceroute']['target']
    trcrt_set["dst_addr"] = config['nlnog.traceroute']['target']
    trcrt_set["src_addr"] = "?"
    trcrt_set["proto"] = config['nlnog.traceroute']['protocol']
    trcrt_set["proto"] = config['nlnog.traceroute']['af']
    trcrt_set["size"] = "?"
    trcrt_set["paris_id"] = "?"

    trcrt_set["result"] = {}

    res_cnt = 0
    for line in trcrt_arr:
        if "traceroute" in line:
            '''
            ip = line.split('(')[1].split(')')[0]
            hop = 0
            trcrt_set[hop] = ip
            trcrt_set["src_addr"] = ip
            '''
            pass
        else:
            hop = re.search(r'\d+', line).group()

            trcrt_set["result"][res_cnt] = {}
            trcrt_set["result"][res_cnt]["hop"] = hop

            rtt = re.findall(r'(\d+.\d+) ms', line)
            query_cnt = 0
            trcrt_set["result"][res_cnt]["result"] = {}

            for query in rtt:
                trcrt_set["result"][res_cnt]["result"][query_cnt] = {}
                trcrt_set["result"][res_cnt]["result"][query_cnt]["from"] = hostname
                trcrt_set["result"][res_cnt]["result"][query_cnt]["rtt"] = query
                query_cnt = query_cnt + 1

            for x in range(int(config['nlnog.traceroute']['query_count'])-len(rtt)):
                trcrt_set["result"][res_cnt]["result"][query_cnt] = {}
                trcrt_set["result"][res_cnt]["result"][query_cnt]["x"] = "*"
                query_cnt = query_cnt + 1





        '''
        elif "(" in line:
            ip = line.split('(')[1].split(')')[0]
            hop = re.search(r'\d+', line).group()
            trcrt_set["result"][res_cnt]["hop"] = hop

        elif "*" in line:
            hop = re.search(r'\d+', line).group()
            trcrt_set[hop] = "*"
        '''
        res_cnt = res_cnt + 1

    trcrt_set["msm_id"] = "?"
    trcrt_set["prb_id"] = hostname
    trcrt_set["msm_name"] = "?"
    trcrt_set["from"] = hostname
    trcrt_set["type"] = "traceroute"
    trcrt_set["group_id"] = "?"
    trcrt_set["stored_timestamp"] = str(int(time.time()))
    # return trcrt_set, out_raw
    return trcrt_set, trcrt_arr
'''
try:
    # nlnogmeta = open('data/nlnogmeta.json')
    trcrt_arr = open('data/funwithregexdump')

except:
    trcrt_set, trcrt_arr = runTrcrt("cesnet01.ring.nlnog.net")

    with open('data/funwithregexdump', 'w') as f:
        json.dump(trcrt_arr, f)
        f.close()
'''
file1 = open('data/traceexample.txt', 'r')
trcrt_arr = file1.readlines()

#trcrt_set, trcrt_arr = runTrcrt("worldstream01.ring.nlnog.net")
print(trcrt_arr)

for line in trcrt_arr:
    print("\n")
    print("Line: "+str(line))
    ip_rtt = re.findall(r'\((\d+.\d+.\d+.\d+)\)((?:\s*(?:\d+.\d+ ms))+)', line)

    print("RTT: "+str(ip_rtt))
    for hit in ip_rtt:
        print("RTT-GR: " + str(hit))
        #print("Gruppe: "+str(hit.group(1))+" "+str(hit.group(2)))
        print("Gruppe: " + str(hit[0]))
        rtt = re.findall(r'(\d+.\d+)', hit[1])
        for ms in rtt:
            print("MS: "+ms)

    nores = re.findall(r'\*', line)
    for hit2 in nores:
        print("No Result")



