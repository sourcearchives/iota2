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

import results_utils as ru


def remove_undecidedlabel(conf_mat_dic, undecidedlabel):
    """
    usage : use to remove samples with the undecidedlabel label from the
            confusion matrix
    """
    #remove prod labels
    for class_ref, prod_dict in conf_mat_dic.items():
        prod_dict.pop(undecidedlabel, None)
    
    #remove ref labels
    conf_mat_dic.pop(undecidedlabel, None)

    return conf_mat_dic

    
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
    nom_path = cfg.getParam("chain", "nomenclaturePath")
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
    #maj_vote.ExecuteAndWriteOutput()

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
    #confusion.ExecuteAndWriteOutput()
    conf_mat_dic = ru.parse_csv(confusion_matrix)
    conf_mat_dic = remove_undecidedlabel(conf_mat_dic, undecidedlabel)
    K, OA, P_dic, R_dic, F_dic = ru.get_coeff(conf_mat_dic)

    ru.print_results(iota2_dir_final, nom_path, conf_mat_dic, K, OA, P_dic, R_dic, F_dic)

    if workingDirectory:
        shutil.copy(maj_vote_path, iota2_dir_final)
        os.remove(maj_vote_path)
        shutil.copy(confusion_matrix, os.path.join(iota2_dir_final, "majVoteValid"))
        os.remove(confusion_matrix)
    
