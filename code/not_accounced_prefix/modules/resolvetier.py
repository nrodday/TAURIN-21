import bz2
import os
import requests
import csv
from csv import DictReader
import configparser
import json

config = configparser.ConfigParser()
config.read('config.ini')

def loadTierMeta():
    filedir=config['general']['tiermeta']
    # Dont forget to reference CAIDA and report publication according to the readme in the dir of file above


    # Download tier meta and convert it to .csv
    new_filename="tierlist_"+filedir.split('serial-2/')[1].split('.')[0]
    if not os.path.isfile("data/"+new_filename+".csv"):
        print('File doesnt exist local, downloading now!')
        r = requests.get(filedir)

        with open('data/'+new_filename+'.bz2', 'wb') as f:
            f.write(r.content)
            f.close()

        unzipped = open('data/'+new_filename+'.txt', 'wb')
        with bz2.open('data/'+new_filename+'.bz2', 'rb') as f:
            content = f.read()
            unzipped.write(content)

        os.remove('data/'+new_filename+'.bz2')

        txt = open('data/'+new_filename+'.txt', 'r')
        lines = txt.readlines()

        with open('data/'+new_filename+'.csv', 'w') as csvfile:
            fieldnames = ['provider', 'customer', 'relation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for line in lines:
                if line.startswith('#'):
                    pass
                else:
                    prov = line.split('|')[0]
                    cust = line.split('|')[1]
                    rela = line.split('|')[2]
                    writer.writerow({'provider': prov, 'customer': cust, 'relation': rela})

        os.remove('data/' + new_filename + '.txt')


    # evaluate tier meta
    with open('data/'+new_filename+'.csv', "r", newline='') as result_csv:
        csv_dict_reader = DictReader(result_csv)
        tier_meta = {}

        for row in csv_dict_reader:
            provider = row['provider']
            customer = row['customer']
            relation = row['relation']

            if provider not in tier_meta:
                tier_meta[provider] = "0"
            if customer not in tier_meta:
                tier_meta[customer] = "0"

            if row['relation'] == "-1":
                if tier_meta[provider] == "3":
                    tier_meta[provider] = "2"
                elif tier_meta[provider] == "2":
                    pass
                else:
                    tier_meta[provider] = "1"

                if tier_meta[customer] == "1":
                    tier_meta[customer] = "2"
                elif tier_meta[customer] == "2":
                    pass
                else:
                    tier_meta[customer] = "3"



    tier1 = 0
    tier2 = 0
    tier3 = 0
    tierx = 0

    for AS in tier_meta:
        if tier_meta[AS] == "1":
            tier1 = tier1 + 1
        elif tier_meta[AS] == "2":
            tier2 = tier2 + 1
        elif tier_meta[AS] == "3":
            tier3 = tier3 + 1
        else:
            tierx = tierx + 1

    if config['general']['debug'] == "True":
        print("Tier 1: "+str(tier1)+" Tier 2: "+str(tier2)+" Tier 3: "+str(tier3)+" Tier X: "+str(tierx))

    # json_object = json.dumps(tier_meta, indent=4)
    # print(json_object)

    # save tiermeta to file
    with open('data/tiermeta.json', 'w') as f:
        json.dump(tier_meta, f)
        f.close()

def getTier(asn):
    try:
        p = open('data/tiermeta.json')
    except:
        print("Could not open tiermeta.json, downloading new one")
        loadTierMeta()
        p = open('data/tiermeta.json')

    meta = json.load(p)
    try:
        asn = meta[asn]
    except:
        asn = 0

    p.close()
    return str(asn)