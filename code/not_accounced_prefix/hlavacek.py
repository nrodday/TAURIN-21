from hlavacek_nlnog import run_nlnog
from hlavacek_ripe import run_ripe
from modules.util import *

import configparser

# Adjustable Parameters
'''
skip
msm_id
requested

af
target
description
protocol
port
first_hop
packets
dont_fragment
paris
response_timeout
packet_size
max_hops
timestamp
'''

# Settings for best results
#run_nlnog(skip="False", requested="0", af="4", target="184.164.235.1", description="BAMeasurement", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")
#run_nlnog(skip="False", requested="0", af="6", target="2804:269c:7::1", description="BAMeasurement", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")

config = configparser.ConfigParser()
config.read('config.ini')

########
# RIPE #
########

# Retrieving probes
probelist_v4, probelist_v6 = ripeprobelist(write=True)

# Creating IPv4 Probelist, splitted in lists with max length of maxnodes
list_v4 = list()
templist = list()
for probe in probelist_v4:
    if len(templist) >= int(config['ripe']['maxnodes']):
        list_v4.append(templist)
        templist = list()
    if len(templist) < int(config['ripe']['maxnodes']):
        templist.append(probe)

list_v4.append(templist)


# Creating IPv6 Probelist, splitted in lists with max length of maxnodes
list_v6 = list()
templist = list()
for probe in probelist_v6:
    if len(templist) >= int(config['ripe']['maxnodes']):
        list_v6.append(templist)
        templist = list()
    if len(templist) < int(config['ripe']['maxnodes']):
        templist.append(probe)
list_v6.append(templist)


# Running one tests for each probelist in list_v4
ripe_msm_list_v4 = list()
testcounter = 1
for probeset in list_v4:
    value = str(probeset).split("[")[1].split("]")[0]
    msm_id = run_ripe(skip="False", probeset=True, probes=value, af="4", target="184.164.232.1",description="Forward DR Probing v4 Run: "+str(testcounter), prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")
    ripe_msm_list_v4.append(msm_id)
    testcounter = testcounter + 1


# Running one tests for each probelist in list_v6
ripe_msm_list_v6 = list()
testcounter = 1
for probeset in list_v6:
    value = str(probeset).split("[")[1].split("]")[0]
    msm_id = run_ripe(skip="False", probeset=True, probes=value, af="6", target="2804:269c:30::1",description="Forward DR Probing v6 Run: "+str(testcounter), prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")
    ripe_msm_list_v6.append(msm_id)
    testcounter = testcounter + 1
    


"""
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29937193", timestamp="1619729869")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29937216", timestamp="1619731042")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29943004", timestamp="1619803358")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29943037", timestamp="1619804517")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29947600", timestamp="1619889829")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29947785", timestamp="1619890996")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29960808", timestamp="1619976191")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29961018", timestamp="1619977060")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29972830", timestamp="1620062580")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29985782", timestamp="1620148948")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29985880", timestamp="1620150110")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29993271", timestamp="1620235338")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="29993302", timestamp="1620236566")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30024961", timestamp="1620321814")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30025108", timestamp="1620323039")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30049454", timestamp="1620408858")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30049537", timestamp="1620410298")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30061864", timestamp="1620495221")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30061988", timestamp="1620496392")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30075769", timestamp="1620582179")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30076001", timestamp="1620583039")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30101032", timestamp="1620668048")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30101281", timestamp="1620669510")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30115867", timestamp="1620755023")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30129141", timestamp="1620840234")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30129557", timestamp="1620841130")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30144605", timestamp="1620926638")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30161999", timestamp="1621014290")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30162460", timestamp="1621015779")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30187475", timestamp="1621100651")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30187882", timestamp="1621102140")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30210140", timestamp="1621187038")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30210386", timestamp="1621188213")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30230890", timestamp="1621273443")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30231018", timestamp="1621274905")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30251468", timestamp="1621359742")
run_ripe(skip="True", af="4", target="184.164.232.1", msm_id="30251617", timestamp="1621360955")

run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29937240", timestamp="1619732254")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29943062", timestamp="1619805741")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29947847", timestamp="1619892209")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29961195", timestamp="1619978301")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29986014", timestamp="1620151345")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="29993334", timestamp="1620237780")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30025261", timestamp="1620323941")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30049580", timestamp="1620411218")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30062181", timestamp="1620497580")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30076092", timestamp="1620584330")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30101605", timestamp="1620670451")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30130006", timestamp="1620842332")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30162887", timestamp="1621017302")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30188489", timestamp="1621103645")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30210531", timestamp="1621189125")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30231272", timestamp="1621276132")
run_ripe(skip="True", af="6", target="2804:269c:30::1", msm_id="30251962", timestamp="1621362249")
"""

#########
# NLNOG #
#########

nlnog_msm_id_4 = run_nlnog(skip="False", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")
nlnog_msm_id_6 = run_nlnog(skip="False", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32")

"""
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619732287", timestamp="1619732287")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619733761", timestamp="1619733761")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619805772", timestamp="1619805772")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619807248", timestamp="1619807248")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619894159", timestamp="1619894159")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619979814", timestamp="1619979814")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620151374", timestamp="1620151374")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620152901", timestamp="1620152901")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620237815", timestamp="1620237815")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620239786", timestamp="1620239786")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620411256", timestamp="1620411256")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620411736", timestamp="1620411736")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620584368", timestamp="1620584368")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620670958", timestamp="1620670958")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620842373", timestamp="1620842373")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620842830", timestamp="1620842830")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621017347", timestamp="1621017347")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621021477", timestamp="1621021477")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621276172", timestamp="1621276172")
run_nlnog(skip="True", requested="0", af="4", target="184.164.232.1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621362291", timestamp="1621362291")


run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619892248", timestamp="1619892248")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1619978334", timestamp="1619978334")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620323979", timestamp="1620323979")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620324444", timestamp="1620324444")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620497610", timestamp="1620497610")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620498085", timestamp="1620498085")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620586337", timestamp="1620586337")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1620670490", timestamp="1620670490")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621103723", timestamp="1621103723")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621104284", timestamp="1621104284")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621189165", timestamp="1621189165")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621191035", timestamp="1621191035")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621277630", timestamp="1621277630")
run_nlnog(skip="True", requested="0", af="6", target="2804:269c:30::1", description="Forward DR Probing", prococol="ICMP", packets="3", paris="1", packet_size="48", max_hops="32", msm_id="1621364133", timestamp="1621364133")
"""
##########
# Result #
##########

# Todo conversion into images for each test instead of once in test.py if needed

