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

def getOrtho(orthoList,pattern):
    """
    pattern example : "s1b(.*)ASC(.*)tif"
    """
    for ortho in orthoList:
        try:
            name = os.path.split(ortho.GetParameterValue("io.out"))[-1].split("?")[0]
        except:
            name = os.path.split(ortho.GetParameterValue("out"))[-1].split("?")[0]
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


def remove_old_dates(OTB_obj, new_dates):
    """remove dates already compute in outCore Stack
    """
    from Common import OtbAppBank
    output_param_name = OtbAppBank.getInputParameterOutput(OTB_obj[0])
    date_pos = -1
    
    img_list = [elem.GetParameterValue(output_param_name) for elem in OTB_obj]
    
    img_to_outcore = []
    for img, OTB_obj_date in zip(img_list, OTB_obj):
        img_date = os.path.basename(img).split("_")[date_pos].replace(".tif","")
        if img_date in new_dates:
            img_to_outcore.append(OTB_obj_date)

    return img_to_outcore
            
        
def main(ortho=None,configFile=None, dates=None, tileName=None, WorkingDirectory=None, logger=logger):
    
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
    
    need_filtering = {'s1aASC': True,
                      's1bDES': True,
                      's1aDES': True,
                      's1bASC': True}

    directories=os.walk(outputPreProcess).next()
    SARFilter = []
    #OUTCORE
    for d in directories[1]:
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            outs1aDES = os.path.join(directories[0],d,"outcore_S1aDES.tif")
            outs1aDES_dates = os.path.join(directories[0],d,"S1aDES_dates.txt")
            new_S1A_DES_dates = compareDates(outs1aDES_dates, dates["s1aDES"])
            s1aDESlist_out = s1aDESlist
            if new_S1A_DES_dates:
                FileUtils.WriteNewFile(outs1aDES_dates,
                                       "\n".join(dates["s1aDES"]))
            
            s1aDESlist_outcore = remove_old_dates(s1aDESlist_out, new_S1A_DES_dates)
            if s1aDESlist_outcore:
                need_filtering["s1aDES"] = True
                s1aDES = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1aDESlist_outcore,
                                                                     "oc" : outs1aDES,
                                                                     "wr" : str(wr),
                                                                     "ram" : str(RAMPerProcess),
                                                                     "pixType" : "float"})
                logger.info("writing : {}".format(outs1aDES))
                s1aDES.ExecuteAndWriteOutput()
                logger.info("{} : done".format(outs1aDES))
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            outs1aASC = os.path.join(directories[0],d,"outcore_S1aASC.tif")
            outs1aASC_dates = os.path.join(directories[0],d,"S1aASC_dates.txt")
            new_S1A_ASC_dates = compareDates(outs1aASC_dates, dates["s1aASC"])
            s1aASClist_out = s1aASClist
            if new_S1A_ASC_dates:
                FileUtils.WriteNewFile(outs1aASC_dates,
                                       "\n".join(dates["s1aASC"]))
            s1aASClist_outcore = remove_old_dates(s1aASClist_out, new_S1A_ASC_dates)
            if s1aASClist_outcore:
                need_filtering["s1aASC"] = True
                s1aASC = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1aASClist_outcore,
                                                                     "oc" : outs1aASC,
                                                                     "wr" : str(wr),
                                                                     "ram" : str(RAMPerProcess),
                                                                     "pixType" : "float"})
                logger.info("writing : {}".format(outs1aASC))
                s1aASC.ExecuteAndWriteOutput()                                            
                logger.info("{} done".format(outs1aASC))
                                           
        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            s1bDESlist_out = s1bDESlist
            outs1bDES = os.path.join(directories[0],d,"outcore_S1bDES.tif")
            outs1bDES_dates = os.path.join(directories[0],d,"S1bDES_dates.txt")
            new_S1B_DES_dates = compareDates(outs1bDES_dates, dates["s1bDES"])
            if new_S1B_DES_dates:
                FileUtils.WriteNewFile(outs1bDES_dates,
                                       "\n".join(dates["s1bDES"]))
            s1bDESlist_outcore = remove_old_dates(s1bDESlist_out, new_S1B_DES_dates)
            if s1bDESlist_outcore:
                need_filtering["s1bDES"] = True
                s1bDES = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1bDESlist_outcore,
                                                                     "oc" : outs1bDES,
                                                                     "wr" : str(wr),
                                                                     "ram" : str(RAMPerProcess),
                                                                     "pixType" : "float"})
                logger.info("writing : {}".format(outs1bDES))
                s1bDES.ExecuteAndWriteOutput()
                logger.info("{} done".format(outs1bDES))
            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            s1bASClist_out = s1bASClist
            outs1bASC = os.path.join(directories[0],d,"outcore_S1bASC.tif")
            outs1bASC_dates = os.path.join(directories[0],d,"S1bASC_dates.txt")
            new_S1B_ASC_dates = compareDates(outs1bASC_dates, dates["s1bASC"])
            if new_S1B_ASC_dates:
                FileUtils.WriteNewFile(outs1bASC_dates,
                                       "\n".join(dates["s1bASC"]))
            s1bASClist_outcore = remove_old_dates(s1bASClist_out, new_S1B_ASC_dates)
            if s1bASClist_outcore:
                need_filtering["s1bASC"] = True
                s1bASC = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1bASClist_outcore,
                                                                     "oc" : outs1bASC,
                                                                     "wr" : str(wr),
                                                                     "ram" : str(RAMPerProcess),
                                                                     "pixType" : "float"})
                logger.info("writing : {}".format(outs1bASC))
                s1bASC.ExecuteAndWriteOutput()
                logger.info("{} done".format(outs1bASC))
        try:
            os.makedirs(os.path.join(directories[0],d,"filtered"))
        except:
            pass

        #FILTERING
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            enl = os.path.join(directories[0],d,"filtered/enl_S1aDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aDES.tif")
            s1aDESlist_out = s1aDESlist
            if not stackFlag : stackFiltered = None

            s1aDES_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1aDESlist_out,
                                                                         "oc" : outs1aDES,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})

            SARFilter.append((s1aDES_last,a,b,s1aDESlist))
                                                        
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            enl = os.path.join(directories[0],d,"filtered/enl_S1aASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aASC.tif")
            s1aASClist_out = s1aASClist
            if not stackFlag : stackFiltered = None
            s1aASC_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1aASClist_out,
                                                                         "oc" : outs1aASC,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1aASC_last,a,b,s1aASClist))

        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            enl = os.path.join(directories[0],d,"filtered/enl_s1bDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bDES.tif")
            s1bDESlist_out = s1bDESlist
            if not stackFlag : stackFiltered = None
            s1bDES_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1bDESlist_out,
                                                                         "oc" : outs1bDES,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1bDES_last,a,b,s1bDESlist))
                                            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            enl = os.path.join(directories[0],d,"filtered/enl_S1bASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bASC.tif")
            s1bASClist_out=s1bASClist
            if not stackFlag:
                stackFiltered = None
            s1bASC_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1bASClist_out,
                                                                         "oc" : outs1bASC,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1bASC_last,a,b,s1bASClist))

    return SARFilter, need_filtering
if __name__=="__main__":
    main(argv[0])
	
