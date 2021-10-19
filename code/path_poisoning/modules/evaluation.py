import json
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

from modules.util import *

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
        log("iteratedata", "DEBUG", "ASN: " + str(prb_asn))
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
    if msm_raw[0]['af'] != int(version):
        log("prepare", "DEBUG", "Measurement version differs from given version, make sure that the correct ip version is set in the traceroute settings when using a old measurement!")
        raise MeasurementError("Measurement version differs from given version, make sure that the correct ip version is set in the traceroute settings when using a old measurement!")

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


def evaluate(data):
    timestamp = time.time()
    # Iterating python dictionary "data" and writing info to file
    evaluated = []
    for asn in data:
        asn_dr = False
        asn_dr_to = {}
        n = 0
        dr_hit_counter = 0
        probe_counter = 0

        # If Debug is true
        if config['general']['debug'] == "True":
            print("Asn: " + str(asn))

        for probe in data[asn]:
            if probe != "raw":
                probe_counter = probe_counter + 1
                probe_asn = data[asn][probe][0]

                for hop in data[asn][probe]:
                    if (data[asn][probe][hop] != "prAdr" and data[asn][probe][hop] != "0") and probe_asn != \
                            data[asn][probe][hop]:
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
                            print("    Hop-Asn: " + data[asn][probe][hop])  # Asn_nr

        dr_list = ""
        for drs in asn_dr_to:
            if dr_list == "":
                dr_list = str(asn_dr_to[drs])
            else:
                dr_list = dr_list + "," + str(asn_dr_to[drs])

        if dr_list == "":
            dr_list = False

        evaluated.append({'asn_nr': str(asn), 'asn_dr': str(asn_dr),
                   'asn_dr_to': str(dr_list),
                   'tier': str(getTier(str(asn))),
                   'count_hits': int(dr_hit_counter), 'count_probes': int(probe_counter), 'timestamp': int(timestamp),
                   'raw_traceroute': str(data[asn]['raw'])})

        #evaluated.append({'asn_nr': str(asn), 'asn_dr': str(asn_dr), 'asn_dr_to': str(dr_list), 'tier': str(getTier(str(asn)))})

    return evaluated
