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
import shutil
import logging
from config import Config
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF
from Common.Utils import run

logger = logging.getLogger(__name__)


def check_duplicates(sqlite_file, logger=logger):
    """
    """
    import sqlite3 as lite
    import sys
    conn = lite.connect(sqlite_file)
    cursor = conn.cursor()
    sql_clause = "select * from output where ogc_fid in (select min(ogc_fid) from output group by GEOMETRY having count(*) >= 2);"
    cursor.execute(sql_clause)
    results = cursor.fetchall()

    if results:
        sql_clause = "delete from output where ogc_fid in (select min(ogc_fid) from output group by GEOMETRY having count(*) >= 2);"
        cursor.execute(sql_clause)
        conn.commit()
        logger.warning("{} were removed in {}".format(len(results), sqlite_file))


def cleanRepo(outputPath, logger=logger):
    """
    remove from the directory learningSamples all unnecessary files
    """
    LearningContent = os.listdir(outputPath + "/learningSamples")
    for c_content in LearningContent:
        c_path = outputPath + "/learningSamples/" + c_content
        if os.path.isdir(c_path):
            try:
                shutil.rmtree(c_path)
            except OSError:
                logger.debug(c_path + " does not exists")


def vectorSamplesMerge(cfg, vectorList, logger=logger):

    regions_position = 2
    seed_position = 3

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    outputPath = cfg.getParam('chain', 'outputPath')
    cleanRepo(outputPath)

    currentModel = os.path.split(vectorList[0])[-1].split("_")[regions_position]
    seed = os.path.split(vectorList[0])[-1].split("_")[seed_position].replace("seed", "")

    shapeOut_name = "Samples_region_" + currentModel + "_seed" + str(seed) + "_learn"
    logger.info("Vectors to merge in %s"%(shapeOut_name))
    logger.info("\n".join(vectorList))

    fu.mergeSQLite(shapeOut_name, os.path.join(outputPath, "learningSamples"), vectorList)

    check_duplicates(os.path.join(os.path.join(outputPath, "learningSamples"), shapeOut_name+".sqlite"))
    for vector in vectorList:
        os.remove(vector)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function merge sqlite to perform training step")
    parser.add_argument("-conf", help="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)
    parser.add_argument("-vl", help="list of vectorFiles to merge (mandatory)",
                        dest="vl", required=True)

    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    vectorSamplesMerge(cfg, args.vl)
