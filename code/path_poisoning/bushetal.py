import random
from datetime import datetime
from multiprocessing import Pool, Manager
import json
import time
import configparser
import pickle
import logging
import traceback

from modules.peeringtb import *

from modules.linkage import *

from modules.util import *

from modules.evaluation import *

from modules.store import *

config = configparser.ConfigParser()
config.read('config.ini')

# createhitlist(4, "True")
# createhitlist(6, "True")


# asn is list of min 1 max 2 asn
def measurement(asn):
    result = ""
    own_prefix_v4 = prv4.pop()
    own_prefix_v6 = prv6.pop()
    log("measurement", "DEBUG", "Beginning new measurement with Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn))
    try:
        if not checktunnel():
            log("measurement", "DEBUG", "Tunnel to MUX is not established, check the status of the tunnel!")
            raise TunnelError("Tunnel to MUX is not established, check the status of the tunnel!")
        # Todo 1
        # Todo Annoounce Prefix + wait(20min)
        if check_announce_v4(own_prefix_v4) == bool(True) or check_announce_v6(own_prefix_v6) == bool(True):
            raise AnnounceError("Prefix is already announced, can't announce it for this measurement!")
        else:
            announce_prefix(own_prefix_v4)
            announce_prefix(own_prefix_v6)

            log("measurement", "DEBUG", "Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn) + " on " + config['general']['mux'] + " announced. Waiting 20 minutes to let it be distributed.")
            if config['general']['debug'] == "True":
                print("Prefix "+str(own_prefix_v4)+" and "+str(own_prefix_v6)+" for AS "+str(asn)+" on " + config['general']['mux'] + " announced. Waiting 20 minutes to let it be distributed.")
            time.sleep(1200)  # wait 20 min

        # Todo 2.1
        # Todo Create alive host list
        alivehosts = {}
        for nr in asn:
            alivehosts[nr] = {}
            prefv4, prefv6 = getprefixes(nr)
            log("measurement", "DEBUG","Prefixes for AS" + str(nr) + " :" + str(prefv4) + str(prefv6))
            if len(prefv4) > 0:
                log("measurement", "DEBUG", "Searching alive v4 hosts for AS" + str(nr))
                alivehosts[nr]["v4"] = getalivehosts_v4(prefv4, own_prefix_v4, hitlist_v4, int(config['zmap']['max_hosts']))
            else:
                alivehosts[nr]["v4"] = []
                log("measurement", "DEBUG", "Skipping alive host search, AS has no v4 prefixes: AS" + str(nr))
                if config['general']['debug'] == "True":
                    print("Skipping alive host search, AS has no v4 prefixes: AS" + str(nr))
            if len(prefv6) > 0:
                log("measurement", "DEBUG", "Searching alive v6 hosts for AS" + str(nr))
                alivehosts[nr]["v6"] = getalivehosts_v6(prefv6, own_prefix_v6, hitlist_v6, int(config['zmap']['max_hosts']))
            else:
                alivehosts[nr]["v6"] = []
                log("measurement", "DEBUG", "Skipping alive host search, AS has no v6 prefixes: AS" + str(nr))
                if config['general']['debug'] == "True":
                    print("Skipping alive host search, AS has no v6 prefixes: AS" + str(nr))

        log("measurement", "DEBUG", "Alive hosts " + str(alivehosts))
        if config['general']['debug'] == "True":
            print("Alive hosts " + str(alivehosts))

        # Todo 2.2
        # Todo Zmap Look Ahead
        lookahead = {}

        # hosts is equivalent with the as number, it contains two arrays with alive hosts (one ipv4, one ipv6)
        for hosts in alivehosts:
            lookahead[hosts] = {}
            lookahead[hosts]['v4'] = {}
            lookahead[hosts]['v6'] = {}

            if len(alivehosts[hosts]['v4']) > 0:
                log("measurement", "DEBUG", "Scanning: " + str(alivehosts[hosts]['v4']))
                if config['general']['debug'] == "True":
                    print("Scanning v4 of as " + str(alivehosts[hosts]) + ": " + str(alivehosts[hosts]['v4']))
                lookahead[hosts]['v4']['zmap'] = zmap(alivehosts[hosts]['v4'], own_prefix_v4, config['zmap']['max_hosts'])
            else:
                lookahead[hosts]['v4']['zmap'] = []

            if len(alivehosts[hosts]['v6']) > 0:
                log("measurement", "DEBUG", "Scanning: " + str(alivehosts[hosts]['v6']))
                if config['general']['debug'] == "True":
                    print("Scanning v6 of as " + str(alivehosts[hosts]) + ": " + str(alivehosts[hosts]['v6']))
                lookahead[hosts]['v6']['zmap'] = zmap(alivehosts[hosts]['v6'], own_prefix_v6, config['zmap']['max_hosts'])
            else:
                lookahead[hosts]['v6']['zmap'] = []

        log("measurement", "DEBUG", lookahead)
        if config['general']['debug'] == "True":
            print(lookahead)

        # Pre evaluation not necessary
        '''deadflag = {}
    
        for look in lookahead:
            deadflag[look] = {}
    
            if len(lookahead[look]['v4']) == 0:
                deadflag[look]['v4'] = bool(True)
            else:
                deadflag[look]['v4'] = bool(False)
    
            if len(lookahead[look]['v6']) == 0:
                deadflag[look]['v6'] = bool(True)
            else:
                deadflag[look]['v6'] = bool(False)
    
        if config['general']['debug'] == "True":
            print(deadflag)'''

        # Todo 3
        # Todo Ripe Atlas Look Ahead (Wenn AS eine RIPE Probe hat)
        target_v4 = ipaddress.ip_network(own_prefix_v4)[1]
        target_v6 = ipaddress.ip_network(own_prefix_v6)[1]

        probelist = {}

        for nr in asn:
            probelist[nr] = {}
            probes_v4, probes_v6 = getprobes(nr, config['ripe']['max_probes'])
            probelist[nr]['v4'] = probes_v4
            probelist[nr]['v6'] = probes_v6

        for nr in asn:
            dr_v4, dr_v6, lookahead_ripe_results_v4, lookahead_ripe_results_v6 = ripeall(probelist[nr]['v4'], probelist[nr]['v6'], str(target_v4), str(target_v6))
            lookahead[nr]['v4']['ripe'] = dr_v4
            lookahead[nr]['v6']['ripe'] = dr_v6
            lookahead[nr]['ripe_results'] = {}
            lookahead[nr]['ripe_results']['v4'] = lookahead_ripe_results_v4
            lookahead[nr]['ripe_results']['v6'] = lookahead_ripe_results_v6

        # Todo 4
        # Todo Prefix Withdraw + wait(90min)
        if check_announce_v4(own_prefix_v4) == bool(False) or check_announce_v6(own_prefix_v6) == bool(False):
            raise AnnounceError("Prefix was not announced, something went wrong during the measurement")
        else:
            withdraw_prefix(own_prefix_v4)
            withdraw_prefix(own_prefix_v6)

            log("measurement", "DEBUG", "Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn) + " on " + config['general']['mux'] + " withdrawn. Waiting 90 minutes to avoid route flap dampening")
            if config['general']['debug'] == "True":
                print("Prefix "+str(own_prefix_v4)+" and "+str(own_prefix_v6)+" for AS "+str(asn)+" on " + config['general']['mux'] + " withdrawn. Waiting 90 minutes to avoid route flap dampening")
            time.sleep(5400)  # wait 90 min

        # Todo 5
        # Todo Announce poisoned prefix + wait(20min)
        if check_announce_v4(own_prefix_v4) == bool(True) or check_announce_v6(own_prefix_v6) == bool(True):
            raise AnnounceError("Prefix is still announced, something went wrong during the measurement")
        else:
            announce_poisoned_prefix(own_prefix_v4, asn)
            announce_poisoned_prefix(own_prefix_v6, asn)

            log("measurement", "DEBUG", "Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn) + " with path poisoning on " + config['general']['mux'] + " announced. Waiting 20 minutes to let it be distributed.")
            if config['general']['debug'] == "True":
                print("Prefix "+str(own_prefix_v4)+" and "+str(own_prefix_v6)+" for AS "+str(asn)+" with path poisoning on " + config['general']['mux'] + " announced. Waiting 20 minutes to let it be distributed.")
            time.sleep(1200)  # wait 20 min

        # Todo 6
        # Todo Zmap Validation
        validation = {}

        for host in alivehosts:
            validation[host] = {}
            validation[host]['v4'] = {}
            validation[host]['v6'] = {}

            if len(alivehosts[hosts]['v4']) > 0:
                log("measurement", "DEBUG", alivehosts[host]['v4'])
                if config['general']['debug'] == "True":
                    print(alivehosts[host]['v4'])
                validation[host]['v4']['zmap'] = zmap(alivehosts[host]['v4'], own_prefix_v4, config['zmap']['max_hosts'])
            else:
                validation[host]['v4']['zmap'] = []

            if len(alivehosts[hosts]['v6']) > 0:
                log("measurement", "DEBUG", alivehosts[host]['v6'])
                if config['general']['debug'] == "True":
                    print(alivehosts[host]['v6'])
                validation[host]['v6']['zmap'] = zmap(alivehosts[host]['v6'], own_prefix_v6, config['zmap']['max_hosts'])
            else:
                validation[host]['v6']['zmap'] = []

        log("measurement", "DEBUG", validation)
        if config['general']['debug'] == "True":
            print(validation)

        # Todo 7
        # Todo Ripe Atlas validation (Wenn AS eine RIPE Probe hat)
        for nr in asn:
            dr_v4, dr_v6, validation_ripe_results_v4, validation_ripe_results_v6 = ripeall(probelist[nr]['v4'], probelist[nr]['v6'], str(target_v4), str(target_v6))
            validation[nr]['v4']['ripe'] = dr_v4
            validation[nr]['v6']['ripe'] = dr_v6
            validation[nr]['ripe_results'] = {}
            validation[nr]['ripe_results']['v4'] = validation_ripe_results_v4
            validation[nr]['ripe_results']['v6'] = validation_ripe_results_v6

        log("measurement", "DEBUG", lookahead)
        log("measurement", "DEBUG", validation)
        print(lookahead)
        print(validation)

        # result = {"lookahead": (lookahead), "validation": (validation)}
        result = {"lookahead": (lookahead), "validation": (validation), "alivehosts": alivehosts, "probelist": probelist}
        log("bushetal.py", "DEBUG", "Raw Result: " + str(result))

        if check_announce_v4(own_prefix_v4) == bool(False) or check_announce_v6(own_prefix_v6) == bool(False):
            raise AnnounceError("Prefix was not announced, something went wrong during the measurement")
        else:
            analyzed = analyze(result)
            log("bushetal.py", "DEBUG", "Analyzed Result: " + str(analyzed))
            print(analyzed)
            store(analyzed)

    except AnnounceError as error:
        traceback.print_exc()
        log("bushetal.py", "DEBUG", str(traceback.print_exc()))
        log("bushetal.py", "DEBUG", "AnnounceError: Could not perform test because of " + str(error))
        print("AnnounceError: Could not perform test because of " + str(error))
        aspool.append(asn)
        messageoperator(error)

    except TunnelError as error:
        traceback.print_exc()
        log("bushetal.py", "DEBUG", str(traceback.print_exc()))
        log("bushetal.py", "DEBUG", "TunnelError: Could not perform test because of " + str(error))
        print("TunnelError: Could not perform test because of " + str(error))
        aspool.append(asn)
        messageoperator(error)

    finally:
        # Todo 8
        # Todo Prefix Withdraw + wait(90min)
        withdraw_prefix(own_prefix_v4)
        withdraw_prefix(own_prefix_v6)

        log("measurement", "DEBUG", "Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn) + " on " + config['general']['mux'] + " withdrawn. Waiting 90 minutes to avoid route flap dampening")
        if config['general']['debug'] == "True":
            print("Prefix " + str(own_prefix_v4) + " and " + str(own_prefix_v6) + " for AS " + str(asn) + " on " + config['general']['mux'] + " withdrawn. Waiting 90 minutes to avoid route flap dampening")
        time.sleep(5400)  # wait 90 min

        prv4.append(own_prefix_v4)
        prv6.append(own_prefix_v6)

        return result


def analyze(input):
    lookahead = input['lookahead']
    validation = input['validation']
    alivehosts = input['alivehosts']
    probelist = input['probelist']
    result = {}
    for nr in lookahead:
        set = {'v4': bool(False), 'v4_asn': bool(False), 'v6': bool(False), 'v6_asn': bool(False), 'counter_v4': {'zmap_hits': 0, 'zmap_max': 0, 'ripe_hits': 0, 'ripe_max': 0}, 'counter_v6': {'zmap_hits': 0, 'zmap_max': 0, 'ripe_hits': 0, 'ripe_max': 0}}
        if len(lookahead[nr]['v4']['zmap']) == 0 and len(lookahead[nr]['v4']['ripe']) == 0:
            set['v4'] = "dead"
        else:
            if len(validation[nr]['v4']['zmap']) > 0:
                set['v4'] = bool(True)
                set['counter_v4']['zmap_hits'] = len(validation[nr]['v4']['zmap'])
                set['counter_v4']['zmap_max'] = len(alivehosts[nr]['v4'])
            if type(validation[nr]['v4']['ripe']) is not str:
                set['v4'] = bool(True)
                set['v4_asn'] = validation[nr]['v4']['ripe']
                set['counter_v4']['ripe_hits'] = validation[nr]['v4']['ripe']['ripe_hits']
                set['counter_v4']['ripe_max'] = len(probelist[nr]['v4'])

        if len(lookahead[nr]['v6']['zmap']) == 0 and len(lookahead[nr]['v6']['ripe']) == 0:
            set['v6'] = "dead"
        else:
            if len(validation[nr]['v6']['zmap']) > 0:
                set['v6'] = bool(True)
                set['counter_v6']['zmap_hits'] = len(validation[nr]['v6']['zmap'])
                set['counter_v6']['zmap_max'] = len(alivehosts[nr]['v6'])
            if type(validation[nr]['v4']['ripe']) is not str:
                set['v6'] = bool(True)
                set['v6_asn'] = validation[nr]['v6']['ripe']
                set['counter_v6']['ripe_hits'] = validation[nr]['v6']['ripe']['ripe_hits']
                set['counter_v6']['ripe_max'] = len(probelist[nr]['v6'])

        set['v4_ripe_look'] = lookahead[nr]['ripe_results']['v4']
        set['v6_ripe_look'] = lookahead[nr]['ripe_results']['v6']
        set['v4_ripe_vali'] = validation[nr]['ripe_results']['v4']
        set['v6_ripe_vali'] = validation[nr]['ripe_results']['v6']

        result[nr] = set

    return result


def store(input):
    for asn in input:
        if input[asn]['v4'] == "dead":
            lookahead_dead_v4 = bool(True)
        else:
            lookahead_dead_v4 = bool(False)
        #data = {'asn': int(asn), 'ip_version': 4, 'default_route': input[asn]['v4'], 'default_target': input[asn]['v4_asn'], 'timestamp': int(time.time()), 'lookahead_dead': lookahead_dead_v4, 'lookahead_ripe': str(input[asn]['v4_ripe_look']), 'validation_ripe': str(input[asn]['v4_ripe_vali'])}
        data = {'asn': int(asn), 'ip_version': 4, 'default_route': input[asn]['v4'],
                'zmap_hits': input[asn]['counter_v4']['zmap_hits'], 'zmap_max': input[asn]['counter_v4']['zmap_max'], 'ripe_hits': input[asn]['counter_v4']['ripe_hits'], 'ripe_max': input[asn]['counter_v4']['ripe_max'],
                'default_target': str(input[asn]['v4_asn']), 'timestamp': int(time.time()),
                'lookahead_dead': lookahead_dead_v4, 'lookahead_ripe': str(input[asn]['v4_ripe_look']),
                'validation_ripe': str(input[asn]['v4_ripe_vali'])}
        try:
            insert(config['mysql']['table'], data)
        except ConnectionError as error:
            log("store", "DEBUG", "Could not connect to database: " + str(error))
            print("Could not connect to database: " + str(error))

        write(data)

        if input[asn]['v6'] == "dead":
            lookahead_dead_v6 = bool(True)
        else:
            lookahead_dead_v6 = bool(False)
        #data = {'asn': int(asn), 'ip_version': 6, 'default_route': input[asn]['v6'], 'default_target': input[asn]['v6_asn'], 'timestamp': int(time.time()), 'lookahead_dead': lookahead_dead_v6, 'lookahead_ripe': str(input[asn]['v6_ripe_look']), 'validation_ripe': str(input[asn]['v6_ripe_vali'])}
        data = {'asn': int(asn), 'ip_version': 6, 'default_route': input[asn]['v6'],
                'zmap_hits': input[asn]['counter_v6']['zmap_hits'], 'zmap_max': input[asn]['counter_v6']['zmap_max'], 'ripe_hits': input[asn]['counter_v6']['ripe_hits'], 'ripe_max': input[asn]['counter_v6']['ripe_max'],
                'default_target': str(input[asn]['v6_asn']), 'timestamp': int(time.time()),
                'lookahead_dead': lookahead_dead_v6, 'lookahead_ripe': str(input[asn]['v6_ripe_look']),
                'validation_ripe': str(input[asn]['v6_ripe_vali'])}
        try:
            insert(config['mysql']['table'], data)
        except ConnectionError as error:
            log("store", "DEBUG", "Could not connect to database: " + str(error))
            print("Could not connect to database: " + str(error))

        write(data)

    return


testresult = {'lookahead': {'41105': {'v4': {'zmap': ['192.71.198.1', '91.132.179.0', '192.121.21.1', '192.176.228.1', '192.71.102.1', '193.234.127.1', '192.36.235.1', '192.71.221.17', '194.14.49.254', '192.36.193.1', '91.132.177.2', '192.36.88.1', '193.234.105.1'], 'ripe': 'False'}, 'v6': {'zmap': [], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}, '41108': {'v4': {'zmap': ['91.228.104.1', '91.228.52.1', '193.25.100.1', '91.206.76.4', '91.206.77.0', '195.110.20.1', '91.228.53.1', '193.3.157.1', '193.25.101.1', '195.88.44.1', '195.88.45.1'], 'ripe': 'False'}, 'v6': {'zmap': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0:172::2', '2001:67c:12a0::14', '2001:67c:12a0:115::3', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:175::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b'], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}}, 'validation': {'41105': {'v4': {'zmap': ['193.234.127.1', '192.36.193.1', '193.234.105.1', '192.36.235.1', '192.36.88.1', '194.14.49.254', '192.71.102.1', '91.132.179.0', '192.71.221.17', '91.132.177.2', '192.71.198.1', '192.176.228.1', '192.121.21.1'], 'ripe': 'False'}, 'v6': {'zmap': [], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}, '41108': {'v4': {'zmap': [], 'ripe': 'False'}, 'v6': {'zmap': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0::14', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b'], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}}, 'alivehosts': {'41105': {'v4': ['91.132.177.2', '192.36.235.1', '193.234.127.1', '192.176.228.1', '192.36.193.1', '192.71.198.1', '194.14.49.254', '192.121.21.1', '192.71.221.17', '192.36.88.1', '91.132.179.0', '193.234.105.1', '192.71.102.1'], 'v6': []}, '41108': {'v4': ['91.228.53.1', '91.228.52.1', '195.110.20.1', '193.3.157.1', '91.206.76.4', '91.228.104.1', '193.25.101.1', '193.25.100.1', '195.88.44.1', '195.88.45.1', '91.206.77.0'], 'v6': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0:172::2', '2001:67c:12a0::14', '2001:67c:12a0:115::3', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:175::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b']}}, 'probelist': {'41105': {'v4': [], 'v6': []}, '41108': {'v4': [], 'v6': []}}}
testresult_modified = {'lookahead': {'41105': {'v4': {'zmap': ['192.71.198.1', '91.132.179.0', '192.121.21.1', '192.176.228.1', '192.71.102.1', '193.234.127.1', '192.36.235.1', '192.71.221.17', '194.14.49.254', '192.36.193.1', '91.132.177.2', '192.36.88.1', '193.234.105.1'], 'ripe': 'False'}, 'v6': {'zmap': [], 'ripe': '5588,13036'}, 'ripe_results': {'v4': [{'fw': 5020, 'mver': '2.2.1', 'lts': 116, 'endtime': 1615418759, 'dst_name': '184.164.232.1', 'dst_addr': '184.164.232.1', 'src_addr': '192.168.78.140', 'proto': 'ICMP', 'af': 4, 'size': 48, 'paris_id': 1, 'result': [{'hop': 1, 'result': [{'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 5.331}, {'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 0.485}, {'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 0.507}]}, {'hop': 2, 'result': [{'x': '*'}, {'x': '*'}, {'x': '*'}]}, {'hop': 3, 'result': [{'x': '*'}, {'x': '*'}, {'from': '213.29.94.202', 'ttl': 62, 'size': 76, 'rtt': 5.668, 'ittl': 0}]}, {'hop': 4, 'result': [{'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 6.225}, {'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 8.106}, {'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 9.336}]}, {'hop': 5, 'result': [{'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 6.526, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 6.011, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 7.245, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 6, 'result': [{'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 6.899}, {'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 6.496}, {'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 7.546}]}, {'hop': 7, 'result': [{'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.032, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.446, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.036, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 8, 'result': [{'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 24.695, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 25.557, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 25.582, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 9, 'result': [{'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 24.531}, {'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 24.383}, {'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 26.87}]}, {'hop': 10, 'result': [{'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 23.308}, {'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 23.689}, {'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 22.787}]}, {'hop': 11, 'result': [{'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 23.09}, {'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 27.268}, {'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 23.188}]}, {'hop': 12, 'result': [{'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 39.376}, {'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 134.585}, {'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 39.583}]}], 'msm_id': 29285787, 'prb_id': 17825, 'timestamp': 1615418738, 'msm_name': 'Traceroute', 'from': '109.183.113.47', 'type': 'traceroute', 'group_id': 29285787, 'stored_timestamp': 1615418761}, {'fw': 4790, 'lts': 105, 'endtime': 1615418741, 'dst_name': '184.164.232.1', 'dst_addr': '184.164.232.1', 'src_addr': '192.168.65.32', 'proto': 'ICMP', 'af': 4, 'size': 48, 'paris_id': 1, 'result': [{'hop': 1, 'result': [{'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 7.457}, {'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 1.114}, {'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 1.119}]}, {'hop': 2, 'result': [{'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.445}, {'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.273}, {'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.35}]}, {'hop': 3, 'result': [{'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.956}, {'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.853}, {'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.892}]}, {'hop': 4, 'result': [{'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.72}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.762}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.703}]}, {'hop': 5, 'result': [{'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.491}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.424}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.411}]}, {'hop': 6, 'result': [{'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.471}, {'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.418}, {'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.402}]}, {'hop': 7, 'result': [{'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 2.661, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 3.024, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 2.986, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 8, 'result': [{'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.85}, {'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.918}, {'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.867}]}, {'hop': 9, 'result': [{'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.681, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.699, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.798, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 10, 'result': [{'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.921, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.807, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.735, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 11, 'result': [{'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 22.618}, {'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 20.43}, {'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 20.393}]}, {'hop': 12, 'result': [{'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 18.838}, {'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 18.709}, {'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 95.379}]}, {'hop': 13, 'result': [{'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.583}, {'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.563}, {'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.539}]}, {'hop': 14, 'result': [{'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.508}, {'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.43}, {'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.327}]}], 'msm_id': 29285787, 'prb_id': 4683, 'timestamp': 1615418739, 'msm_name': 'Traceroute', 'from': '89.233.144.102', 'type': 'traceroute', 'group_id': 29285787, 'stored_timestamp': 1615418743}], 'v6': ''}}, '41108': {'v4': {'zmap': ['91.228.104.1', '91.228.52.1', '193.25.100.1', '91.206.76.4', '91.206.77.0', '195.110.20.1', '91.228.53.1', '193.3.157.1', '193.25.101.1', '195.88.44.1', '195.88.45.1'], 'ripe': 'False'}, 'v6': {'zmap': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0:172::2', '2001:67c:12a0::14', '2001:67c:12a0:115::3', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:175::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b'], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}}, 'validation': {'41105': {'v4': {'zmap': ['193.234.127.1', '192.36.193.1', '193.234.105.1', '192.36.235.1', '192.36.88.1', '194.14.49.254', '192.71.102.1', '91.132.179.0', '192.71.221.17', '91.132.177.2', '192.71.198.1', '192.176.228.1', '192.121.21.1'], 'ripe': '5588,13036'}, 'v6': {'zmap': [], 'ripe': 'False'}, 'ripe_results': {'v4': [{'fw': 5020, 'mver': '2.2.1', 'lts': 116, 'endtime': 1615418759, 'dst_name': '184.164.232.1', 'dst_addr': '184.164.232.1', 'src_addr': '192.168.78.140', 'proto': 'ICMP', 'af': 4, 'size': 48, 'paris_id': 1, 'result': [{'hop': 1, 'result': [{'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 5.331}, {'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 0.485}, {'from': '192.168.78.1', 'ttl': 64, 'size': 76, 'rtt': 0.507}]}, {'hop': 2, 'result': [{'x': '*'}, {'x': '*'}, {'x': '*'}]}, {'hop': 3, 'result': [{'x': '*'}, {'x': '*'}, {'from': '213.29.94.202', 'ttl': 62, 'size': 76, 'rtt': 5.668, 'ittl': 0}]}, {'hop': 4, 'result': [{'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 6.225}, {'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 8.106}, {'from': '213.29.94.201', 'ttl': 252, 'size': 68, 'rtt': 9.336}]}, {'hop': 5, 'result': [{'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 6.526, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 6.011, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 249, 'size': 140, 'rtt': 7.245, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 6, 'result': [{'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 6.899}, {'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 6.496}, {'from': '62.115.180.86', 'ttl': 250, 'size': 68, 'rtt': 7.546}]}, {'hop': 7, 'result': [{'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.032, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.446, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 245, 'size': 140, 'rtt': 25.036, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 8, 'result': [{'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 24.695, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 25.557, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '80.91.252.42', 'ttl': 246, 'size': 140, 'rtt': 25.582, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 9, 'result': [{'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 24.531}, {'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 24.383}, {'from': '80.91.246.45', 'ttl': 247, 'size': 28, 'rtt': 26.87}]}, {'hop': 10, 'result': [{'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 23.308}, {'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 23.689}, {'from': '62.115.144.33', 'ttl': 57, 'size': 76, 'rtt': 22.787}]}, {'hop': 11, 'result': [{'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 23.09}, {'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 27.268}, {'from': '184.164.255.5', 'ttl': 56, 'size': 76, 'rtt': 23.188}]}, {'hop': 12, 'result': [{'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 39.376}, {'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 134.585}, {'from': '184.164.232.1', 'ttl': 52, 'size': 48, 'rtt': 39.583}]}], 'msm_id': 29285787, 'prb_id': 17825, 'timestamp': 1615418738, 'msm_name': 'Traceroute', 'from': '109.183.113.47', 'type': 'traceroute', 'group_id': 29285787, 'stored_timestamp': 1615418761}, {'fw': 4790, 'lts': 105, 'endtime': 1615418741, 'dst_name': '184.164.232.1', 'dst_addr': '184.164.232.1', 'src_addr': '192.168.65.32', 'proto': 'ICMP', 'af': 4, 'size': 48, 'paris_id': 1, 'result': [{'hop': 1, 'result': [{'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 7.457}, {'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 1.114}, {'from': '192.168.64.1', 'ttl': 64, 'size': 76, 'rtt': 1.119}]}, {'hop': 2, 'result': [{'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.445}, {'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.273}, {'from': '89.233.144.97', 'ttl': 254, 'size': 68, 'rtt': 2.35}]}, {'hop': 3, 'result': [{'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.956}, {'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.853}, {'from': '195.144.98.109', 'ttl': 253, 'size': 68, 'rtt': 1.892}]}, {'hop': 4, 'result': [{'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.72}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.762}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.703}]}, {'hop': 5, 'result': [{'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.491}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.424}, {'from': '213.29.165.18', 'ttl': 250, 'size': 68, 'rtt': 2.411}]}, {'hop': 6, 'result': [{'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.471}, {'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.418}, {'from': '89.24.86.6', 'ttl': 249, 'size': 68, 'rtt': 2.402}]}, {'hop': 7, 'result': [{'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 2.661, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 3.024, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.180.87', 'ttl': 246, 'size': 140, 'rtt': 2.986, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 8, 'result': [{'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.85}, {'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.918}, {'from': '62.115.180.86', 'ttl': 247, 'size': 68, 'rtt': 2.867}]}, {'hop': 9, 'result': [{'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.681, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.699, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.124.26', 'ttl': 242, 'size': 140, 'rtt': 20.798, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 10, 'result': [{'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.921, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.807, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}, {'from': '62.115.112.12', 'ttl': 243, 'size': 140, 'rtt': 20.735, 'ittl': 2, 'icmpext': {'version': 0, 'rfc4884': 1, 'obj': [{'class': 0, 'type': 0}]}}]}, {'hop': 11, 'result': [{'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 22.618}, {'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 20.43}, {'from': '80.91.246.45', 'ttl': 244, 'size': 28, 'rtt': 20.393}]}, {'hop': 12, 'result': [{'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 18.838}, {'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 18.709}, {'from': '62.115.144.33', 'ttl': 54, 'size': 76, 'rtt': 95.379}]}, {'hop': 13, 'result': [{'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.583}, {'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.563}, {'from': '184.164.255.5', 'ttl': 53, 'size': 76, 'rtt': 18.539}]}, {'hop': 14, 'result': [{'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.508}, {'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.43}, {'from': '184.164.232.1', 'ttl': 49, 'size': 48, 'rtt': 34.327}]}], 'msm_id': 29285787, 'prb_id': 4683, 'timestamp': 1615418739, 'msm_name': 'Traceroute', 'from': '89.233.144.102', 'type': 'traceroute', 'group_id': 29285787, 'stored_timestamp': 1615418743}], 'v6': ''}}, '41108': {'v4': {'zmap': [], 'ripe': 'False'}, 'v6': {'zmap': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0::14', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b'], 'ripe': 'False'}, 'ripe_results': {'v4': '', 'v6': ''}}}, 'alivehosts': {'41105': {'v4': ['91.132.177.2', '192.36.235.1', '193.234.127.1', '192.176.228.1', '192.36.193.1', '192.71.198.1', '194.14.49.254', '192.121.21.1', '192.71.221.17', '192.36.88.1', '91.132.179.0', '193.234.105.1', '192.71.102.1'], 'v6': []}, '41108': {'v4': ['91.228.53.1', '91.228.52.1', '195.110.20.1', '193.3.157.1', '91.206.76.4', '91.228.104.1', '193.25.101.1', '193.25.100.1', '195.88.44.1', '195.88.45.1', '91.206.77.0'], 'v6': ['2001:67c:12a0:283::2', '2001:67c:12a0::36e7:7dc6', '2001:67c:12a0:a4::2', '2001:67c:12a0:ffff::beef', '2001:67c:12a0:3:4332:5deb:e44c:fe88', '2001:67c:12a0:f2::2', '2001:67c:12a0:13e::2', '2001:67c:12a0::d3d3:5d9e', '2001:67c:12a0:172::2', '2001:67c:12a0::14', '2001:67c:12a0:115::3', '2001:67c:12a0:120::2', '2001:67c:12a0:264::2', '2001:67c:12a0:8c::2', '2001:67c:12a0::9ede:4247', '2001:67c:12a0:1af::2', '2001:67c:12a0::3676:7ac2', '2001:67c:12a0:1a6::2', '2001:67c:12a0:175::2', '2001:67c:12a0:3:f233:9ccf:be3e:ad7b']}}, 'probelist': {'41105': {'v4': ['5588','13036'], 'v6': []}, '41108': {'v4': [], 'v6': []}}}

# Scheduler
startTime = datetime.now()

#Former predefined ASlist

# Write all as numbers to aslist.txt, that contain a probe from atlas.ripe.net
# ripeaslist(write=True)
aspool = []

try:
    aspool = pickle.load(open("data/aspool.p", "rb"))
except FileNotFoundError:
    asfile = config['general']['asfile']

    with open(asfile) as f:
        aslist = [line.rstrip('\n') for line in f]
        f.close()

    aslist.reverse()

    while len(aslist) >= 1:
        if len(aslist) >= 2:
            as1 = aslist.pop()
            as2 = aslist.pop()

            blocked = list()

            while checkRelation(as1, as2):
                blocked.append(as2)
                as2 = aslist.pop()

            aslist = aslist + blocked

            aspool.append([as1, as2])
        else:
            as1 = aslist.pop()
            aspool.append([as1, as1])
finally:
    random.shuffle(aspool)

manager = Manager()
prv4 = manager.list()
prv6 = manager.list()

with open("data/prefixes4.txt") as f:
    preflistv4 = [line.rstrip('\n') for line in f]
    f.close()
    for prefix in preflistv4:
        prv4.append(prefix)

with open("data/prefixes6.txt") as f:
    preflistv6 = [line.rstrip('\n') for line in f]
    f.close()
    for prefix in preflistv6:
        prv6.append(prefix)

# https://www.iana.org/assignments/as-numbers/as-numbers.xhtml
# Max allocated AS number is 401308
# aspool = list(map(str, range(401308, 0, -1)))

hitlist_v4 = createhitlist(4, "False")
hitlist_v6 = createhitlist(6, "False")

# Defining Proccont
if len(prv4) > len(prv6):
    proccount = len(prv6)
else:
    proccount = len(prv4)

try:
    log("bushetal.py", "DEBUG", "Proccount: " + str(proccount))
    log("bushetal.py", "DEBUG", "ASListLen: " + str(len(aspool)))
    print("Proccount: " + str(proccount))
    print("ASListLen: " + str(len(aspool)))
    with Pool(proccount) as p:
        try:
            results = p.map(measurement, aspool, chunksize=1)
            log("bushetal.py", "DEBUG", results)

            # Done in measurement itself
            '''for result in results:
                if result != "":
                    log("bushetal.py", "DEBUG", "Raw Result: " + str(result))
                    analyzed = analyze(result)
                    log("bushetal.py", "DEBUG", "Analyzed Result: " + str(analyzed))
                    print(analyzed)
                    store(analyzed)
                else:
                    log("bushetal.py", "DEBUG", "Result empty, skipping. Content of result for check: " + str(result))'''

        except AnnounceError as error:
            traceback.print_exc()
            log("bushetal.py", "DEBUG", str(traceback.print_exc()))
            log("bushetal.py", "DEBUG", "AnnounceError: Could not perform test because of " + str(error))
            print("AnnounceError: Could not perform test because of " + str(error))
            messageoperator(error)

        except ValueError as error:
            traceback.print_exc()
            log("bushetal.py", "DEBUG", str(traceback.print_exc()))
            log("bushetal.py", "DEBUG", "ValueError: Could not perform test because of "+ str(error))
            print("ValueError: Could not perform test because of "+ str(error))
            messageoperator(error)

        finally:
            p.close()
            p.join()

            pickle.dump(aspool, open("data/aspool.p", "wb"))

except IndexError as error:
    traceback.print_exc()
    log("bushetal.py", "DEBUG", str(traceback.print_exc()))

    log("bushetal.py", "DEBUG", "Could not run test via multiprocessing, switching to linear approach because of " + str(error))
    print("Could not run test via multiprocessing, switching to linear approach because of " + str(error))
    messageoperator(error)

finally:
    log("bushetal.py", "DEBUG", "Finished measurements")

log("bushetal.py", "DEBUG", "#######################################################################################################")
print("#######################################################################################################")

endTime = datetime.now()
log("bushetal.py", "DEBUG", "Host init: "+str(endTime-startTime))
print("Host init: "+str(endTime-startTime))

