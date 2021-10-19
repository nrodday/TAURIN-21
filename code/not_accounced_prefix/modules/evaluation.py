import json
import time
import csv
from csv import DictReader
import configparser
from datetime import datetime
import ipaddress
import multiprocessing as mp
from multiprocessing import Pool
from functools import partial

from modules.resolvetier import (
    loadTierMeta,
    getTier
)
from modules.resolveasn import (
    getAsnCymru,
    getAsnRipe,
    getAsnNlnog
)

from modules.store import *

config = configparser.ConfigParser()
config.read('config.ini')

loadTierMeta()


def iteratedata(kind, version, preparedata):
    backdata = {}

    try:
        prb_id = preparedata['prb_id']
        prb_set = {}
        if kind == "ripe":
            prb_asn = getAsnRipe(prb_id)
        elif kind == "nlnog":
            prb_asn = getAsnNlnog(prb_id)
        else:
            prb_asn = ""
            quit("Could not get asn source, kind must be ripe or nlnog")

        # If Debug is true
        if config['general']['debug'] == "True":
            print(prb_asn)

        prb_set[0] = str(prb_asn)

        for second in preparedata['result']:
            try:
                for third in second['result']:
                    try:
                        if ipaddress.ip_address(str(third['from'])).is_global:
                            asn = getAsnCymru(third['from'], int(version))
                            if str(prb_asn) in asn:
                                prb_set[second['hop']] = str(prb_asn)
                            else:
                                prb_set[second['hop']] = asn[0]
                        else:
                            prb_set[second['hop']] = "prAdr"
                    except:
                        pass
            except:
                pass

        backdata = {'prb_set': prb_set, 'prb_id': prb_id, 'prb_raw': preparedata}

    finally:
        return backdata


# Implementation of multiprocessing
def prepare(msm_raw, kind, version):
    '''try:
        if msm_raw[0]['af'] != int(version):
            quit("Measurement version differs from given version, make sure that the correct ip version is set in the traceroute settings when using a old measurement!")
    except TypeError as error:
        quit("TypeError: Error in provided msm_raw file: " + str(error))
    except IndexError as error:
        quit("IndexError: Error in provided msm_raw file: " + str(error))'''
    # Setting probe counter
    probe_count = 0

    func = partial(iteratedata, kind, version)

    with Pool(processes=8) as p:
        results = p.map(func, msm_raw)
        # clean up once all tasks are done
        p.close()
        p.join()

    data = {}

    for result in results:
        if len(result) > 0:
            probe_count = probe_count + 1
            prb_asn = result['prb_set'][0]
            prb_id = result['prb_id']
            if prb_asn in data:
                data[prb_asn][prb_id] = result['prb_set']
                try:
                    data[prb_asn]['raw'][prb_id] = result['prb_raw']
                except KeyError:
                    data[prb_asn]['raw'] = {}
                    data[prb_asn]['raw'][prb_id] = result['prb_raw']
            else:
                data[prb_asn] = {}
                data[prb_asn][prb_id] = result['prb_set']
                try:
                    data[prb_asn]['raw'][prb_id] = result['prb_raw']
                except KeyError:
                    data[prb_asn]['raw'] = {}
                    data[prb_asn]['raw'][prb_id] = result['prb_raw']

    return probe_count, data


def evaluate(data, msm_id, kind, af, probe_count, timestamp):
    with open('results/hlavacek_'+kind+'_'+str(msm_id)+'.csv', 'w') as csvfile:
        fieldnames = ['asn_nr', 'asn_dr', 'asn_dr_to', 'tier']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Iterating python dictionary "data" and writing info to file
        for asn in data:
            asn_dr = False
            asn_dr_to = {}
            n = 0
            dr_hit_counter = 0
            probe_counter = 0

            # If Debug is true
            if config['general']['debug'] == "True":
                print("Asn: "+str(asn))

            for probe in data[asn]:
                if probe != "raw":
                    probe_counter = probe_counter + 1
                    probe_asn = data[asn][probe][0]

                    for hop in data[asn][probe]:
                        if (data[asn][probe][hop] != "prAdr" and data[asn][probe][hop] != "0") and probe_asn != data[asn][probe][hop]:
                            # If Debug is true
                            if config['general']['debug'] == "True":
                                print("    Default route detected! DR to: " + str(data[asn][probe][hop]))
                            asn_dr = True
                            if not str(data[asn][probe][hop]) in asn_dr_to.values():
                                asn_dr_to[n] = str(data[asn][probe][hop])
                                n = n + 1
                                dr_hit_counter = dr_hit_counter + 1
                                break

                        else:
                            # If Debug is true
                            if config['general']['debug'] == "True":
                                print("    Hop-Asn: "+data[asn][probe][hop])   # Asn_nr

            dr_list = ""
            for drs in asn_dr_to:
                if dr_list == "":
                    dr_list = str(asn_dr_to[drs])
                else:
                    dr_list = dr_list + "," + str(asn_dr_to[drs])

            if dr_list == "":
                dr_list = False

            try:
                content = {'asn': int(asn), 'ip_version': int(af), 'default_route': str(asn_dr),
                        'default_target': str(dr_list), 'probe_provider': str(kind), 'msm_id': int(msm_id), 'count_hits': int(dr_hit_counter), 'count_probes': int(probe_counter), 'timestamp': int(timestamp),
                        'raw_traceroute': str(data[asn]['raw'])}

                write(config['mysql']['table'], content)
                try:
                    insert(config['mysql']['table'], content)
                except ConnectionError as error:
                    print("Could not connect to database: " + str(error))

                writer.writerow({'asn_nr': str(asn), 'asn_dr': str(asn_dr), 'asn_dr_to': str(dr_list), 'tier': str(getTier(str(asn)))})
            except ValueError as error:
                print("Could not evaluate asn because of: "+str(error))


