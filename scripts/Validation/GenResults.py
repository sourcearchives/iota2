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

import argparse
import os
import heapq
import numpy as np
from scipy import stats
from Common import FileUtils as fu
from Common.Utils import run


def genResults(pathRes, pathNom):
    """
    generate IOTA² final report
    """
    import ResultsUtils as resU

    all_csv = fu.FileSearch_AND(pathRes+"/TMP", True, "Classif", ".csv")

    resU.stats_report(all_csv, pathNom, os.path.join(pathRes, "RESULTS.txt"))
    
    for seed_csv in all_csv:
        name, ext = os.path.splitext(os.path.basename(seed_csv))
        out_png = os.path.join(pathRes, "Confusion_Matrix_{}.png".format(name))
        resU.gen_confusion_matrix_fig(seed_csv, out_png, pathNom,
                                      undecidedlabel=None, dpi=900,
                                      write_conf_score=False, grid_conf=True)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function shape classifications (fake fusion and tiles priority)")
    parser.add_argument("-path.res", help="path to the folder which contains classification's results (mandatory)", dest="pathRes", required=True)
    parser.add_argument("-path.nomenclature", help="path to the nomenclature (mandatory)", dest="pathNom", required=True)    
    args = parser.parse_args()

    genResults(args.pathRes,args.pathNom)


































