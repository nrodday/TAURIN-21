import requests
import hashlib
import os
import shlex
import time
from ripe.atlas.cousteau import *
from ripe.atlas.cousteau.exceptions import *

import traceback

from pathlib import Path

from modules.util import *

from modules.evaluation import *

config = configparser.ConfigParser()
config.read('config.ini')


# retrieve the prefixes for a asn number
def getprefixes(asn):
    prefixesv4 = []
    prefixesv6 = []

    #Todo save list in data and download fresh List if older than x
    for attempt in range(3):
        try:
            with requests.get('https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS' + asn, timeout=600) as request:
                if request.status_code == 200:
                    data = json.loads(request.content.decode('utf-8'))
                    for prefix in data["data"]["prefixes"]:
                        network = ipaddress.ip_network(prefix["prefix"])
                        if network.version == 4:
                            prefixesv4.append(prefix["prefix"])
                        elif network.version == 6:
                            prefixesv6.append(prefix["prefix"])

                else:
                    raise requests.exceptions.ConnectionError("Could not connect to stat.ripe.net!")
        except requests.exceptions.ConnectionError:
            log("getprefixes", "DEBUG", "Could not connect to stat.ripe.net!")
            print("getprefixes: Could not connect to stat.ripe.net!")
            continue
        else:
            break

    return prefixesv4, prefixesv6


def getalivehosts_v4(prefixes, own_prefix, hitlist, max):
    alivehosts = []
    try:
        version = ipaddress.ip_network(own_prefix).version
    except ValueError as error:
        log("getalivehosts", "DEBUG", "Could not identify version of given ip addresses " + str(error))
        quit("getalivehosts: Could not identify version of given ip addresses " + str(error))
    except IndexError as error:
        log("getalivehosts", "DEBUG", "No prefixes found for " + str(prefixes) + " at own prefix " + str(own_prefix) + " because of " + str(error))
        print("getalivehosts: No prefixes found for " + str(prefixes) + " at own prefix " + str(own_prefix) + " because of " + str(error))
        return alivehosts

    match = []
    try:
        zmapcounter = 0
        # Counter that stores amount of zmap tries for this run
        for hit in hitlist:
            if len(alivehosts) >= max:
                raise Breakpoint1
            # Speedcheck to avoid long search in hitlist
            if len(match) >= max and zmapcounter <= 3:
                hosts = zmap(match, own_prefix, max)
                zmapcounter = zmapcounter + 1
                for host in hosts:
                    if host not in alivehosts:
                        alivehosts.append(host)
                        log("getalivehosts", "DEBUG", "Adding host to IPv4 alivehost list: Host: " + str(host) + " found for announced prefix " + str(own_prefix))
                    if len(alivehosts) >= max:
                        raise Breakpoint1
                match = []

            # Bulkcheck
            if len(match) >= 100 and zmapcounter > 3:
                hosts = zmap(match, own_prefix, max)
                zmapcounter = zmapcounter + 1
                for host in hosts:
                    if host not in alivehosts:
                        alivehosts.append(host)
                        log("getalivehosts", "DEBUG", "Adding host to IPv4 alivehost list: Host: " + str(host) + " found for announced prefix " + str(own_prefix))
                    if len(alivehosts) >= max:
                        raise Breakpoint1
                match = []

            try:
                nethex = int(hit, 16)
                net_raw = socket.inet_ntoa(struct.pack("!L", nethex))
                net = ipaddress.ip_address(net_raw)
            except ValueError as error:
                log("getalivehosts", "DEBUG", str(error))
                print("getalivehosts: " + str(error))
                continue

            try:
                for prefix in prefixes:
                    network = ipaddress.ip_network(prefix)

                    try:
                        if network.version != version:
                            raise PrefixError("Version from prefix differs from others")

                        if net in network:
                            # print(str(net) + " : " + str(prefix))

                            hostlist = hitlist[hit]
                            for host in hostlist:
                                hosthex = int(host, 16)

                                ip = socket.inet_ntoa(struct.pack("!L", nethex + hosthex))
                                # print(ip)
                                if ip not in match:
                                    log("getalivehosts", "DEBUG", "Found a hit: " + str(ip) + " for prefix " + str(prefix) + " on announced prefix " + str(own_prefix))
                                    if config['general']['debug'] == "True":
                                        print("Found a hit: " + str(ip) + " for prefix " + str(prefix) + " on announced prefix " + str(own_prefix))

                                    match.append(ip)
                                    raise Breakpoint2

                    except PrefixError:
                        log("getalivehosts", "DEBUG", "Skipping prefix, because of diff in ip version!")
                        print("Skipping prefix, because of diff in ip version!")

            except Breakpoint2:
                pass

        if len(match) > 0:
            hosts = zmap(match, own_prefix, max)
            for host in hosts:
                if len(alivehosts) >= max:
                    raise Breakpoint1
                if host not in alivehosts:
                    alivehosts.append(host)
                    log("getalivehosts", "DEBUG", "Adding host to alivehost list: Host: " + str(host) + " found for announced prefix " + str(own_prefix))

    except Breakpoint1:
        log("getalivehosts", "DEBUG", "Found enough alivehosts for announced prefix " + str(own_prefix))
        pass

    log("getalivehosts", "DEBUG", "Found matches for announced prefix " + str(own_prefix) + ": " + str(match))
    log("getalivehosts", "DEBUG", "Found alivehosts for announced prefix " + str(own_prefix) + ": " + str(alivehosts))
    if config['general']['debug'] == "True":
        print(match)
        print(alivehosts)

    return alivehosts


