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


def generateMajorityVoteMap(iota2_dir, dataField, nom_path,
                            runs=1, pixType='uint8', undecidedlabel=255, keep_runs_results=True,
                            workingDirectory=None):
    """function use to generate a majority voting map

    get all classifications Classif_Seed_*.tif in the /final directory and fusion them
    under the raster call MajorityVoting.tif

    Parameters
    ----------

    iota2_dir : string
        path to the iota2's output path
    dataField : string
        data's field name
    nom_path : string
        path to the nomenclature file
    runs : int
        number of iota2 runs (random learning splits)
    pixType : string
        output pixel format (available in OTB)
    undecidedlabel : int
        label for label for un-decisions
    keep_runs_results : bool
        flag to inform if seeds results could be overwritten
    workingDirectory : string
        path to a working directory
    """
    import os
    import shutil

    import fileUtils as fut
    import otbAppli as otbApp

    iota2_dir_final = os.path.join(iota2_dir, "final")
    new_results_seed_file = "RESULTS_seeds.txt"
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
                                                                "ref.vector.in": os.path.join(wd_merge, maj_vote_vec_name + ".sqlite"),
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
