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

import ConfigParser
import os
import re
import logging
from sys import argv
import otbApplication as otb

from Common import OtbAppBank

logger = logging.getLogger(__name__)

def getOrtho(orthoList, pattern):
    """
    pattern example : "s1b(.*)ASC(.*)tif"
    """
    for ortho in orthoList:
        name = os.path.split(ortho)[-1].split("?")[0]
        compiled = re.compile(pattern)
        ms = compiled.search(name)
        try :
            ms.group(1).strip()
            yield ortho
        except:
            continue

def getDatesInOtbOutputName(otbObj):
    
    if isinstance(otbObj,str):	
        return int(otbObj.split("/")[-1].split("_")[4].split("t")[0])
    elif type(otbObj)==otb.Application:
        outputParameter = OtbAppBank.getInputParameterOutput(otbObj)
        return int(otbObj.GetParameterValue(outputParameter).split("/")[-1].split("_")[4].split("t")[0])


def compareDates(datesFile, dates):
    """
    """
    old_dates = []

    if os.path.exists(datesFile):
        with open(datesFile, "r") as f_dates:
            old_dates = [line.rstrip() for line in f_dates]
    new_dates = [date for date in dates if not date in old_dates]
    new_dates.sort()

    return new_dates


def remove_old_dates(img_list, new_dates):
    """remove dates already compute in outCore Stack
    """
    from Common import OtbAppBank

    date_pos = -1

    img_to_outcore = []
    for img in img_list:
        img_date = os.path.basename(img).split("_")[date_pos].replace(".tif","")
        if img_date in new_dates:
            img_to_outcore.append(img)
    return img_to_outcore
            
        
