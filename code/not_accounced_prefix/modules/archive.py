import json
import csv
import time


def archive(kind, target, data, config, msm_id, description, nodes):
    filename = kind + "_" + str(msm_id) + '.json'

    # Check if file already exits
    try:
        test = open('archive/'+filename, 'r')
        test.close()

    # If not, create File with json dump and create entry in archive.csv
    except FileNotFoundError:
        with open('archive/' + filename, 'w') as f:
            json.dump(data, f)
            f.close()

        # Making entry for traceroute config in archive.csv
        try:
            test = open('archive/archive.csv', 'r')
            test.close()
            archivefile = open('archive/archive.csv', 'a')
            fieldnames = ['probeset', 'target', 'description', 'config', 'measurement_id', 'filename', 'nodes', 'timestamp']
            writer = csv.DictWriter(archivefile, fieldnames=fieldnames)

        except FileNotFoundError:
            archivefile = open('archive/archive.csv', 'w')
            fieldnames = ['probeset', 'target', 'description', 'config', 'measurement_id', 'filename', 'nodes', 'timestamp']
            writer = csv.DictWriter(archivefile, fieldnames=fieldnames)
            writer.writeheader()


        finally:
            writer.writerow({'probeset': kind, 'target': target, 'description': description, 'config': config,
                             'measurement_id': msm_id, 'filename': filename, 'nodes': nodes,
                             'timestamp': int(time.time())})
            archivefile.close()
