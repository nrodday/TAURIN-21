import subprocess
import shlex
import ipaddress
import os
import json
import time
import requests
import bz2

from modules.util import *


def getAsnCymru(ip, version):
    if version == 4 or version == 6:
        if version == 4:
            ip_rev = ipaddress.ip_address(ip).reverse_pointer.split('.in')[0]
            cmd = 'dig +short ' + ip_rev + '.origin.asn.cymru.com TXT'  # Preparing the command
        elif version == 6:
            ip_rev = ipaddress.ip_address(ip).reverse_pointer.split('.ip')[0]
            cmd = 'dig +short ' + ip_rev + '.origin6.asn.cymru.com. TXT'  # Preparing the command

        proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)  # Executing
        out,err=proc.communicate()  # Fetching result

        #print("Out dec " + out.decode())
        #print("Out err " + str(err))
        #print("Out raw " + str(out))
        #print(out.decode().split('\n'))

        if out.decode() != "":
            asn = []
            for line in out.decode().split('\n'):
                if line != "":
                    #print(line.split('"')[1].split(' ')[0])
                    asn.append(line.split('"')[1].split(' ')[0])  # Cutting beginning " and unnecessary stuff after the asn number
                else:
                    pass
        else:
            asn = 0

        return(asn)
    else:
        log("getAsnCymru", "DEBUG", "Version has to be 4 or 6!")
        return "Version has to be 4 or 6!"


# translates nlnog id to asn according to the nlnog meta info provided by NLNOG RING NODES
def getAsnNlnog(nlnogid):
    loadNlnogMeta()
    p = open('data/nlnogmeta.json')

    meta = json.load(p)
    try:
        asn = meta[nlnogid]
    except:
        asn = 0

    p.close()
    return str(asn)


def loadNlnogMeta():
    try:
        st = os.stat('data/nlnogmeta.json')
        mtime = st.st_mtime
    except:
        mtime = 0;
    finally:
        if time.time()-mtime > 86400:
            if mtime == 0:
                log("loadNlnogMeta", "DEBUG", "NLNog meta not existing, downloading newest probe meta data from NLNog")
                print('NLNog meta not existing, downloading newest probe meta data from NLNog')
            else:
                log("loadNlnogMeta", "DEBUG", "NLNog meta too old, downloading newest probe meta data from NLNog")
                print('NLNog meta too old, downloading newest probe meta data from NLNog')

            url = 'https://api.ring.nlnog.net/1.0/nodes'
            r = requests.get(url)
            meta = json.loads(r.content)
            data = {}
            # Rearrange downloaded array
            for nodes in meta['results']['nodes']:
                data[nodes['hostname']] = nodes['asn']

            # save rearranged array to file
            with open('data/nlnogmeta.json', 'w') as f:
                json.dump(data, f)
                f.close()

        else:
            log("loadNlnogMeta", "DEBUG", "NLNog meta exists and is less than one day old, skipping download")
            print("NLNog meta exists and is less than one day old, skipping download")


def getAsnRipe(probeid):
    loadRipeMeta()
    p = open('data/probemeta.json')

    meta = json.load(p)
    p.close()

    for objects in meta['objects']:
        if probeid == objects['id']:
            return objects['asn_v4']


def loadRipeMeta():
    try:
        st = os.stat('data/probemeta.json')
        mtime = st.st_mtime
    except:
        mtime = 0

    finally:
        if time.time()-mtime > 86400:
            if mtime == 0:
                log("loadRipeMeta", "DEBUG", "Probe Meta not existing, downloading newest probe meta data from Ripe")
                print('Probe Meta not existing, downloading newest probe meta data from Ripe')
            else:
                log("loadRipeMeta", "DEBUG", "Probe Meta too old, downloading newest probe meta data from Ripe")
                print('Probe Meta too old, downloading newest probe meta data from Ripe')

            url = 'https://ftp.ripe.net/ripe/atlas/probes/archive/meta-latest'
            r = requests.get(url)

            with open('data/probemeta.bz2', 'wb') as f:
                f.write(r.content)
                f.close()

            unzipped = open('data/probemeta.json', 'wb')
            with bz2.open('data/probemeta.bz2', 'rb') as f:
                content = f.read()
                unzipped.write(content)

            os.remove('data/probemeta.bz2')

        else:
            log("loadRipeMeta", "DEBUG", "Probe Meta exists and is less than one day old, skipping download")
            print("Probe Meta exists and is less than one day old, skipping download")