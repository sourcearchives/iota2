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
import fileUtils as fu
from config import Config
import serviceConfigFile as SCF


def cleanRepo(outputPath):
    """
    remove from the directory learningSamples all unnecessary files
    """
    LearningContent = os.listdir(outputPath+"/learningSamples")
    for c_content in LearningContent:
        c_path = outputPath+"/learningSamples/"+c_content
        if os.path.isdir(c_path):
            shutil.rmtree(c_path)


def mergeSqlite(vectorList, outputVector):
    """
    IN 
    vectorList [list of strings] : vector's path to merge
    
    OUT
    outputVector [string] : output path
    """
    import sqlite3
    import shutil

    vectorList_cpy = [elem for elem in vectorList]

    def cleanSqliteDatabase(db, table):

        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        res = cursor.fetchall()
        res = [x[0] for x in res]
        if len(res) > 0:
            if table in res:
                cursor.execute("DROP TABLE %s;"%(table))
        conn.commit()
        cursor = conn = None
        
    if os.path.exists(outputVector):
        os.remove(outputVector)

    shutil.copy(vectorList_cpy[0],outputVector)

    if len(outputVector) > 1:
        del vectorList_cpy[0]
        
        conn = sqlite3.connect(outputVector)
        cursor = conn.cursor()
        for cpt, currentVector in enumerate(vectorList_cpy):
            cursor.execute("ATTACH '%s' as db%s;"%(currentVector,str(cpt)))
            cursor.execute("CREATE TABLE output2 AS SELECT * FROM db"+str(cpt)+".output;")
            cursor.execute("INSERT INTO output SELECT * FROM output2;")
            conn.commit()
            cleanSqliteDatabase(outputVector, "output2")
        cursor = conn = None


def vectorSamplesMerge(cfg,vectorList):

    regions_position = 2
    seed_position = 3
    
    if not isinstance(cfg,SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    outputPath = cfg.getParam('chain', 'outputPath')
    runs = cfg.getParam('chain', 'runs')
    mode = cfg.getParam('chain', 'executionMode')
    cleanRepo(outputPath)
    
    currentModel = os.path.split(vectorList[0])[-1].split("_")[regions_position]
    seed = os.path.split(vectorList[0])[-1].split("_")[seed_position].replace("seed","")

    shapeOut_name = "Samples_region_" + currentModel + "_seed" + str(seed) + "_learn"
    shapeOut_path = os.path.join(outputPath, "learningSamples", shapeOut_name)
    mergeSqlite(vectorList, shapeOut_path)
    
    for vector in vectorList:
        os.remove(vector)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function merge sqlite to feed training")
    parser.add_argument("-conf", help ="path to the configuration file (mandatory)",
                        dest="pathConf", required=True)

    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    vectorSamplesMerge(cfg)
