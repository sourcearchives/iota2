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
    """
    import collections
    import csv

    """
#Reference labels (rows):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222
#Produced labels (columns):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222,255
11142,595,13,2,22,0,0,60,26,0,0,7,224,26,2,412
350,14836,18,1,132,0,0,58,6,0,0,0,480,45,6,440
125,5,2819,25,82,0,0,10,0,0,0,3,19,47,0,253
3,1,72,638,44,0,0,7,0,0,0,0,11,4,0,121
21,481,154,17,9424,1,0,118,19,0,0,2,1074,69,0,654
10,25,9,0,25,0,0,1,0,0,0,0,66,13,1,32
2,1,0,0,16,0,71,174,17,0,0,4,0,1,0,25
67,86,16,0,174,2,115,2532,140,0,0,1,311,30,3,454
17,52,1,1,64,0,19,576,1015,0,0,5,68,10,0,265
18,2,0,0,0,0,1,27,103,17,0,1,1,1,0,16
0,0,0,0,79,0,0,9,0,0,118,0,0,0,0,42
22,60,102,0,21,0,0,2,3,0,0,2322,3,5,0,91
194,488,29,6,346,0,0,20,1,0,0,3,16424,76,0,530
169,129,99,15,61,0,0,45,0,0,0,2,560,1469,3,332
95,274,12,0,70,0,0,245,0,0,0,0,236,19,183,337
    """
    with open(csv_in, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        ref_lab = [elem.replace("#Reference labels (rows):","") for elem in csv_reader.next()]
        prod_lab = [elem.replace("#Produced labels (columns):","") for elem in csv_reader.next()]

        all_labels = sorted(map(int, list(set(ref_lab + prod_lab))))

        #construct confusion matrix structure and init it at "0"
        matrix = collections.OrderedDict()
        for lab in all_labels:
            matrix[lab] = collections.OrderedDict()
            matrix[lab][lab] = 0
        print matrix

        #init confusion matrix
        
        #fill-up confusion matrix
        pause = raw_input("check")
        csv_dict = csv.DictReader(csvfile, fieldnames=prod_lab)
        for row in csv_dict:
            print row
            pause = raw_input("STOP")


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

    parse_csv(confusion_matrix)
    
    if workingDirectory:
        shutil.copy(maj_vote_path, iota2_dir_final)
        os.remove(maj_vote_path)
        shutil.copy(confusion_matrix, os.path.join(iota2_dir_final, "majVoteValid"))
        os.remove(confusion_matrix)
    
