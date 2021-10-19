import os
import configparser

from modules.store import *

config = configparser.ConfigParser()
config.read('config.ini')

# Overwrite
config['mysql']['table'] = "bush_test"


def analyze(input):
    lookahead = input['lookahead']
    validation = input['validation']

    set = {'v4': bool(False), 'v4_asn': bool(False), 'v6': bool(False), 'v6_asn': bool(False), 'counter_v4': {'zmap_hits': 0, 'zmap_max': 0, 'ripe_hits': 0, 'ripe_max': 0}, 'counter_v6': {'zmap_hits': 0, 'zmap_max': 0, 'ripe_hits': 0, 'ripe_max': 0}}
    if len(lookahead['v4']['zmap']) == 0 and len(lookahead['v4']['ripe']) == 0:
        set['v4'] = "dead"
    else:
        if len(validation['v4']['zmap']) > 0:
            set['v4'] = bool(True)
            set['counter_v4']['zmap_hits'] = len(validation['v4']['zmap'])
            set['counter_v4']['zmap_max'] = len(lookahead['v4']['zmap'])
        if type(validation['v4']['ripe']) is not str or list:
            set['v4'] = bool(True)
            set['v4_asn'] = validation['v4']['ripe']
            set['counter_v4']['ripe_hits'] = len(validation['v4']['ripe'].split(",")) if isinstance(validation['v4']['ripe'], str) else len(validation['v4']['ripe'])
            set['counter_v4']['ripe_max'] = len(lookahead['v4']['ripe'].split(",")) if isinstance(lookahead['v4']['ripe'], str) else len(lookahead['v4']['ripe'])

    if len(lookahead['v6']['zmap']) == 0 and len(lookahead['v6']['ripe']) == 0:
        set['v6'] = "dead"
    else:
        if len(validation['v6']['zmap']) > 0:
            set['v6'] = bool(True)
            set['counter_v6']['zmap_hits'] = len(validation['v6']['zmap'])
            set['counter_v6']['zmap_max'] = len(lookahead['v6']['zmap'])
        if type(validation['v4']['ripe']) is not str or list:
            set['v6'] = bool(True)
            set['v6_asn'] = validation['v6']['ripe']
            set['counter_v6']['ripe_hits'] = len(validation['v6']['ripe'].split(",")) if isinstance(validation['v6']['ripe'], str) else len(validation['v6']['ripe'])
            set['counter_v6']['ripe_max'] = len(lookahead['v6']['ripe'].split(",")) if isinstance(lookahead['v6']['ripe'], str) else len(lookahead['v6']['ripe'])

    set['v4_ripe_look'] = lookahead['ripe_results']['v4']
    set['v6_ripe_look'] = lookahead['ripe_results']['v6']
    set['v4_ripe_vali'] = validation['ripe_results']['v4']
    set['v6_ripe_vali'] = validation['ripe_results']['v6']

    return set


def store(input):
    for asn in input:
        if input[asn]['v4'] == "dead":
            lookahead_dead_v4 = bool(True)
        else:
            lookahead_dead_v4 = bool(False)
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


def scanlog(filename):
    skey_result = "Raw Result: "
    skey_as = "Searching alive v4 hosts for AS"
    skey_hosts = "Alive hosts "

    result = dict()
    with open("./log/" + filename, "r") as file:

        for line in file:
            line = line.strip()
            if skey_as in line:
                asn = line.split(skey_as)[1]
                result[asn] = {"lookahead": {"v4": {"zmap": [], "ripe": []}, "v6": {"zmap": [], "ripe": []}, 'ripe_results': {'v4': '', 'v6': ''}}, "validation": {"v4": {"zmap": [], "ripe": []}, "v6": {"zmap": [], "ripe": []}, 'ripe_results': {'v4': '', 'v6': ''}}}

            # get all alive hosts by asn
            if skey_hosts in line:
                try:
                    hostlist = eval(line.split(skey_hosts)[1])
                    for asn in hostlist:
                        if asn in result:
                            # print(raw["lookahead"][asn])
                            result[asn]["alivehosts"] = hostlist[asn]

                except SyntaxError:
                    continue

            # get all results and probes by asn
            if skey_result in line:
                raw = eval(line.split(skey_result)[1])
                # get lookahead and probelist
                for asn in raw["lookahead"]:
                    if asn in result:
                        # get complete lookahead
                        result[asn]["lookahead"] = raw["lookahead"][asn]
                        if "ripe_results" not in result[asn]["lookahead"]:
                            result[asn]["lookahead"]["ripe_results"] = {'v4': '', 'v6': ''}

                # get validation
                for asn in raw["validation"]:
                    if asn in result:
                        result[asn]["validation"] = raw["validation"][asn]
                        if "ripe_results" not in result[asn]["validation"]:
                            result[asn]["validation"]["ripe_results"] = {'v4': '', 'v6': ''}

    return result


results = dict()
for filename in os.listdir("log"):
    if filename.endswith(".log") and filename.startswith("bush"):
        result = scanlog(filename)
        if len(result) > 0:
            results = {**results, **result}

analyzed = dict()
for set in results:
    analyzed[set] = analyze(results[set])

store(analyzed)