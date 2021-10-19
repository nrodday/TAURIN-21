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

'''# Connect
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# pkey_file = paramiko.RSAKey.from_private_key_file("/home/luke/.ssh/nlnog", "nlnog")
pkey_file = "/home/luke/.ssh/nlnog"
#client.connect("coloclue01.ring.nlnog.net", 22, "rgnet", pkey="~/.ssh/nlnog", passphrase="nlnog", allow_agent=True)
client.connect("coloclue01.ring.nlnog.net", username="rgnet", key_filename=pkey_file, passphrase="nlnog")

command1 = "env > env_output"
command2 = "cat trcrt_paramikotest_2"
command3 = "traceroute 184.164.235.1 -A -m 32 -I"

#stdin, stdout, stderr = client.exec_command(command3)

#print(str(stdout))


sleeptime = 0.001
outdata, errdata = '', ''
ssh_transp = client.get_transport()
chan = ssh_transp.open_session()
# chan.settimeout(3 * 60 * 60)
chan.setblocking(0)

paramiko.agent.AgentRequestHandler(chan)
chan.get_pty()

chan.exec_command(command2)
while True:  # monitoring process
    # Reading from output streams
    while chan.recv_ready():
        outdata += str(chan.recv(1000))
    while chan.recv_stderr_ready():
        errdata += str(chan.recv_stderr(1000))
    if chan.exit_status_ready():  # If completed
        break
    time.sleep(sleeptime)
retcode = chan.recv_exit_status()
ssh_transp.close()

print(outdata)
print(errdata)'''

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
            '''
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
            hop = re.search(r'\d+', line).group()

            trcrt_set["result"][res_cnt] = {}
            trcrt_set["result"][res_cnt]["hop"] = hop

            query_cnt = 0
            trcrt_set["result"][res_cnt]["result"] = {}
            #print("\n")
            #print("Line: " + str(line))
            ip_rtt = re.findall(r'\((\d+.\d+.\d+.\d+)\)((?:\s*(?:\d+.\d+ ms))+)', line)

            #print("RTT: " + str(ip_rtt))
            for hit in ip_rtt:
                #print("RTT-GR: " + str(hit))
                #print("Gruppe: " + str(hit[0]))
                rtt = re.findall(r'(\d+.\d+)', hit[1])
                for ms in rtt:
                    trcrt_set["result"][res_cnt]["result"][query_cnt] = {}
                    trcrt_set["result"][res_cnt]["result"][query_cnt]["from"] = hit[0]
                    trcrt_set["result"][res_cnt]["result"][query_cnt]["rtt"] = ms
                    query_cnt = query_cnt + 1
                    #print("MS: " + ms)

            nores = re.findall(r'\*', line)
            for hit2 in nores:
                #print("No Result")
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
    return trcrt_set



try:
    # nlnogmeta = open('data/nlnogmeta.json')
    nlnogmeta = open('data/nlnogmeta_short.json')
except:
    print("Could not open nlnogmeta.json, downloading new one")
    #getNlnogMeta()
    # nlnogmeta = open('data/nlnogmeta.json')
    nlnogmeta = open('data/nlnogmeta_short.json')

nodes = json.load(nlnogmeta)



''' Teststuff of multiprocessing
def lookitup(nodename):
    cmd='dig '+nodename  # Preparing the command
    proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)  # Executing
    out,err=proc.communicate()  # Fetching result
    return out

starttime = datetime.now()
with Pool(processes=4) as p:
    m = mp.Manager()
    results = p.map(lookitup, nodes)
# clean up once all tasks are done
p.close()
p.join()
print("Multi: "+str(datetime.now()-starttime))

starttime2 = datetime.now()
for node in nodes:
    starttime = datetime.now()
    out = lookitup(node)
    print(out)

print("For: "+str(datetime.now()-starttime2))


print(results)

exit()

'''

starttime1 = datetime.now()
with Pool(mp.cpu_count()) as p:
    m = mp.Manager()
    results = p.map(runTrcrt, nodes)
# clean up once all tasks are done
p.close()
p.join()

msm_mp = {}
count = 0
for result in results:
    msm_mp[count] = result
    count = count + 1

with open('data/nlnog_msm_mp.json', 'w') as f:
    json.dump(msm_mp, f)
    f.close()

endtime1 = datetime.now()
print("Done! Wrote measurement information of "+str(count)+" ring nodes into data/nlnog_msm_mp.json")



''' For Loop, durch Multithreading ersetzt
msm_for = {}
starttime2 = datetime.now()
count = 0
for node in nodes:
    #print(node)
    count = count + 1
    trcrt_set, trcrt_arr = runTrcrt(node)
    msm_for[count] = trcrt_set
    # Above 2 lines print the traceroute stuff in beautfiul output
    #for line in trcrt_arr:
    #    print(line)

with open('data/nlnog_msm_for.json', 'w') as f:
    json.dump(msm_for, f)
    f.close()

endtime2 = datetime.now()
print("Done! Wrote measurement information of "+str(count)+" ring nodes into data/nlnog_msm_for.json")
print("For-Schleife: "+str(endtime2-starttime2))
'''
print("Multiprocess: "+str(endtime1-starttime1))
