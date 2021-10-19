from modules.resolvetier import *
import pickle

def resultprep(msm_id_list, kind=""):
    dataset = dict()
    if type(msm_id_list) == list:
        for msm_id in msm_id_list:
            with open('results/hlavacek_'+kind+'_'+str(msm_id)+'.csv', "r", newline='') as result_csv:
                csv_dict_reader = DictReader(result_csv)
                for row in csv_dict_reader:
                    asn = row['asn_nr']
                    bool = row['asn_dr']
                    dr = row['asn_dr_to']
                    tier = row['tier']

                    if asn not in dataset:
                        dataset[asn] = {"bool": bool, "dr": dr, "tier": tier}
                    else:
                        # If asn is already in dataset and is not the same as this entry and is not already True
                        if dataset[asn]["bool"] != bool and dataset[asn]["bool"] != "True":
                            dataset[asn] = {"bool": bool, "dr": dr, "tier": tier}

    if type(msm_id_list) == dict:
        for msm_id in msm_id_list:
            for id in msm_id_list[msm_id]:
                with open('results/hlavacek_' + msm_id + '_' + str(id) + '.csv', "r", newline='') as result_csv:
                    csv_dict_reader = DictReader(result_csv)
                    for row in csv_dict_reader:
                        asn = row['asn_nr']
                        bool = row['asn_dr']
                        dr = row['asn_dr_to']
                        tier = row['tier']

                        if asn not in dataset:
                            dataset[asn] = {"bool": bool, "dr": dr, "tier": tier}
                        else:
                            # If asn is already in dataset and is not the same as this entry and is not already True
                            if dataset[asn]["bool"] != bool and dataset[asn]["bool"] != "True":
                                dataset[asn] = {"bool": bool, "dr": dr, "tier": tier}

    tier_1_dr_true = 0
    tier_2_dr_true = 0
    tier_3_dr_true = 0
    tier_0_dr_true = 0

    tier_1_dr_false = 0
    tier_2_dr_false = 0
    tier_3_dr_false = 0
    tier_0_dr_false = 0

    asn_total = len(dataset)
    asn_dr_true = 0
    asn_dr_false = 0

    for data in dataset:
        if dataset[data]["bool"] == "True":
            asn_dr_true = asn_dr_true + 1
        else:
            asn_dr_false = asn_dr_false + 1

        if dataset[data]["bool"] == "True" and dataset[data]["tier"] == "1":
            tier_1_dr_true = tier_1_dr_true + 1
        if dataset[data]["bool"] == "True" and dataset[data]["tier"] == "2":
            tier_2_dr_true = tier_2_dr_true + 1
        if dataset[data]["bool"] == "True" and dataset[data]["tier"] == "3":
            tier_3_dr_true = tier_3_dr_true + 1
        if dataset[data]["bool"] == "True" and dataset[data]["tier"] == "0":
            tier_0_dr_true = tier_0_dr_true + 1

        if dataset[data]["bool"] == "False" and dataset[data]["tier"] == "1":
            tier_1_dr_false = tier_1_dr_false + 1
        if dataset[data]["bool"] == "False" and dataset[data]["tier"] == "2":
            tier_2_dr_false = tier_2_dr_false + 1
        if dataset[data]["bool"] == "False" and dataset[data]["tier"] == "3":
            tier_3_dr_false = tier_3_dr_false + 1
        if dataset[data]["bool"] == "False" and dataset[data]["tier"] == "0":
            tier_0_dr_false = tier_0_dr_false + 1

    sum_false = tier_1_dr_false+tier_2_dr_false+tier_3_dr_false+tier_0_dr_false
    sum_true = tier_1_dr_true + tier_2_dr_true + tier_3_dr_true + tier_0_dr_true

    if sum_false != asn_dr_false:
        print("sum_false and asn_dr_false differ! Something must went wrong!")
    if sum_true != asn_dr_true:
        print("sum_true and asn_dr_true differ! Something must went wrong!")
    if sum_true + sum_false != asn_total:
        print("sum_true+sum_false and asn_total differ! Something must went wrong!")

    print("T1 True: " + str(tier_1_dr_true))
    print("T2 True: " + str(tier_2_dr_true))
    print("T3 True: " + str(tier_3_dr_true))
    print("TX True: " + str(tier_0_dr_true))

    print("Total True: " + str(asn_dr_true))

    print("T1 False: " + str(tier_1_dr_false))
    print("T2 False: " + str(tier_2_dr_false))
    print("T3 False: " + str(tier_3_dr_false))
    print("TX False: " + str(tier_0_dr_false))

    print("Total False: " + str(asn_dr_false))

    print("DR in %: " + str((asn_dr_true/asn_total)*100))

    print("Total ASN: " + str(asn_total))


