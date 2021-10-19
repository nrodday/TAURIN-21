from datetime import datetime
startTime = datetime.now()

from csv import DictReader

probe_count = 0
msm_id = 27956213
# msm_id = 27955599

res_false_pos = 0
res_dr_count = 0
res_asn_count = 0

with open(str(msm_id) + ".csv", "r", newline='') as result_csv:
    csv_dict_reader = DictReader(result_csv)
    for row in csv_dict_reader:
        if row['asn_nr'] == row['asn_dr_to']:
            res_false_pos = res_false_pos + 1
        if row['asn_dr'] == "True":
            res_dr_count = res_dr_count + 1
        else:
            res_asn_count = res_asn_count + 1

print("False Pos: " + str(res_false_pos) + " - Total ASN: " + str(res_asn_count) + " - Total DR: " + str(res_dr_count) + " - Total Probes: " + str(probe_count) + " - Execution Time: " + str(datetime.now() - startTime))
