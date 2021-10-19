from modules.resolvetier import *
from modules.linkage import *


def resultprep():
    asnv4 = list()
    v4_dr_true_t1 = list()
    v4_dr_true_t2 = list()
    v4_dr_true_t3 = list()
    v4_dr_true_t0 = list()

    v4_dr_false_t1 = list()
    v4_dr_false_t2 = list()
    v4_dr_false_t3 = list()
    v4_dr_false_t0 = list()

    asnv6 = list()
    v6_dr_true_t1 = list()
    v6_dr_true_t2 = list()
    v6_dr_true_t3 = list()
    v6_dr_true_t0 = list()

    v6_dr_false_t1 = list()
    v6_dr_false_t2 = list()
    v6_dr_false_t3 = list()
    v6_dr_false_t0 = list()


    v4_dr_true = list()
    v6_dr_true = list()
    v4_dr_false = list()
    v6_dr_false = list()

    with open('results/bushetal_2.csv', "r", newline='') as result_csv:
        csv_dict_reader = DictReader(result_csv)
        for row in csv_dict_reader:
            asn = row['as_tested']
            version = row['ip_version']
            bool = row['default_route']
            dr = row['default_target']
            tier = getTier(asn)

            prefv4, prefv6 = getprefixes(asn)
            print(str(prefv4) + str(prefv6))

            if row['lookahead_dead'] == "True":
                pass
            else:
                #if len(prefv4) > 0 and len(prefv6) > 0:
                if True:
                    if len(prefv4) > 0 and version == "4":
                        asnv4.append(asn)

                        if bool == "True":
                            v4_dr_true.append(asn)

                            if tier == "1":
                                v4_dr_true_t1.append(asn)
                            elif tier == "2":
                                v4_dr_true_t2.append(asn)
                            elif tier == "3":
                                v4_dr_true_t3.append(asn)
                            elif tier == "0":
                                v4_dr_true_t0.append(asn)

                        if bool == "False":
                            v4_dr_false.append(asn)

                            if tier == "1":
                                v4_dr_false_t1.append(asn)
                            elif tier == "2":
                                v4_dr_false_t2.append(asn)
                            elif tier == "3":
                                v4_dr_false_t3.append(asn)
                            elif tier == "0":
                                v4_dr_false_t0.append(asn)

                    if len(prefv6) > 0 and version == "6":
                        asnv6.append(asn)

                        if bool == "True":
                            v6_dr_true.append(asn)

                            if tier == "1":
                                v6_dr_true_t1.append(asn)
                            elif tier == "2":
                                v6_dr_true_t2.append(asn)
                            elif tier == "3":
                                v6_dr_true_t3.append(asn)
                            elif tier == "0":
                                v6_dr_true_t0.append(asn)

                        if bool == "False":
                            v6_dr_false.append(asn)

                            if tier == "1":
                                v6_dr_false_t1.append(asn)
                            elif tier == "2":
                                v6_dr_false_t2.append(asn)
                            elif tier == "3":
                                v6_dr_false_t3.append(asn)
                            elif tier == "0":
                                v6_dr_false_t0.append(asn)

    merged_t1_true = v4_dr_true_t1 + list(set(v6_dr_true_t1) - set(v4_dr_true_t1))
    merged_t2_true = v4_dr_true_t2 + list(set(v6_dr_true_t2) - set(v4_dr_true_t2))
    merged_t3_true = v4_dr_true_t3 + list(set(v6_dr_true_t3) - set(v4_dr_true_t3))
    merged_t0_true = v4_dr_true_t0 + list(set(v6_dr_true_t0) - set(v4_dr_true_t0))

    merged_t1_false = list(set(v4_dr_false_t1 + list(set(v6_dr_false_t1) - set(v4_dr_false_t1))) - set(merged_t1_true))
    merged_t2_false = list(set(v4_dr_false_t2 + list(set(v6_dr_false_t2) - set(v4_dr_false_t2))) - set(merged_t2_true))
    merged_t3_false = list(set(v4_dr_false_t3 + list(set(v6_dr_false_t3) - set(v4_dr_false_t3))) - set(merged_t3_true))
    merged_t0_false = list(set(v4_dr_false_t0 + list(set(v6_dr_false_t0) - set(v4_dr_false_t0))) - set(merged_t0_true))

    asnmerged = asnv4 + list(set(asnv6) - set(asnv4))

    only_v4_true = list(set(v4_dr_true) - set(v6_dr_true))
    only_v6_true = list(set(v6_dr_true) - set(v4_dr_true))
    both_true = list(set(set(v4_dr_true + list(set(v6_dr_true) - set(v4_dr_true))) - set(only_v4_true)) - set(only_v6_true))
    # both_true = list(set(v4_dr_true + v6_dr_true) - set(only_v4_true) - set(only_v6_true))

    print("IPv4 ########################################")
    print("T1 True: " + str(len(v4_dr_true_t1)))
    print("T2 True: " + str(len(v4_dr_true_t2)))
    print("T3 True: " + str(len(v4_dr_true_t3)))
    print("TX True: " + str(len(v4_dr_true_t0)))
    totaltruev4 = len(v4_dr_true_t1) + len(v4_dr_true_t2) + len(v4_dr_true_t3) + len(v4_dr_true_t0)
    print("Total True: " + str(totaltruev4))

    print("T1 False: " + str(len(v4_dr_false_t1)))
    print("T2 False: " + str(len(v4_dr_false_t2)))
    print("T3 False: " + str(len(v4_dr_false_t3)))
    print("TX False: " + str(len(v4_dr_false_t0)))

    totalfalsev4 = len(v4_dr_false_t1) + len(v4_dr_false_t2) + len(v4_dr_false_t3) + len(v4_dr_false_t0)
    print("Total False: " + str(totalfalsev4))

    print("DR in %: " + str((totaltruev4/len(asnv4))*100))
    print("Total AS Count: " + str(len(asnv4)))

    print("\n")
    print("IPv6 ########################################")
    print("T1 True: " + str(len(v6_dr_true_t1)))
    print("T2 True: " + str(len(v6_dr_true_t2)))
    print("T3 True: " + str(len(v6_dr_true_t3)))
    print("TX True: " + str(len(v6_dr_true_t0)))
    totaltruev6 = len(v6_dr_true_t1) + len(v6_dr_true_t2) + len(v6_dr_true_t3) + len(v6_dr_true_t0)
    print("Total True: " + str(totaltruev6))

    print("T1 False: " + str(len(v6_dr_false_t1)))
    print("T2 False: " + str(len(v6_dr_false_t2)))
    print("T3 False: " + str(len(v6_dr_false_t3)))
    print("TX False: " + str(len(v6_dr_false_t0)))

    totalfalsev6 = len(v6_dr_false_t1) + len(v6_dr_false_t2) + len(v6_dr_false_t3) + len(v6_dr_false_t0)
    print("Total False: " + str(totalfalsev6))

    print("DR in %: " + str((totaltruev6/len(asnv6))*100))
    print("Total AS Count: " + str(len(asnv6)))

    print("\n")
    print("Both ########################################")
    print("T1 True: " + str(len(merged_t1_true)))
    print("T2 True: " + str(len(merged_t2_true)))
    print("T3 True: " + str(len(merged_t3_true)))
    print("TX True: " + str(len(merged_t0_true)))
    totaltruemerged = len(merged_t1_true) + len(merged_t2_true) + len(merged_t3_true) + len(merged_t0_true)
    print("Total True: " + str(totaltruemerged))

    print("T1 False: " + str(len(merged_t1_false)))
    print("T2 False: " + str(len(merged_t2_false)))
    print("T3 False: " + str(len(merged_t3_false)))
    print("TX False: " + str(len(merged_t0_false)))

    totalfalsemerged = len(merged_t1_false) + len(merged_t2_false) + len(merged_t3_false) + len(merged_t0_false)
    print("Total False: " + str(totalfalsemerged))

    print("DR in %: " + str((totaltruemerged/len(asnmerged))*100))
    print("Total AS Count: " + str(len(asnmerged)))

    print("\n")
    print("Summary ########################################")
    print("Only v4: " + str(len(only_v4_true)))
    print("Only v6: " + str(len(only_v6_true)))
    print("Both vX: " + str(len(both_true)))

    print(merged_t1_true)
    print(v4_dr_true_t1)
    print(v6_dr_true_t1)


resultprep()
