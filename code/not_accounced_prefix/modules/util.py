import json
import requests

def ripeprobelist(write = False):
    probelist_v4 = []
    probelist_v6 = []
    next = "https://atlas.ripe.net/api/v2/probes/?format=json"

    while next is not None:
        try:
            with requests.get(next, timeout=600) as request:
                if request.status_code == 200:
                    data = json.loads(request.content.decode('utf-8'))
                    next = data['next']
                    print(next)

                    for result in data['results']:
                        if result['id'] not in probelist_v4 and isinstance(result['asn_v4'], int) and result['status']['id'] == 1:
                            print(result['id'])
                            probelist_v4.append(result['id'])
                        if result['id'] not in probelist_v6 and isinstance(result['asn_v6'], int) and result['status']['id'] == 1:
                            print(result['id'])
                            probelist_v6.append(result['id'])
                else:
                    raise requests.exceptions.ConnectionError("Could not connect to atlas.ripe.net!")
        except requests.exceptions.ConnectionError:
            print("Could not connect to stat.ripe.net!")

        if write:
            try:
                with open('data/ripeprobes_v4.txt', 'w') as file:
                    for probe in probelist_v4:
                        file.write(str(probe) + '\n')

                with open('data/ripeprobes_v6.txt', 'w') as file:
                    for probe in probelist_v6:
                        file.write(str(probe) + '\n')

            except FileNotFoundError as error:
                quit("File cant be found because of " + str(error))

    return probelist_v4, probelist_v6