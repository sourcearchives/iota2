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
import os
import logging

from Common import FileUtils as fut

logger = logging.getLogger(__name__)


def compute_fusion_options(iota2_dir_final, final_classifications, method,
                           undecidedlabel, dempstershafer_mob, pixType,
                           fusion_path):
    """ use to determine fusion parameters
    """

    if method == "majorityvoting":
        options = {"il": final_classifications,
                   "method": method,
                   "nodatalabel": "0",
                   "undecidedlabel": str(undecidedlabel),
                   "pixType": pixType,
                   "out": fusion_path}
    else:
        confusionSeed = [fut.FileSearch_AND(os.path.join(iota2_dir_final, "TMP"),
                         True,
                         "Classif_Seed_{}.csv".format(run))[0] for run in range(len(final_classifications))]
        confusionSeed.sort()
        final_classifications.sort()
        options = {"il": final_classifications,
                   "method": "dempstershafer",
                   "nodatalabel": "0",
                   "undecidedlabel": str(undecidedlabel),
                   "method.dempstershafer.mob": dempstershafer_mob,
                   "method.dempstershafer.cmfl": confusionSeed,
                   "pixType": pixType,
                   "out": fusion_path}
    return options

def mergeFinalClassifications(iota2_dir, dataField, nom_path, colorFile,
                              runs=1, pixType='uint8', method="majorityvoting",
                              undecidedlabel=255, dempstershafer_mob="precision",
                              keep_runs_results=True, enableCrossValidation=False,
                              validationShape=None,
                              workingDirectory=None, logger=logger):
    """function use to merge classifications by majorityvoting or dempstershafer's method and evaluate it.

    get all classifications Classif_Seed_*.tif in the /final directory and fusion them
    under the raster call Classifications_fusion.tif. Then compute statistics using the
    results_utils library

    Parameters
    ----------

    iota2_dir : string
        path to the iota2's output path
    dataField : string
        data's field name
    nom_path : string
        path to the nomenclature file
    colorFile : string
        path to the color file description
    runs : int
        number of iota2 runs (random learning splits)
    pixType : string
        output pixel format (available in OTB)
    method : string
        fusion's method (majorityvoting/dempstershafer)
    undecidedlabel : int
        label for label for un-decisions
    dempstershafer_mob : string
        mass of belief measurement (precision/recall/accuracy/kappa)
    keep_runs_results : bool
        flag to inform if seeds results could be overwritten
    enableCrossValidation : bool
        flag to inform if cross validation is enable
    validationShape : string
        path to a shape dedicated to validate fusion of classifications
    workingDirectory : string
        path to a working directory

    See Also
    --------

    results_utils.gen_confusion_matrix_fig
    results_utils.stats_report
    """
    import shutil

    from Common import OtbAppBank as otbApp
    from Validation import ResultsUtils as ru
    from Common import CreateIndexedColorImage as color

    fusion_name = "Classifications_fusion.tif"
    new_results_seed_file = "RESULTS_seeds.txt"
    fusion_vec_name = "fusion_validation"#without extension
    confusion_matrix_name = "fusionConfusion.png"

    if not method in ["majorityvoting", "dempstershafer"]:
        err_msg = "the fusion method must be 'majorityvoting' or 'dempstershafer'"
        logger.error(err_msg)
        raise Exception(err_msg)
    if not dempstershafer_mob in ["precision", "recall", "accuracy", "kappa"]:
        err_msg = "the dempstershafer MoB must be 'precision' or 'recall' or 'accuracy' or 'kappa'"
        logger.error(err_msg)
        raise Exception(err_msg)

    iota2_dir_final = os.path.join(iota2_dir, "final")
    wd = iota2_dir_final
    wd_merge = os.path.join(iota2_dir_final, "merge_final_classifications")
    if workingDirectory:
        wd = workingDirectory
        wd_merge = workingDirectory

    final_classifications = [fut.FileSearch_AND(iota2_dir_final, True, "Classif_Seed_{}.tif".format(run))[0] for run in range(runs)]
    fusion_path = os.path.join(wd, fusion_name)

    fusion_options = compute_fusion_options(iota2_dir_final, final_classifications,
                                            method, undecidedlabel,
                                            dempstershafer_mob, pixType,
                                            fusion_path)
    logger.debug("fusion options:")
    logger.debug(fusion_options)
    fusion_app = otbApp.CreateFusionOfClassificationsApplication(fusion_options)
    logger.debug("START fusion of final classifications")
    fusion_app.ExecuteAndWriteOutput()
    logger.debug("END fusion of final classifications")

    fusion_color_index = color.CreateIndexedColorImage(fusion_path,
                                                       colorFile,
                                                       co_option=["COMPRESS=LZW"])
    
    confusion_matrix = os.path.join(iota2_dir_final, "merge_final_classifications", "confusion_mat_maj_vote.csv")
    if enableCrossValidation is False:
        vector_val = fut.FileSearch_AND(os.path.join(iota2_dir_final, "merge_final_classifications"), True, "_majvote.sqlite")
    else :
        vector_val = fut.FileSearch_AND(os.path.join(iota2_dir, "dataAppVal"), True, "val.sqlite")
    if validationShape:
        validation_vector = validationShape
    else:
        fut.mergeSQLite(fusion_vec_name, wd_merge, vector_val)
        validation_vector = os.path.join(wd_merge, fusion_vec_name + ".sqlite")

    confusion = otbApp.CreateComputeConfusionMatrixApplication({"in": fusion_path,
                                                                "out": confusion_matrix,
                                                                "ref": "vector",
                                                                "ref.vector.nodata": "0",
                                                                "ref.vector.in": validation_vector,
                                                                "ref.vector.field": dataField.lower(),
                                                                "nodatalabel": "0",
                                                                "ram": "5000"})
    confusion.ExecuteAndWriteOutput()

    maj_vote_conf_mat = os.path.join(iota2_dir_final, confusion_matrix_name)
    ru.gen_confusion_matrix_fig(csv_in=confusion_matrix, out_png=maj_vote_conf_mat,
                                nomenclature_path=nom_path, undecidedlabel=undecidedlabel, dpi=900)

    if keep_runs_results:
        seed_results = fut.FileSearch_AND(iota2_dir_final, True, "RESULTS.txt")[0]
        shutil.copy(seed_results, os.path.join(iota2_dir_final, new_results_seed_file))

    maj_vote_report = os.path.join(iota2_dir_final, "RESULTS.txt")

    ru.stats_report(csv_in=[confusion_matrix], nomenclature_path=nom_path, out_report=maj_vote_report,
                    undecidedlabel=undecidedlabel)

    if workingDirectory:
        shutil.copy(fusion_path, iota2_dir_final)
        shutil.copy(fusion_color_index, iota2_dir_final)
        os.remove(fusion_path)
