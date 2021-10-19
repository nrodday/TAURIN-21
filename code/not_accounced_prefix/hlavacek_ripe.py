from datetime import datetime
startTime = datetime.now()

from ripe.atlas.cousteau import (
    Traceroute,
    AtlasSource,
    AtlasCreateRequest,
    AtlasResultsRequest,
    Measurement
)

import json
import time
import configparser

from modules.evaluation import (
    prepare,
    evaluate,
    evaluate2,
    summarize
)

from modules.archive import archive

from modules.resolveasn import *


def run_ripe(**kwargs):
    ##############################################################
    # Reading from the Config File
    config = configparser.ConfigParser()
    config.read('config.ini')

    timestamp = kwargs.get('timestamp', time.time())

    ripeconf = ""
    af = kwargs.get('af', config['traceroute']['af'])
    description = kwargs.get('description', config['traceroute']['description'])
    target = kwargs.get('target', config['traceroute']['target'])
    protocol = kwargs.get('protocol', config['traceroute']['protocol'])
    port = kwargs.get('port', config['traceroute']['port'])
    packets = kwargs.get('packets', config['traceroute']['packets'])
    paris = kwargs.get('paris', config['traceroute']['paris'])
    first_hop = kwargs.get('first_hop', config['traceroute']['first_hop'])
    dont_fragment = kwargs.get('dont_fragment', config['traceroute']['dont_fragment'])
    size = kwargs.get('packet_size', config['traceroute']['packet_size'])
    max_hops = kwargs.get('max_hops', config['traceroute']['max_hops'])
    requested = kwargs.get('requested', config['ripe']['requested'])

    if requested == "0":
        requested = config['ripe']['maxnodes']

    ripeconf = ripeconf + "IPv"+af
    ripeconf = ripeconf + " Protocol: "+protocol
    if protocol == "TCP":
        ripeconf = ripeconf + " Port: "+port
    ripeconf = ripeconf + " Packets: "+packets
    ripeconf = ripeconf + " Paris: "+paris
    ripeconf = ripeconf + " FirstHop: "+first_hop
    ripeconf = ripeconf + " DontFragment: "+dont_fragment
    ripeconf = ripeconf + " Size: "+size
    ripeconf = ripeconf + " MaxHops: "+max_hops


    ##############################################################
    # Declaring traceroute settings
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
        size= size,
        max_hops=max_hops
    )

    if kwargs.get('probeset'):
        source = AtlasSource(
            type="probes",
            value=kwargs.get('probes'),
            requested=len(kwargs.get('probes'))
        )
    else:
        # Declaring source settings
        source = AtlasSource(
            type=config['ripe']['type'],
            value=config['ripe']['value'],
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

    msm_id = []

    # Starting the test, if skip is set to true, skipping
    skip = kwargs.get('skip', config['ripe']['skip'])

    if skip == "True" or skip == "true":
        print("Skipped creation of new measurement!")
        msm_id = kwargs.get('msm_id', config['ripe']['msm_id'])
    else:
        (is_success, response) = atlas_request.create()
        if is_success:
            print("Measurement successfully created")
            # saving msm_id from response for further analysis
            msm_id = response['measurements'][0]
        else:
            print("Could not create new measurement! Aborting." + str(response))
            quit()

    print("Measurement ID: " + str(msm_id))

    ##############################################################
    # Waiting till measurement is finished

    # retrieving measurement info once
    try:
        measurement = Measurement(id=msm_id)

        while measurement.status != "Stopped":
            # retrieving measurement info again
            measurement = Measurement(id=msm_id)
            print ("MSM status: "+measurement.status)
            print("Waiting till measurement is stopped!")
            time.sleep(5)

        print("Measurement stopped!")

    except ValueError:
        pass

    ##############################################################
    # Measurement evaluation

    print("Proceeding with evaluation!")

    loadRipeMeta()

    # Setting probe counter
    probe_count = 0

    # Request measurement data
    kwargs = {"msm_id": msm_id}

    is_success, results = AtlasResultsRequest(**kwargs).create()


    # If Debug is true
    if config['general']['debug'] == "True":
        # Test printing python dict in json look
        json_object = json.dumps(results, indent=4)
        print(json_object)

    # Converting measurement info to smaller python dict
    if is_success:
        archive("ripe", target, results, ripeconf, msm_id, description, requested)
    else:
        if config['general']['debug'] == "True":
            print("Could not load measurement from ripe, trying to load from archive!")

        try:
            filename = "ripe_" + str(msm_id) + '.json'
            loadeddata = open('archive/' + filename)
            results = json.load(loadeddata)

        except FileNotFoundError:
            print("Could not load measurement from ripe and local archive! Aborting.")
            exit()

    probe_count, data = prepare(results, "ripe", af)

    # If Debug is true
    if config['general']['debug'] == "True":
        # Test printing python dict in json look
        json_object = json.dumps(data, indent = 4)
        print(json_object)

    # Evaluate gathered data
    evaluate(data, msm_id, "ripe", af, probe_count, timestamp)

    # Measurement Summary
    summarize(msm_id, "ripe", startTime, probe_count)

    # Done
    print("Done, GL HF!")

    return msm_id