def getalivehosts_v6(prefixes, own_prefix, hitlist, max):
    alivehosts = []
    try:
        version = ipaddress.ip_network(own_prefix).version
    except ValueError as error:
        log("getalivehosts", "DEBUG", "Could not identify version of given ip addresses " + str(error))
        quit("getalivehosts: Could not identify version of given ip addresses " + str(error))
    except IndexError as error:
        log("getalivehosts", "DEBUG", "No prefixes found for " + str(prefixes) + " at own prefix " + str(own_prefix) + " because of " + str(error))
        print("getalivehosts: No prefixes found for " + str(prefixes) + " at own prefix " + str(own_prefix) + " because of " + str(error))
        return alivehosts

    match = []

    try:
        zmapcounter = 0
        for hit in hitlist:
            if len(alivehosts) >= max:
                raise Breakpoint1
            if len(match) >= max and zmapcounter <= 3:
                zmapcounter = zmapcounter + 1
                hosts = zmap(match, own_prefix, max)
                for host in hosts:
                    if host not in alivehosts:
                        alivehosts.append(host)
                        log("getalivehosts", "DEBUG", "Adding host to IPv6 alivehost list: Host: " + str(host) + " found for announced prefix " + str(own_prefix))
                    if len(alivehosts) >= max:
                        raise Breakpoint1
                match = []

            # Bulkcheck
            if len(match) >= 100 and zmapcounter > 3:
                hosts = zmap(match, own_prefix, max)
                zmapcounter = zmapcounter + 1
                for host in hosts:
                    if host not in alivehosts:
                        alivehosts.append(host)
                        log("getalivehosts", "DEBUG", "Adding host to IPv6 alivehost list: Host: " + str(host) + " found for announced prefix " + str(own_prefix))
                    if len(alivehosts) >= max:
                        raise Breakpoint1
                match = []

            try:
                ip = ipaddress.ip_address(hit)
            except ValueError as error:
                log("getalivehosts", "DEBUG", str(error))
                print("getalivehosts: " + str(error))
                continue

            try:
                for prefix in prefixes:
                    network = ipaddress.ip_network(prefix)

                    try:
                        if network.version != version:
                            raise PrefixError("Version from prefix differs from others")

                        if ip in network and hit not in match:
                            log("getalivehosts", "DEBUG", "Found a hit: " + str(hit) + " for prefix " + str(prefix) + " on announced prefix " + str(own_prefix))
                            if config['general']['debug'] == "True":
                                print("Found a hit: " + str(hit) + " for prefix " + str(prefix) + " on announced prefix " + str(own_prefix))
                            match.append(hit)
                            raise Breakpoint2
                    except PrefixError:
                        log("getalivehosts", "DEBUG", "Skipping prefix, because of diff in ip version!")
                        print("Skipping prefix, because of diff in ip version!")
            except Breakpoint2:
                pass

        if len(match) > 0:
            hosts = zmap(match, own_prefix, max)
            for host in hosts:
                if len(alivehosts) >= max:
                    raise Breakpoint1
                if host not in alivehosts:
                    alivehosts.append(host)

    except Breakpoint1:
        log("getalivehosts", "DEBUG", "Found enough alivehosts for announced prefix " + str(own_prefix))
        pass

    log("getalivehosts", "DEBUG", "Found matches for announced prefix " + str(own_prefix) + ": " + str(match))
    log("getalivehosts", "DEBUG", "Found alivehosts for announced prefix " + str(own_prefix) + ": " + str(alivehosts))

    if config['general']['debug'] == "True":
        print("Match: " + str(own_prefix) + " : " + str(match))
        print("Alivehosts: " + str(own_prefix) + " : " + str(alivehosts))

    return alivehosts


