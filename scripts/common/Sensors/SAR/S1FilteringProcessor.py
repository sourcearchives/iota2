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
from sys import argv
import otbApplication as otb

from Common import OtbAppBank

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
    
def main(ortho=None,configFile=None, dates=None, WorkingDirectory=None):
    
    import ast

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

    reset_outcore = config.get('Filtering','Reset_outcore')
    
    need_filtering = {'s1aASC': True,
                      's1bDES': True,
                      's1aDES': True,
                      's1bASC': True}

    directories=os.walk(outputPreProcess).next()
    SARFilter = []
    for d in directories[1]:
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            outs1aDES = os.path.join(directories[0],d,"outcore_S1aDES.tif")
            outs1aDES_dates = os.path.join(directories[0],d,"S1aDES_dates.txt")
            print outs1aDES_dates
            pause = raw_input("W8")
            s1aDESlist_out = s1aDESlist
            if wMode or not stackFlag: 
                s1aDESlist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            
            s1aDES = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1aDESlist_out,
                                                                 "oc" : outs1aDES,
                                                                 "wr" : str(wr),
                                                                 "ram" : str(RAMPerProcess),
                                                                 "pixType" : "float"})
            
            if not os.path.exists(outs1aDES):
                s1aDES.ExecuteAndWriteOutput()
            
                                                        
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            s1aASClist_out = s1aASClist
            if wMode or not stackFlag: 
                s1aASClist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            outs1aASC = os.path.join(directories[0],d,"outcore_S1aASC.tif")
            s1aASC = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1aASClist_out,
                                                                 "oc" : outs1aASC,
                                                                 "wr" : str(wr),
                                                                 "ram" : str(RAMPerProcess),
                                                                 "pixType" : "float"})
            if wMode or not stackFlag : s1aASC.ExecuteAndWriteOutput()                                            
            else : s1aASC.Execute()
                                           
        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            s1bDESlist_out = s1bDESlist
            if wMode or not stackFlag: 
                s1bDESlist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            outs1bDES = os.path.join(directories[0],d,"outcore_S1bDES.tif")
            s1bDES = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1bDESlist,
                                                                 "oc" : outs1bDES,
                                                                 "wr" : str(wr),
                                                                 "ram" : str(RAMPerProcess),
                                                                 "pixType" : "float"})
            if wMode or not stackFlag : s1bDES.ExecuteAndWriteOutput()
            else : s1bDES.Execute()
            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            s1bASClist_out = s1bASClist
            if wMode or not stackFlag: 
                s1bASClist = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            outs1bASC = os.path.join(directories[0],d,"outcore_S1bASC.tif")
            s1bASC = OtbAppBank.CreateMultitempFilteringOutcore({"inl" : s1bASClist,
                                                                 "oc" : outs1bASC,
                                                                 "wr" : str(wr),
                                                                 "ram" : str(RAMPerProcess),
                                                                 "pixType" : "float"})
            if wMode or not stackFlag: s1bASC.ExecuteAndWriteOutput()       
            else : s1bASC.Execute()                                     

        try:
            os.makedirs(os.path.join(directories[0],d,"filtered"))
        except:
            pass
            
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            outs1aDES = os.path.join(directories[0],d,"outcore_S1aDES.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1aDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aDES.tif")
            s1aDES_out = s1aDES
            s1aDESlist_out = s1aDESlist
            if wMode or not stackFlag:
                s1aDESlist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
                s1aDES_out = s1aDES.GetParameterValue("oc")
            if not stackFlag : stackFiltered = None
            s1aDES_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1aDESlist_out,
                                                                         "oc" : s1aDES_out,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})

            SARFilter.append((s1aDES_last,s1aDES,a,b,s1aDESlist))
                                                        
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            outs1aASC = os.path.join(directories[0],d,"outcore_S1aASC.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1aASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aASC.tif")
            s1aASC_out = s1aASC
            s1aASClist_out = s1aASClist
            if wMode or not stackFlag:
                s1aASC_out = s1aASC.GetParameterValue("oc")
                s1aASClist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            if not stackFlag : stackFiltered = None
            s1aASC_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1aASClist_out,
                                                                         "oc" : s1aASC_out,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1aASC_last,s1aASC,a,b,s1aASClist))

        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            outs1bDES = os.path.join(directories[0],d,"outcore_S1bDES.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_s1bDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bDES.tif")
            s1bDES_out = s1bDES
            s1bDESlist_out = s1bDESlist
            if wMode or not stackFlag:
                s1bDES_out = s1bDES.GetParameterValue("oc")
                s1bDESlist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            if not stackFlag : stackFiltered = None
            s1bDES_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1bDESlist_out,
                                                                         "oc" : s1bDES_out,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1bDES_last,s1bDES,a,b,s1bDESlist))
                                            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            outs1bASC = os.path.join(directories[0],d,"outcore_S1bASC.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1bASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bASC.tif")
            s1bASClist_out=s1bASClist
            s1bASC_out=s1bASC
            if wMode or not stackFlag:
                s1bASClist_out = sorted([currentOrtho.GetParameterValue(OtbAppBank.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
                s1bASC_out = s1bASC.GetParameterValue("oc")
            if not stackFlag:
                stackFiltered = None
            s1bASC_last,a,b = OtbAppBank.CreateMultitempFilteringFilter({"inl" : s1bASClist_out,
                                                                         "oc" : s1bASC_out,
                                                                         "wr" : str(wr),
                                                                         "enl" : enl,
                                                                         "ram" : str(RAMPerProcess),
                                                                         "pixType" : "float",
                                                                         "outputstack" : stackFiltered})
            SARFilter.append((s1bASC_last,s1bASC,a,b,s1bASClist))

    return SARFilter, need_filtering
if __name__=="__main__":
    main(argv[0])
	