def main(ortho=None, configFile=None, dates=None, tileName=None, logger=logger):
    
    import ast
    from Common import FileUtils

    config = ConfigParser.ConfigParser()
    config.read(configFile)
    wMode = ast.literal_eval(config.get('Processing','writeTemporaryFiles'))
    stackFlag = ast.literal_eval(config.get('Processing','outputStack'))
    stdoutfile=None
    stderrfile=open("S1ProcessorErr.log",'a')
    RAMPerProcess=int(config.get('Processing','RAMPerProcess'))
    if "logging" in config.get('Processing','Mode').lower():
        stdoutfile=open("S1ProcessorOut.log",'a')
        stderrfile=open("S1ProcessorErr.log",'a')
    if "debug" in config.get('Processing','Mode').lower():
        stdoutfile=None
        stderrfile=None
    outputPreProcess = config.get('Paths','Output')
    wr = config.get('Filtering','Window_radius')

    directories=os.walk(outputPreProcess).next()
    SARFilter = []
    #OUTCOREs
    for d in directories[1]:
        s1_vv_DES_scene = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1(.*)"+d+"(.*)vv(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1_vv_DES_scene:
            outcore_s1_vv_DES = os.path.join(directories[0],d,"outcore_S1_vv_DES.tif")
            outcore_s1_vv_DES_dates = os.path.join(directories[0],d,"S1_vv_DES_dates.txt")
            new_outcore_s1_vv_DES_dates = compareDates(outcore_s1_vv_DES_dates, dates["s1_DES"])
            if new_outcore_s1_vv_DES_dates:
                FileUtils.WriteNewFile(outcore_s1_vv_DES_dates,
                                       "\n".join(dates["s1_DES"]))
            s1_vv_DES_outcore = remove_old_dates(s1_vv_DES_scene,
                                                 new_outcore_s1_vv_DES_dates)
            if s1_vv_DES_outcore or not os.path.exists(outcore_s1_vv_DES):
                s1_vv_DES_outcore = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1_vv_DES_outcore,
                                                                                "oc" : outcore_s1_vv_DES,
                                                                                "wr" : str(wr),
                                                                                "ram" : str(RAMPerProcess),
                                                                                "pixType" : "float"})
                logger.info("writing : {}".format(outcore_s1_vv_DES))
                s1_vv_DES_outcore.ExecuteAndWriteOutput()
                logger.info("{} : done".format(outcore_s1_vv_DES))

        s1_vh_DES_scene = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1(.*)"+d+"(.*)vh(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1_vh_DES_scene:
            outcore_s1_vh_DES = os.path.join(directories[0],d,"outcore_S1_vh_DES.tif")
            outcore_s1_vh_DES_dates = os.path.join(directories[0],d,"S1_vh_DES_dates.txt")
            new_outcore_s1_vh_DES_dates = compareDates(outcore_s1_vh_DES_dates, dates["s1_DES"])
            if new_outcore_s1_vh_DES_dates:
                FileUtils.WriteNewFile(outcore_s1_vh_DES_dates,
                                       "\n".join(dates["s1_DES"]))
            s1_vh_DES_outcore = remove_old_dates(s1_vh_DES_scene,
                                                 new_outcore_s1_vh_DES_dates)
            if s1_vh_DES_outcore or not os.path.exists(outcore_s1_vh_DES):
                s1_vh_DES_outcore = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1_vh_DES_outcore,
                                                                                "oc" : outcore_s1_vh_DES,
                                                                                "wr" : str(wr),
                                                                                "ram" : str(RAMPerProcess),
                                                                                "pixType" : "float"})
                logger.info("writing : {}".format(outcore_s1_vh_DES))
                s1_vh_DES_outcore.ExecuteAndWriteOutput()
                logger.info("{} : done".format(outcore_s1_vh_DES))
                                           
        s1_vv_ASC_scene = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1(.*)"+d+"(.*)vv(.*)ASC(.*)tif")], key=getDatesInOtbOutputName)
        if s1_vv_ASC_scene:
            outcore_s1_vv_ASC = os.path.join(directories[0],d,"outcore_S1_vv_ASC.tif")
            outcore_s1_vv_ASC_dates = os.path.join(directories[0],d,"S1_vv_ASC_dates.txt")
            new_outcore_s1_vv_ASC_dates = compareDates(outcore_s1_vv_ASC_dates, dates["s1_ASC"])
            if new_outcore_s1_vv_ASC_dates:
                FileUtils.WriteNewFile(outcore_s1_vv_ASC_dates,
                                       "\n".join(dates["s1_ASC"]))
            s1_vv_ASC_outcore = remove_old_dates(s1_vv_ASC_scene,
                                                 new_outcore_s1_vv_ASC_dates)
            if s1_vv_ASC_outcore or not os.path.exists(outcore_s1_vv_ASC):
                s1_vv_ASC_outcore = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1_vv_ASC_outcore,
                                                                                "oc" : outcore_s1_vv_ASC,
                                                                                "wr" : str(wr),
                                                                                "ram" : str(RAMPerProcess),
                                                                                "pixType" : "float"})
                logger.info("writing : {}".format(outcore_s1_vv_ASC))
                s1_vv_ASC_outcore.ExecuteAndWriteOutput()
                logger.info("{} : done".format(outcore_s1_vv_ASC))
        
        s1_vh_ASC_scene = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1(.*)"+d+"(.*)vh(.*)ASC(.*)tif")], key=getDatesInOtbOutputName)
        if s1_vh_ASC_scene:
            outcore_s1_vh_ASC = os.path.join(directories[0],d,"outcore_S1_vh_ASC.tif")
            outcore_s1_vh_ASC_dates = os.path.join(directories[0],d,"S1_vh_ASC_dates.txt")
            new_outcore_s1_vh_ASC_dates = compareDates(outcore_s1_vh_ASC_dates, dates["s1_ASC"])
            if new_outcore_s1_vh_ASC_dates:
                FileUtils.WriteNewFile(outcore_s1_vh_ASC_dates,
                                       "\n".join(dates["s1_ASC"]))
            s1_vh_ASC_outcore = remove_old_dates(s1_vh_ASC_scene,
                                                 new_outcore_s1_vh_ASC_dates)
            if s1_vh_ASC_outcore or not os.path.exists(outcore_s1_vh_ASC):
                s1_vh_ASC_outcore = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1_vh_ASC_outcore,
                                                                                "oc" : outcore_s1_vh_ASC,
                                                                                "wr" : str(wr),
                                                                                "ram" : str(RAMPerProcess),
                                                                                "pixType" : "float"})
                logger.info("writing : {}".format(outcore_s1_vh_ASC))
                s1_vh_ASC_outcore.ExecuteAndWriteOutput()
                logger.info("{} : done".format(outcore_s1_vh_ASC))
               
        try:
            os.makedirs(os.path.join(directories[0],d,"filtered"))
        except:
            pass

        #FILTERING
        if s1_vv_DES_scene:
            enl = os.path.join(directories[0],d,"filtered/enl_S1_vv_DES.tif")
            s1_vv_DES_filtered = os.path.join(directories[0],d,"filtered/S1_vv_DES_Filtered.tif")
            s1_vv_DES_filtered_app, a, b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1_vv_DES_scene,
                                                                                      "oc" : outcore_s1_vv_DES,
                                                                                      "wr" : str(wr),
                                                                                      "enl" : enl,
                                                                                      "ram" : str(RAMPerProcess),
                                                                                      "pixType" : "float",
                                                                                      "outputstack" : s1_vv_DES_filtered})

            SARFilter.append((s1_vv_DES_filtered_app, a, b))
        if s1_vh_DES_scene:
            enl = os.path.join(directories[0],d,"filtered/enl_S1_vh_DES.tif")
            s1_vh_DES_filtered = os.path.join(directories[0],d,"filtered/S1_vh_DES_Filtered.tif")
            s1_vh_DES_filtered_app, a, b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1_vh_DES_scene,
                                                                                      "oc" : outcore_s1_vh_DES,
                                                                                      "wr" : str(wr),
                                                                                      "enl" : enl,
                                                                                      "ram" : str(RAMPerProcess),
                                                                                      "pixType" : "float",
                                                                                      "outputstack" : s1_vh_DES_filtered})

            SARFilter.append((s1_vh_DES_filtered_app, a, b))
        if s1_vv_ASC_scene:
            enl = os.path.join(directories[0],d,"filtered/enl_S1_vv_ASC.tif")
            s1_vv_ASC_filtered = os.path.join(directories[0],d,"filtered/S1_vv_ASC_Filtered.tif")
            s1_vv_ASC_filtered_app, a, b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1_vv_ASC_scene,
                                                                                      "oc" : outcore_s1_vv_ASC,
                                                                                      "wr" : str(wr),
                                                                                      "enl" : enl,
                                                                                      "ram" : str(RAMPerProcess),
                                                                                      "pixType" : "float",
                                                                                      "outputstack" : s1_vv_ASC_filtered})

            SARFilter.append((s1_vv_ASC_filtered_app, a, b))
        if s1_vh_ASC_scene:
            enl = os.path.join(directories[0],d,"filtered/enl_S1_vh_ASC.tif")
            s1_vh_ASC_filtered = os.path.join(directories[0],d,"filtered/S1_vh_ASC_Filtered.tif")
            s1_vh_ASC_filtered_app, a, b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1_vh_ASC_scene,
                                                                                      "oc" : outcore_s1_vh_ASC,
                                                                                      "wr" : str(wr),
                                                                                      "enl" : enl,
                                                                                      "ram" : str(RAMPerProcess),
                                                                                      "pixType" : "float",
                                                                                      "outputstack" : s1_vh_ASC_filtered})

            SARFilter.append((s1_vh_ASC_filtered_app, a, b))
    return SARFilter

