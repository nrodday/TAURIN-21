import json

import subprocess
import shlex

import ipaddress

from ripe.atlas.cousteau import AtlasResultsRequest


def getAsn(ip):
    o1 = ip.split('.')[0]
    o2 = ip.split('.')[1]
    o3 = ip.split('.')[2]
    o4 = ip.split('.')[3]
    ip_rev = o4+'.'+o3+'.'+o2+'.'+o1 #Reversing the ip for correct lookup

    cmd='dig +short '+ip_rev+'.origin.asn.cymru.com TXT' #Preparing the command
    proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE) #Executing
    out,err=proc.communicate() #Fetching result

    asn = out.split('"')[1].split(' ')[0] #Cutting beginning " and unneccessary stuff after the asn number
    return(asn)

#print(getAsn("80.72.240.74"))

kwargs = {
    "msm_id": 27837066
    #"msm_id": 27837000
#    "start": datetime(2020, 10, 26),
#    "stop": datetime(2020, 10, 26),
#    "probe_ids": [1203,1238,1290,1312]
}

is_success, results = AtlasResultsRequest(**kwargs).create()


data = {}

if is_success:
    """
    last_ip = ''
    for first in results:
        #print first['msm_id'], first['src_addr']
        for second in first['result']:
            #print second, second['hop']
            #print second['result']

            for third in second['result']:
                try:
                    if (last_ip != third['from']):
                            last_ip = third['from']
                            #print("GET ASN FOR this IP")
                            print first['msm_id'], first['prb_id'], first['src_addr'], second['hop'], third['from'],
                            if (ipaddress.ip_address(unicode(first['src_addr'])).is_global): print(getAsn(first['src_addr'])),
                            else: print('PSADR'),
                            if (ipaddress.ip_address(unicode(third['from'])).is_global): print(getAsn(third['from']))
                            else: print('PDADR')
                    else:
                        pass
                except:
                    pass
    print('##########################################################')
    """
    for first in results:
        prb_id = first['prb_id']
        prb_set = {}
        prb_asn = 0
        for second in first['result']:
            for third in second['result']:
                try:
                    if (ipaddress.ip_address(unicode(third['from'])).is_global):
                        asn = getAsn(third['from'])
                        prb_set[second['hop']] = asn
                        if (prb_asn == 0): prb_asn = asn
                    else:
                        prb_set[second['hop']] = "prAdr"
                except:
                    pass

        if prb_asn in data:
            data[prb_asn][prb_id] = prb_set
        else:
            data[prb_asn] = {}
            data[prb_asn][prb_id] = prb_set

json_object = json.dumps(data, indent = 4)
print(json_object)

f = open("asn.csv", "w")
f.write("asn_nr"+","+"asn_dr"+","+"asn_dr_to"+";\n")

for asn in data:
    asn_dr = False
    asn_dr_to = False
    print "Asn: " + str(asn)
    for probe in data[asn]:
        print "  Probe: "+str(probe)
        lasthop = ""
        for hop in data[asn][probe]:
            if (data[asn][probe][hop] != "prAdr"):
                if (lasthop == "" or lasthop == data[asn][probe][hop]):
                    print "    Hop-Asn: "+data[asn][probe][hop] #Asn_nr
                    lasthop = data[asn][probe][hop]
                else:
                    print "    Default Route detected! DR to: "+data[asn][probe][hop]
                    asn_dr = True
                    asn_dr_to = data[asn][probe][hop]

    f.write(str(asn)+","+str(asn_dr)+","+str(asn_dr_to)+";\n")



f.close()


########################################Pseudocode Gedanke
#for each result
#    get probe ip_address and check ASN_NR
#    for each hop get ip_address and check ASN_NR
#    if HOP_ASN != SOURCE_ASN then default_route = TRUE
#    Dann noch irgendwie in JSON reinklopfen mit ASN_NR als Key
##########################################################

#print(ipaddress.ip_address(unicode("10.0.0.0")).is_global)

