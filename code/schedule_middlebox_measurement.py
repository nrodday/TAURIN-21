__author__ = "Nils Rodday"
__copyright__ = "Copyright 2019"
__credits__ = ["Nils Rodday"]
__email__ = "nils.rodday@unibw.de"
__status__ = "Experimental"

#Get input list from https://ftp.ripe.net/ripe/atlas/probes/archive/2021/05/

import sys
import argparse
import json
import math
from ipwhois import IPWhois
from calendar import timegm
import os
import pickle

import datetime
from ripe.atlas.cousteau import (
  Ping,
  Http,
  Traceroute,
  AtlasSource,
  AtlasCreateRequest,
  AtlasResultsRequest,
  ProbeRequest
)

#ATLAS_API_KEY_Klement = "xxx"
ATLAS_API_KEY_Nils = "xxx"

ATLAS_API_KEY_Nils = "testing" #NEW Probes FIle first!
#ATLAS_API_KEY_Klement = "blub"

def parse_arguments(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="RIPE Atlas probes file")
    return parser.parse_args(args)

def probe_selection(RIPE_probes):

    # probes = ProbeRequest()
    #
    # for probe in probes:
    #     print(probe["id"])
    #
    # # Print total count of found probes
    # print(probes.total_count)

    probes = []
    ipv4_probes_counter = 0

    with open(RIPE_probes) as json_file:
        data = json.load(json_file)
        for p in data['objects']:
            if p['status_name'] == "Connected" and p['asn_v4'] != None:
                ipv4_probes_counter += 1
            if p['status_name'] == "Connected" and p['asn_v4'] != None and p['address_v4'] != None:
                probes.append(p['id'])

        print('Total probes in RIPE Atlas file (incl abandoned): ' + str(len(data['objects'])))
        print('Total probes in RIPE Atlas file (connected and v4)): ' + str(ipv4_probes_counter))
        print('Total probes selected (connected, v4 and ipv4 public ip entry): ' + str((len(probes))))
        probes.sort()
        #print(probes)

        return probes

def schedule_measurements(selected_probes, now):

    start = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)

    measurements_traceroute = []
    measurements_traceroute.append(Traceroute(
        af=4,
        target='147.28.14.1',
        description='Middlebox measurement',
        protocol="ICMP",
        resolve_on_probe="yes",
        paris=16,
    ))

    #value = [34260]
    value = ','.join([str(x) for x in selected_probes])
    #print(value)
    source = AtlasSource(type="probes", value=value, requested=len(selected_probes))
    #source = AtlasSource(type="probes", value='1002455', requested=1)
    #[value.append(str(x)) for x in selected_probes]
    #source = AtlasSource(type="probes", value=value, requested=len(value))

    atlas_request = AtlasCreateRequest(
        start_time=start,
        key=ATLAS_API_KEY_Nils,
        measurements=measurements_traceroute,
        sources=[source],
        is_oneoff=True
    )

    is_success, response = atlas_request.create()

    return is_success, response

def create_folders(timestamp, folder_prefix):
    path = folder_prefix + "/" + timestamp + "/"
    if not os.path.exists(path):
        os.makedirs(path)

def save_ids_to_files(response, response_2, timestamp, folder_prefix):
    path = folder_prefix + "/" + timestamp + "/"

    with open(path + "measurement_ids.json", "a") as write_file:
        write_file.write(json.dumps(response["measurements"]))
        write_file.write(json.dumps(response_2["measurements"]))

def main(args):

    args = parse_arguments(args)

    folder_prefix = "Atlas/middlebox"
    RIPE_probes = args.input
    print("Input file: ", RIPE_probes)

    selected_probes = probe_selection(RIPE_probes) #get all probes for middlebox inferences
    print("Selected probes: ", len(selected_probes))
    print()

    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    timestamp = str(datetime.datetime.timestamp(now)).split('.')[0]
    #print(timestamp)

    create_folders(timestamp, folder_prefix) #Creates traceroute and http folders

    #Return valiables are dicts
    is_success, response = schedule_measurements(selected_probes[:6000], now)
    print(is_success, response)
    is_success_2, response_2 = schedule_measurements(selected_probes[6000:], now)
    print(is_success_2, response_2)
    save_ids_to_files(response, response_2, timestamp, folder_prefix)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))