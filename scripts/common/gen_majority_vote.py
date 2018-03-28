#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================


def parse_csv(csv_in):
    """
    usage : use to parse OTB's confusion matrix
    IN
    csv_in [string] path to a csv file
    
    OUT
    matrix [collections.OrderedDict of collections.OrderedDict]

    example :
    if csv_in contain :
    #Reference labels (rows):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222
    #Produced labels (columns):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222,255
    11100,586,13,2,54,0,0,25,2,0,0,2,291,47,4,338
    434,14385,12,0,171,1,0,31,43,0,0,3,475,52,10,484
    98,8,3117,109,160,0,0,3,0,0,0,9,33,105,66,494
    4,0,38,571,5,0,0,3,0,0,0,1,13,9,0,47
    53,310,72,52,9062,0,1,431,27,0,0,0,459,56,16,1065
    37,40,4,0,4,0,0,6,1,0,0,0,49,11,1,59
    1,1,0,0,13,0,56,146,24,0,0,0,0,0,0,31
    41,158,6,4,200,0,42,4109,249,1,0,11,390,46,11,642
    50,76,1,3,20,0,17,478,957,3,0,12,58,7,3,315
    1,5,0,0,0,0,0,22,102,12,0,0,0,0,0,20
    0,0,0,0,83,0,0,12,0,0,41,0,3,0,0,109
    95,66,3,4,0,1,0,3,12,0,0,6599,3,9,0,50
    171,425,30,9,348,0,0,9,0,0,0,0,17829,67,3,585
    180,166,111,4,93,0,0,61,5,0,0,5,668,1213,14,451
    159,143,1,0,180,0,0,33,0,0,0,0,149,22,304,258
    
    print matrix[11][221]
    > 4
    print matrix[11][222]
    > 338
    print matrix[255]
    > OrderedDict([(11, 0), (12, 0),..., (255, 0)])
    """
    import collections
    import csv

    with open(csv_in, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        ref_lab = [elem.replace("#Reference labels (rows):","") for elem in csv_reader.next()]
        prod_lab = [elem.replace("#Produced labels (columns):","") for elem in csv_reader.next()]

        all_labels = sorted(map(int, list(set(ref_lab + prod_lab))))

        #construct confusion matrix structure and init it at 0
        matrix = collections.OrderedDict()
        for lab in all_labels:
            matrix[lab] = collections.OrderedDict()
            for l in all_labels:
                matrix[lab][l] = 0

        #fill-up confusion matrix
        csv_dict = csv.DictReader(csvfile, fieldnames=prod_lab)
        for row_num, row_ref in enumerate(csv_dict):
            for klass, value in row_ref.items():
                ref = int(ref_lab[row_num])
                prod = int(klass)
                matrix[ref][prod] += int(value)

    return matrix

def get_coeff(matrix):
    """
    """

    nan = -1000
    classes_labels = matrix.keys()

    OA_nom = sum([matrix[class_name][class_name] for class_name in matrix.keys()])
    nb_samples = sum([matrix[ref_class_name][prod_class_name] for ref_class_name in matrix.keys() for prod_class_name in matrix.keys()])
    
    if nb_samples != 0.0:
        OA = float(OA_nom)/float(nb_samples)
    else:
        OA = nan

    P_dic = {}
    R_dic = {}
    F_dic = {}
    luckyRate = 0.
    for classe_name in classes_labels:
        OA_class = matrix[classe_name][classe_name]
        P_denom = sum([matrix[ref][classe_name] for ref in classes_labels])
        R_denom = sum([matrix[classe_name][ref] for ref in classes_labels])
        if float(P_denom) != 0.0:
            P = float(OA_class) / float(P_denom)
        else:
            P = nan
        if float(R_denom) != 0.0:
            R = float(OA_class) / float(R_denom)
        else:
            R = nan
        if float(P + R) != 0.0:
            F = float(2.0 * P * R) / float(P + R)
        else:
            F = nan
        P_dic[classe_name] = P
        R_dic[classe_name] = R
        F_dic[classe_name] = F
    
        luckyRate += P_denom * R_denom

    K_denom = float((nb_samples * nb_samples) - luckyRate)
    K_nom = float((OA * nb_samples * nb_samples) - luckyRate)
    if K_denom != 0.0:
        K = K_nom / K_denom
    else:
        K = nan
            
    print P_dic
    print "-----------------"
    print R_dic
    print "-----------------"
    print F_dic
    print "-----------------"
    print OA
    print K


def generateMajorityVoteMap(cfg, workingDirectory=None):
    """
    """
    import os
    import shutil

    import serviceConfigFile as SCF
    import fileUtils as fut
    import otbAppli as otbApp

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    iota2_dir = cfg.getParam("chain", "outputPath")
    runs = cfg.getParam("chain", "runs")
    dataField = cfg.getParam("chain", "dataField")
    pixType = cfg.getParam("argClassification", "pixType")
    iota2_dir_final = os.path.join(iota2_dir, "final")

    try:
        undecidedlabel = cfg.getParam("chain", "majorityVoteMap_undecidedlabel")
    except:
        undecidedlabel = 255


    wd = iota2_dir_final
    wd_merge = os.path.join(iota2_dir_final, "majVoteValid")
    if workingDirectory:
        wd = workingDirectory
        wd_merge = workingDirectory

    final_classifications = [fut.FileSearch_AND(iota2_dir_final, True, "Classif_Seed_{}.tif".format(run))[0] for run in range(runs)]

    maj_vote_name = "MajorityVoting.tif"
    maj_vote_path = os.path.join(wd, maj_vote_name)
    
    maj_vote = otbApp.CreateFusionOfClassificationsApplication({"il": final_classifications,
                                                                "method": "majorityvoting",
                                                                "nodatalabel": "0",
                                                                "undecidedlabel": str(undecidedlabel),
                                                                "pixType": pixType,
                                                                "out": maj_vote_path})
    maj_vote.ExecuteAndWriteOutput()

    confusion_matrix = os.path.join(iota2_dir_final, "majVoteValid", "confusion_mat_maj_vote.csv")
    vector_val = fut.FileSearch_AND(os.path.join(iota2_dir_final, "majVoteValid"), True, "_majvote.sqlite")
    maj_vote_vec_name = "merge_valid_maj_vote"
    
    fut.mergeSQLite(maj_vote_vec_name, wd_merge,vector_val)

    confusion = otbApp.CreateComputeConfusionMatrixApplication({"in": maj_vote_path,
                                                                "out": confusion_matrix,
                                                                "ref": "vector",
                                                                "ref.vector.nodata": "0",
                                                                "ref.vector.in": os.path.join(wd_merge, maj_vote_vec_name+".sqlite"),
                                                                "ref.vector.field": dataField.lower(),
                                                                "nodatalabel": "0",
                                                                "ram": "5000"})
    confusion.ExecuteAndWriteOutput()
    conf_mat_dic = parse_csv(confusion_matrix)
    #conf_mat_dic.pop(255, None)
    coeff = get_coeff(conf_mat_dic)

    if workingDirectory:
        shutil.copy(maj_vote_path, iota2_dir_final)
        os.remove(maj_vote_path)
        shutil.copy(confusion_matrix, os.path.join(iota2_dir_final, "majVoteValid"))
        os.remove(confusion_matrix)
    