def zmap(alivehosts, own_prefix, max):
    reachable = []
    try:
        version = ipaddress.ip_address(alivehosts[0]).version
    except ValueError as error:
        log("zmap", "DEBUG", "Could not identify version of given ip addresses " + str(error))
        quit("zmap: Could not identify version of given ip addresses " + str(error))
    except IndexError as error:
        log("zmap", "DEBUG", "Alive hosts is empty " + str(error))
        if config['general']['debug'] == "True":
            print("zmap: Alive hosts is empty " + str(error))
        return reachable

    md5 = hashlib.md5(str(alivehosts).encode()).hexdigest()
    target_file =  "tmp/"+md5

    Path("tmp").mkdir(parents=False, exist_ok=True)

    with open(target_file, 'w') as file:
        for host in alivehosts:
            file.write(host+"\n")

    packetrate = config['zmap']['packet_limit']
    source_ip = ipaddress.ip_network(own_prefix)[1]
    interface = config['general']['interface']
    gateway_mac = config['general']['gateway_mac']

    if version == 4:
        probemodule = config['zmap']['probe_module_v4']
        cmd = "sudo zmap -N " + str(max) + " -q -v 0 -r " + packetrate + " -M " + probemodule + " -i " + interface + " --source-ip=" + str(source_ip) + " --gateway-mac=" + gateway_mac + " -I " + target_file
    elif version == 6:
        probemodule = config['zmap']['probe_module_v6']
        cmd = "sudo zmap -N " + str(max) + " -q -v 0 -r " + packetrate + " -M " + probemodule + " -i " + interface + " --ipv6-source-ip=" + str(source_ip) + " --gateway-mac=" + gateway_mac + " --ipv6-target-file=" + target_file
    else:
        log("zmap", "DEBUG", "IP Version must be 4 or 6! Now it is: "+str(version))
        quit("IP Version must be 4 or 6! Now it is: "+str(version))

    log("zmap", "DEBUG", cmd)
    if config['general']['debug'] == "True":
        print(cmd)

    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)  # Executing
    out, err = proc.communicate()  # Fetching result

    for line in out.decode().split('\n'):
        if line in alivehosts:
            try:
                ipaddress.ip_address(line)
                reachable.append(line)
            except ValueError as error:
                log("zmap", "DEBUG", "Not an ip address " + str(error))
                print("zmap: Not an ip address " + str(error))
        else:
            continue

    os.remove(target_file)

    return reachable


