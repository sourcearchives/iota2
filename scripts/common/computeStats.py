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

import sqlite3 as lite
import argparse
import shutil
import math
import os
import time
from collections import OrderedDict
import ogr
import scipy.stats as stats
from config import Config
from Common import FileUtils as fut
from Validation import plotCor as correlation


def cleanSqliteDatabase(db, table):

    conn2 = lite.connect(db)
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT name FROM sqlite_master WHERE type='table';")
    res = cursor2.fetchall()
    res = [x[0] for x in res]
    if len(res) > 0:
        if table in res:
            cursor2.execute("DROP TABLE %s;"%(table))
    cursor2 = conn2 = None

class StdevFunc:

    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1

    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1

    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))

class spearmanrFunc:
    def __init__(self):
        self.samples1 = []
        self.samples2 = []
    def step(self, v1, v2):
        self.samples1.append(v1)
        self.samples2.append(v2)
    def finalize(self):
        return stats.spearmanr(self.samples1, self.samples2)[0]

def computeStatistics(finalDataBasePath, dataField):

    conn = lite.connect(finalDataBasePath)
    cursor = conn.cursor()
    cursor.execute("select name from sqlite_master where type = 'table';")
    tableName = str(cursor.fetchall()[-1][0])

    # Add function stdev to sqlite database
    conn.create_aggregate("stdev", 1, StdevFunc)
    conn.create_aggregate("spearmanr", 2, spearmanrFunc)
    cursor = conn.cursor()

    SQL = "SELECT "+dataField+",avg(validity),stdev(validity),avg(confidence),\
           stdev(confidence),spearmanr(validity,confidence)\
           FROM "+tableName+" GROUP BY "+dataField+";"

    cursor.execute(SQL)
    statistics = cursor.fetchall()

    statDico = OrderedDict()
    for currentClass, AVGval, STDval, AVGconf, STDconf, SPEAR in statistics:
        statDico[str(currentClass)] = {"avgVal":AVGval, "stdVal":STDval, \
                                       "avgConf":AVGconf, "stdConf":STDconf, \
                                       "spearman":SPEAR}
    return statDico

def plotRelation(finalDataBasePath, dataField, seed, iota2Folder):

    outputs = []
    nomenclature = {10:"annualCrop",
                    11:"ete",
                    12:"hiver",
                    211:"prairie",
                    221:"verger",
                    222:"vigne",
                    223:"olivier",
                    224:"arboriculture",
                    31:"foret feuillus",
                    32:"foret coniferes",
                    33:"forets melangees",
                    34:"pelouses",
                    35:"estives-landes",
                    36:"lande ligneuse",
                    41:"bati",
                    42:"bati diffus",
                    43:"zones ind et com",
                    44:"surface route",
                    45:"surfaces minerales",
                    46:"plages et dunes",
                    51:"eau",
                    52:"mer et oceans",
                    53:"glaciers ou neiges et",
                    255:"autres"}
    AllClasses = sorted(fut.getFieldElement(finalDataBasePath, driverName="SQLite", field=dataField, mode="unique", elemType="int"))
    
    #init
    valuesByClass = OrderedDict()
    for cClass in AllClasses:
        valuesByClass[cClass] = []
    
    driver = ogr.GetDriverByName("SQLite")
    dataSource = driver.Open(finalDataBasePath, 0)
    layer = dataSource.GetLayer()
    
    minVal = 1000000
    maxVal = 0
    minConf = 100
    maxConf = 0
    
    for feature in layer:
        val = feature.GetField("validity")
        if val > maxVal:
            maxVal = val
        if val < minVal:
            minVal = val
        conf = feature.GetField("confidence")
        if conf > maxConf:
            maxConf = conf
        if conf < minConf:
            minConf = conf
        cClass = feature.GetField(dataField)
        valuesByClass[cClass].append((conf, val))
    
    for cClass in valuesByClass:
        y = [cX for cX, cY in valuesByClass[cClass]]
        x = [cY for cX, cY in valuesByClass[cClass]]
        outputPath = iota2Folder+"/final/TMP/"+nomenclature[cClass].replace(" ", "_")+"_confFValid_Seed_"+str(seed)+".png"
        print "Creating : "+outputPath
        #title="Confidence = f( Validity ) : Class :"+nomenclature[cClass]
        parametres = correlation.Parametres()
        parametres.xlims = [minVal, maxVal]
        parametres.ylims = [minConf, maxConf]
        parametres.xBinStep = 1
        parametres.yBinStep = 1
        correlation.plotCorrelation(x, y, "Validity", "Confidence", outputPath, parametres)
        outputs.append(outputPath)
    return outputs
    
def computeStats(pathConf, wD=None):

    dataField = Config(file(pathConf)).chain.dataField
    iota2Folder = Config(file(pathConf)).chain.outputPath
    runs = Config(file(pathConf)).chain.runs
    workingDirectory = iota2Folder+"/final/TMP"
    if wD:
        workingDirectory = wD
    
    statsBySeed = []
    for seed in range(runs):
        #Get sqlites
        dataBase = fut.FileSearch_AND(iota2Folder+"/final/TMP", True, ".sqlite", "extraction", "learn")#stats only on learnt polygons
        #dataBase = fut.FileSearch_AND("/work/OT/theia/oso/TMP/sampleExtraction", True, ".sqlite", "extraction")
        finalDataBaseName = "statsDataBase_run_"+str(seed)+".sqlite"#will contain all data base
        finalDataBasePath = workingDirectory+"/"+finalDataBaseName

        if os.path.exists(finalDataBasePath):
            os.remove(finalDataBasePath)
        
        shutil.copy(dataBase[0], finalDataBasePath)
        del dataBase[0]
        fields = "GEOMETRY,"+",".join(fut.getAllFieldsInShape(finalDataBasePath, driver='SQLite'))
        
        conn = lite.connect(finalDataBasePath)
        cursor = conn.cursor()
        cursor.execute("select name from sqlite_master where type = 'table';")
        tableName = str(cursor.fetchall()[-1][0])
        
        print "Fill up statistics dataBase"
        for currentDataBase in dataBase:
            print ("Add dataBase : {}".format(currentDataBase))
            cursor.execute("ATTACH '%s' as db2;"%(currentDataBase))
            cursor.execute("CREATE TABLE output2 AS SELECT * FROM db2.output;")
            cursor.execute("INSERT INTO "+tableName+"("+fields+") SELECT "+fields+" FROM output2;")
            conn.commit()
            conn = cursor = None
            conn = lite.connect(finalDataBasePath)
            cursor = conn.cursor()
            cleanSqliteDatabase(finalDataBasePath, "output2")

        #plot relation
        plotsSeed = plotRelation(finalDataBasePath, dataField, seed, iota2Folder)
        #Compute statistics
        print "Compute statistics"
        statsByClass = computeStatistics(finalDataBasePath, dataField)
        statsBySeed.append(statsByClass)

    return statsBySeed


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="from points vector, compute stats")
    parser.add_argument("-wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)", dest="pathConf", required=True)
    args = parser.parse_args()

    statsBySeed = computeStats(args.pathConf, args.pathWd)
    print statsBySeed
    """
    Example :
    python computeStats.py -wd /work/OT/theia/oso/TMP/sampleExtraction -conf /home/uz/vincenta/config/configS1S2_4Tiles_multiSARdespeckle.cfg
    """
    
    
    
    
    
    
    
    
    
    
