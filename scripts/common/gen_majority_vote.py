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
    keep_runs_results = cfg.getParam('chain', 'keep_runs_results')
    new_results_seed_file = "RESULTS_seeds.txt"

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

    fut.mergeSQLite(maj_vote_vec_name, wd_merge, vector_val)

    confusion = otbApp.CreateComputeConfusionMatrixApplication({"in": maj_vote_path,
                                                                "out": confusion_matrix,
                                                                "ref": "vector",
                                                                "ref.vector.nodata": "0",
                                                                "ref.vector.in": os.path.join(wd_merge, maj_vote_vec_name+".sqlite"),
                                                                "ref.vector.field": dataField.lower(),
                                                                "nodatalabel": "0",
                                                                "ram": "5000"})
    confusion.ExecuteAndWriteOutput()

    maj_vote_conf_mat = os.path.join(iota2_dir_final, "MajVoteConfusion.png")
    ru.gen_confusion_matrix_fig(csv_in=confusion_matrix, out_png=maj_vote_conf_mat,
                                nomenclature_path=nom_path, undecidedlabel=undecidedlabel, dpi=900)

    if keep_runs_results:
        seed_results = fut.FileSearch_AND(iota2_dir_final, True, "RESULTS.txt")[0]
        shutil.copy(seed_results, os.path.join(iota2_dir_final, new_results_seed_file))
        
    maj_vote_report = os.path.join(iota2_dir_final, "RESULTS.txt")
    ru.stats_report(csv_in=confusion_matrix, nomenclature_path=nom_path, out_report=maj_vote_report,
                    undecidedlabel=undecidedlabel)

    if workingDirectory:
        shutil.copy(maj_vote_path, iota2_dir_final)
        os.remove(maj_vote_path)
    