def getprobes(asn, max):
    filters_v4 = {"asn_v4": asn, "status": "1"}
    probes_v4 = ProbeRequest(**filters_v4)

    filters_v6 = {"asn_v6": asn, "status": "1"}
    probes_v6 = ProbeRequest(**filters_v6)

    v4 = []
    for probe in probes_v4:
        if len(v4) >= max:
            break
        else:
            v4.append(probe['id'])

    v6 = []
    for probe in probes_v6:
        if len(v6) >= max:
            break
        else:
            v6.append(probe['id'])

    return v4, v6


def ripecreate(probelist, target, version):
    #Todo
    requested = len(probelist)
    value = str(probelist).split("[")[1].split("]")[0]

    af = version
    description = config['traceroute']['description']
    target = target
    protocol = config['traceroute']['protocol']
    port = config['traceroute']['port']
    packets = config['traceroute']['packets']
    paris = config['traceroute']['paris']
    first_hop = config['traceroute']['first_hop']
    dont_fragment = config['traceroute']['dont_fragment']
    response_timeout = config['traceroute']['response_timeout']
    size = config['traceroute']['packet_size']
    max_hops = config['traceroute']['max_hops']

    traceroute = Traceroute(
        af=af,
        target=target,
        description=description,
        protocol=protocol,
        port=port,
        packets=packets,
        paris=paris,
        first_hop=first_hop,
        dont_fragment=dont_fragment,
        response_timeout=response_timeout,
        size=size,
        max_hops=max_hops
    )

    # Declaring source settings
    source = AtlasSource(
        type="probes",
        value=value,
        requested=requested
    )

    # Declaring request with source and traceroute settings as oneoff test
    atlas_request = AtlasCreateRequest(
        # start_time=datetime.utcnow(),
        key=config['ripe']['atlasapikey'],
        measurements=[traceroute],
        sources=[source],
        is_oneoff=True
    )

    is_success, response = atlas_request.create()
    if is_success:
        response = response['measurements'][0]
    else:
        is_success = bool(False)

    return is_success, response


def ripestatus(msm_id):
    try:
        measurement = Measurement(id=msm_id)
        return measurement.status
    except APIResponseError as error:
        log("ripestatus", "DEBUG", str(error))
        print("ripestatus: " + str(error))
        return bool(False)


def riperequest(msm_id):
    kwargs = {"msm_id": msm_id}
    is_success, results = AtlasResultsRequest(**kwargs).create()
    log("riperequest", "DEBUG", is_success)
    log("riperequest", "DEBUG", results)
    return is_success, results