# Measurement Summary
# Runtime, Total AS, Total Probes, Total DRs, False positives (DR to Same ASN)
def summarize(msm_id, kind, startTime, probe_count):
    res_false_pos = 0
    res_dr_count = 0
    res_asn_count = 0
    tier1 = 0
    tier2 = 0
    tier3 = 0
    tierx = 0

    with open('results/hlavacek_'+kind+'_'+str(msm_id)+'.csv', "r", newline='') as result_csv:
        csv_dict_reader = DictReader(result_csv)
        for row in csv_dict_reader:
            if row['asn_nr'] == row['asn_dr_to']:
                res_asn_count = res_asn_count + 1
                res_false_pos = res_false_pos + 1
            if row['asn_dr'] == "True":
                res_asn_count = res_asn_count + 1
                res_dr_count = res_dr_count + 1
                if row['tier'] == "1": tier1 = tier1 + 1
                elif row['tier'] == "2": tier2 = tier2 + 1
                elif row['tier'] == "3": tier3 = tier3 + 1
                else: tierx = tierx + 1
            else:
                res_asn_count = res_asn_count + 1

    print("False Positives: " + str(res_false_pos) + " - Total ASN: " + str(res_asn_count) + " - Total DR: " + str(
        res_dr_count) + " - Percentage: " + str(
        round((res_dr_count / res_asn_count) * 100, 2)) + "%")
    print("Tier 1: " + str(tier1))
    print("Tier 2: " + str(tier2))
    print("Tier 3: " + str(tier3))
    print("Tier X: " + str(tierx))
    print("Total Probes: " + str(probe_count) + " - Execution Time: " + str(datetime.now() - startTime))


# Work in Progress, this function should recognize, if there is a DR from a given AS to another, that also uses a DR Route
def evaluate2(data, msm_id, kind):
    data_split = {}

    for asn in data:
        for probe in data[asn]:
            probe_asn = data[asn][probe][0]
            lasthop = ""
            probe_set = {}
            probe_set[0] = data[asn][probe][0]
            n = 1
            for hop in data[asn][probe]:
                probe_set[n] = data[asn][probe][hop]


                if probe_asn in data_split:
                    data_split[probe_asn] = probe_set
                else:
                    data_split[probe_asn] = {}
                    data_split[probe_asn] = probe_set

#    if asn in data_split:
#        data[asn][prb_id] = prb_set
#    else:
#        data[prb_asn] = {}
#        data[prb_asn][prb_id] = prb_set

    # If Debug is true
    if config['general']['debug'] == "True":
        json_object = json.dumps(data_split, indent=4)
        print("###########################################################")
        print(json_object)

    exit()

    with open('results/hlavacek_'+kind+'_'+str(msm_id)+'.csv', 'w') as csvfile:
        fieldnames = ['asn_nr', 'asn_dr', 'asn_dr_to']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Iterating python dictionary "data" and writing info to file
        for asn in data:
            asn_dr = False
            asn_dr_to = {}
            n = 0

            # If Debug is true
            if config['general']['debug'] == "True":
                print("Asn: "+str(asn))

            for probe in data[asn]:
                probe_asn = data[asn][probe][0]

                for hop in data[asn][probe]:
                    if data[asn][probe][hop] != "prAdr" and data[asn][probe][hop] != "0" and probe_asn != data[asn][probe][hop]:
                        # If Debug is true
                        if config['general']['debug'] == "True":
                            print("    Default route detected! DR to: " + str(data[asn][probe][hop]))
                        asn_dr = True
                        if not str(data[asn][probe][hop]) in asn_dr_to.values():
                            asn_dr_to[n] = str(data[asn][probe][hop])
                            n = n + 1

                    else:
                        # If Debug is true
                        if config['general']['debug'] == "True":
                            print("    Hop-Asn: "+data[asn][probe][hop]) # Asn_nr

            dr_list = ""
            for drs in asn_dr_to:
                if dr_list == "":
                    dr_list = str(asn_dr_to[drs])
                else:
                    dr_list = dr_list + "," + str(asn_dr_to[drs])

            if dr_list == "":
                dr_list = False

            writer.writerow({'asn_nr': str(asn), 'asn_dr': str(asn_dr), 'asn_dr_to': str(dr_list)})