def comparison(msm_id_list):
    try:
        dataset_panep = pickle.load(open("results/panep.p","rb"))
    except FileNotFoundError:
        dataset_panep = dict()
        if type(msm_id_list) == dict:
            for msm_id in msm_id_list:
                for id in msm_id_list[msm_id]:
                    with open('results/hlavacek_' + msm_id + '_' + str(id) + '.csv', "r", newline='') as result_csv:
                        csv_dict_reader = DictReader(result_csv)
                        for row in csv_dict_reader:
                            asn = row['asn_nr']
                            bool = row['asn_dr']
                            dr = row['asn_dr_to']
                            tier = row['tier']

                            if asn not in dataset_panep:
                                dataset_panep[asn] = {"bool": bool, "dr": dr, "tier": tier}
                            else:
                                # If asn is already in dataset and is not the same as this entry and is not already True
                                if dataset_panep[asn]["bool"] != bool and dataset_panep[asn]["bool"] != "True":
                                    dataset_panep[asn] = {"bool": bool, "dr": dr, "tier": tier}

        pickle.dump(dataset_panep, open("results/panep.p", "wb"))

    try:
        dataset_papp = pickle.load(open("results/papp.p","rb"))

    except FileNotFoundError:
        dataset_papp = dict()
        with open('results/bushetal.csv', "r", newline='') as result_csv:
            csv_dict_reader = DictReader(result_csv)
            for row in csv_dict_reader:
                asn = row['as_tested']
                version = row['ip_version']
                bool = row['default_route']
                dr = row['default_target']
                tier = getTier(asn)

                if asn not in dataset_papp:
                    dataset_papp[asn] = {"bool": bool, "dr": dr, "tier": tier}
                else:
                    # If asn is already in dataset and is not the same as this entry and is not already True
                    if dataset_papp[asn]["bool"] != bool and dataset_papp[asn]["bool"] != "True":
                        dataset_papp[asn] = {"bool": bool, "dr": dr, "tier": tier, "version": version}
                print(str(asn) + " processed!")

        pickle.dump(dataset_papp, open("results/papp.p", "wb"))

    dataset = dict()
    dataset["same"] = dict()
    dataset["different"] = dict()
    count = 0
    for asn in dataset_panep:
        print(asn)
        print(dataset_panep[asn])

        if asn in dataset_papp:
            count = count + 1
            panep_state = dataset_panep[asn]["bool"]
            papp_state = dataset_papp[asn]["bool"]

            set = {"papp": papp_state, "panep": panep_state}

            if papp_state != panep_state:
                print("Ungleich")
                dataset["different"][asn] = set
            else:
                print("Gleich")
                dataset["same"][asn] = set

    print("Gleich: " + str(len(dataset["same"])))
    print("Ungleich: " + str(len(dataset["different"])))

    print("Länge PAPP: " + str(len(dataset_papp)))
    print("Länge PANEP: " + str(len(dataset_panep)))
    print("Neu " + str(count))
    papp = 0
    panep = 0
    for asn in dataset["different"]:
        if dataset["different"][asn]["papp"] == "True":
            papp = papp + 1
        if dataset["different"][asn]["panep"] == "True":
            panep = panep + 1

    print("PAPP True: " + str(papp))
    print("PANEP True: " + str(panep))


    return dataset



# Lukas account
luke_ripe_msm_list_v4 = ['28502492', '28502754', '28503007', '28503224', '28503489', '28503745', '28503985', '28504226', '28504495', '28504697', '28504913', '28505264']
luke_ripe_msm_list_v6 = ['28505417', '28505618', '28505787']

# Nils account
nils_ripe_msm_list_v4 = ['28507052', '28507254']
nils_ripe_msm_list_v6 = ['28507485']

nlnog_msm_list_v4 = ['1609967335']
nlnog_msm_list_v6 = ['1609969227']

msmidlist = dict()
msmidlist['ripe'] = ['28502492', '28502754', '28503007', '28503224', '28503489', '28503745', '28503985', '28504226', '28504495', '28504697', '28504913', '28505264', '28505417', '28505618', '28505787']
msmidlist['ripe'] = ['28507052', '28507254', '28507485']
msmidlist['nlnog'] = ['1609967335', '1609969227']
'''
print("\n")
print("RIPE v4 Luke ###########################################################################")
resultprep(luke_ripe_msm_list_v4, "ripe")
print("\n")
print("RIPE v6 Luke ###########################################################################")
resultprep(luke_ripe_msm_list_v6, "ripe")
print("\n")
print("RIPE v4 Nils ###########################################################################")
resultprep(nils_ripe_msm_list_v4, "ripe")
print("\n")
print("RIPE v6 Nils ###########################################################################")
resultprep(nils_ripe_msm_list_v6, "ripe")
print("\n")
print("NLnog v4 ###############################################################################")
resultprep(nlnog_msm_list_v4, "nlnog")
print("\n")
print("NLnog v6 ###############################################################################")
resultprep(nlnog_msm_list_v6, "nlnog")
print("\n")
print("Total ##################################################################################")
resultprep(msmidlist, "all")
'''

print(comparison(msmidlist))