def ripeall(probes_v4, probes_v6, target_v4, target_v6):
    dr_v4 = "False"
    dr_v6 = "False"
    is_success_v4_create = bool(False)
    is_success_v6_create = bool(False)
    msm_id_v4 = ""
    msm_id_v6 = ""
    msm_stat_v4 = ""
    msm_stat_v6 = ""
    timeout = 3600
    sleeptime = 10

    results_v4 = ""
    results_v6 = ""

    if len(probes_v4) > 0:
        is_success_v4_create, msm_id_v4 = ripecreate(probes_v4, target_v4, 4)
        log("ripeall", "DEBUG", str(is_success_v4_create) + " creation on target " + str(target_v4))
        log("ripeall", "DEBUG", str(msm_id_v4) + " msm_id on target " + str(target_v4))
        msm_stat_v4 = ripestatus(msm_id_v4)

    if len(probes_v6) > 0:
        is_success_v6_create, msm_id_v6 = ripecreate(probes_v6, target_v6, 6)
        log("ripeall", "DEBUG", str(is_success_v6_create) + " creation on target " + str(target_v6))
        log("ripeall", "DEBUG", str(msm_id_v6) + " msm_id on target " + str(target_v6))
        msm_stat_v6 = ripestatus(msm_id_v6)

    if is_success_v4_create:
        timer = 0
        while msm_stat_v4 != "Stopped" and msm_stat_v4 != "Failed" and timer < timeout:
            msm_stat_v4 = ripestatus(msm_id_v4)

            log("ripeall", "DEBUG", str(msm_id_v4) + ": " + str(msm_stat_v4))
            if config['general']['debug'] == "True":
                print(str(msm_id_v4) + ": " + str(msm_stat_v4))

            timer = timer + sleeptime
            time.sleep(sleeptime)

    if is_success_v6_create:
        timer = 0
        while msm_stat_v6 != "Stopped" and msm_stat_v6 != "Failed" and timer < timeout:
            msm_stat_v6 = ripestatus(msm_id_v6)

            log("ripeall", "DEBUG", str(msm_id_v6) + ": " + str(msm_stat_v6))
            if config['general']['debug'] == "True":
                print(str(msm_id_v6) + ": " + str(msm_stat_v6))

            timer = timer + sleeptime
            time.sleep(sleeptime)

    if is_success_v4_create and msm_stat_v4 == "Stopped":
        is_success_v4_request, results_v4 = riperequest(msm_id_v4)
        log("ripeall", "DEBUG", "Request success status " + str(is_success_v4_request) + " on target " + str(target_v4))
        log("ripeall", "DEBUG", "Request result content " + str(results_v4) + " on target " + str(target_v4))
        try:
            if len(results_v4) > 0:
                probe_count_v4, data_v4 = prepare(results_v4, "ripe", "4")
                evaluated_v4 = evaluate(data_v4)
                log("ripeall", "DEBUG", evaluated_v4)
                print(evaluated_v4)
                for ev in evaluated_v4:
                    if ev['asn_dr'] == "True":
                        dr_v4 = {}
                        dr_v4['asn_dr_to'] = ev['asn_dr_to']
                        dr_v4['ripe_hits'] = ev['count_hits']
                        dr_v4['ripe_max'] = ev['count_probes']
                    else:
                        dr_v4 = str(ev['asn_dr'])
            else:
                log("ripeall", "DEBUG", "Results delivered from ripe atlas are empty, cant evaluate")
        except TypeError as error:
            log("ripeall", "DEBUG", "TypeError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v4)
            print(results_v4)
        except IndexError as error:
            log("ripeall", "DEBUG", "IndexError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v4)
            print(results_v4)
        except MeasurementError as error:
            log("ripeall", "DEBUG", "MeasurementError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v4)
            print(results_v4)

    if is_success_v6_create:
        is_success_v6_request, results_v6 = riperequest(msm_id_v6)
        log("ripeall", "DEBUG", "Request success status " + str(is_success_v6_request) + " on target " + str(target_v4))
        log("ripeall", "DEBUG", "Request result content " + str(results_v6) + " on target " + str(target_v4))
        try:
            if len(results_v6) > 0:
                probe_count_v6, data_v6 = prepare(results_v6, "ripe", "6")
                evaluated_v6 = evaluate(data_v6)
                log("ripeall", "DEBUG", evaluated_v6)
                print(evaluated_v6)
                for ev in evaluated_v6:
                    if ev['asn_dr'] == "True":
                        dr_v6 = {}
                        dr_v6['asn_dr_to'] = ev['asn_dr_to']
                        dr_v6['ripe_hits'] = ev['count_hits']
                        dr_v6['ripe_max'] = ev['count_probes']
                    else:
                        dr_v6 = ev['asn_dr']
            else:
                log("ripeall", "DEBUG", "Results delivered from ripe atlas are empty, cant evaluate")
        except TypeError as error:
            log("ripeall", "DEBUG", "TypeError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v6)
        except IndexError as error:
            log("ripeall", "DEBUG", "IndexError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v6)
        except MeasurementError as error:
            log("ripeall", "DEBUG", "MeasurementError: Error in provided msm_raw file!" + str(error))
            log("ripeall", "DEBUG", results_v6)

    if is_success_v4_create and msm_stat_v4 == "Failed":
        log("ripeall", "DEBUG", "Failure during IPv4 measurement at atlas.ripe.net, msm_id: " + str(msm_id_v4))

    if is_success_v6_create and msm_stat_v6 == "Failed":
        log("ripeall", "DEBUG", "Failure during IPv6 measurement at atlas.ripe.net, msm_id: " + str(msm_id_v6))

    return dr_v4, dr_v6, results_v4, results_v6
