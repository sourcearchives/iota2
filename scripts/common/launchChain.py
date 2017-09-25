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

import argparse, os
import fileUtils as fu
from config import Config
import serviceConfigFile as SCF
import codeStrings

def gen_oso_parallel(cfg):

    Fileconfig = cfg.pathConf

    PYPATH = cfg.getParam('chain', 'pyAppPath')
    NOMENCLATURE= cfg.getParam('chain', 'nomenclaturePath')
    JOBPATH= cfg.getParam('chain', 'jobsPath')
    TESTPATH= cfg.getParam('chain', 'outputPath')
    LISTTILE= cfg.getParam('chain', 'listTile')
    TILEPATH= cfg.getParam('chain', 'featuresPath')
    L5PATH= cfg.getParam('chain', 'L5Path')
    L8PATH= cfg.getParam('chain', 'L8Path')
    S2PATH= cfg.getParam('chain', 'S2Path')
    S1PATH= cfg.getParam('chain', 'S1Path')
    GROUNDTRUTH= cfg.getParam('chain', 'groundTruth')
    DATAFIELD= cfg.getParam('chain', 'dataField')
    Nsample= cfg.getParam('chain', 'runs')
    MODE= cfg.getParam('chain', 'mode')
    MODEL= cfg.getParam('chain', 'model')
    REGIONFIELD= cfg.getParam('chain', 'regionField')
    PATHREGION= cfg.getParam('chain', 'regionPath')
    LOGPATH= cfg.getParam('chain', 'logPath')
    CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
    chainName=cfg.getParam('chain', 'chainName')
    REARRANGE_FLAG = cfg.getParam('argTrain', 'rearrangeModelTile')
    REARRANGE_PATH = cfg.getParam('argTrain', 'rearrangeModelTile_out')
    COLORTABLE = cfg.getParam('chain', 'colorTable')
    MODE_OUT_Rsplit = cfg.getParam('chain', 'mode_outside_RegionSplit')
    TRAIN_MODE = cfg.getParam('argTrain', 'shapeMode')
    outputStat = cfg.getParam('chain', 'outputStatistics')
    BINDING = "True" #Always true

    pathChain = JOBPATH+"/"+chainName+".pbs"
    chainFile = open(pathChain,"w")
    chainFile.write(codeStrings.parallelChainStep1%(JOBPATH,PYPATH,LOGPATH,
                    NOMENCLATURE,JOBPATH,PYPATH,TESTPATH,LISTTILE,TILEPATH,
                    L8PATH,L5PATH,S2PATH,S1PATH,Fileconfig,GROUNDTRUTH,
                    DATAFIELD,Nsample,Fileconfig,MODE,MODEL,REGIONFIELD,
                    PATHREGION,REARRANGE_PATH,COLORTABLE))
    if MODE != "outside":
        chainFile.write(codeStrings.parallelChainStep2)
    else :
        chainFile.write(codeStrings.parallelChainStep3)
    chainFile.write(codeStrings.parallelChainStep4)

    if MODE == "outside" and CLASSIFMODE == "fusion" and not REARRANGE_FLAG:
        chainFile.write(codeStrings.parallelChainStep5)

    elif CLASSIFMODE == "fusion" and REARRANGE_FLAG:
        chainFile.write(codeStrings.parallelChainStep6)
    else:
        chainFile.write(codeStrings.parallelChainStep7)

    if TRAIN_MODE != "points":
        chainFile.write(codeStrings.parallelChainStep8)
    elif TRAIN_MODE == "points" and BINDING == "False":
        chainFile.write(codeStrings.parallelChainStep8_b)
    elif TRAIN_MODE == "points" and BINDING == "True":
        chainFile.write(codeStrings.parallelChainStep8_c)

    if CLASSIFMODE == "separate":
        chainFile.write(codeStrings.parallelChainStep9)
    elif CLASSIFMODE == "fusion" and MODE !="one_region":
        chainFile.write(codeStrings.parallelChainStep10)
    elif CLASSIFMODE == "fusion" and MODE =="one_region":
        raise Exception("you can't choose the 'one region' mode and use the fusion mode together")
    if outputStat == 'True':
        chainFile.write(codeStrings.parallelChainStep11)
    chainFile.close()
    return pathChain

def gen_oso_sequential(cfg):

    MODE = cfg.getParam('chain', 'mode')
    CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')

    if CLASSIFMODE == "fusion" and MODE == "one_region":
        raise Exception("you can't choose the 'one region' mode and use the fusion mode together")

    import launchChainSequential as lcs
    
    # Launch chain in sequential mode
    lcs.launchChainSequential(cfg)


#def gen_jobGenCmdFeatures(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenCmdFeatures%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchFeat(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchFeat%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobEnvelope(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobEnvelope%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenerateRegionShape(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenerateRegionShape%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobRegionByTiles(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobRegionByTiles%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobExtractactData(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobExtractactData%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobDataAppVal(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobDataAppVal%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobVectorSampler(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobVectorSampler%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenSamplesMerge(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenSamplesMerge%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobCmdSplitShape(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobCmdSplitShape%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobSplitShape(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobSplitShape%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobRearrange(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobRearrange%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenCmdStat(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenCmdStat%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchFusion(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchFusion%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchStat(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchStat%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenCmdTrain(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenCmdTrain%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchTrain(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchTrain%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenCmdClass(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenCmdClass%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchClass(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchClass%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobCmdFusion(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobCmdFusion%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobNoData(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobNoData%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobClassifShaping(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobClassifShaping%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenCmdConf(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenCmdConf%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchConfusion(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenJobLaunchConfusion%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobfusionConfusion(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobfusionConfusion%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenResults(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobGenResults%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobGenJobLaunchOutStat(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.GenJobLaunchOutStat%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()
#
#def gen_jobMergeOutStat(JOBPATH, LOGPATH, Fileconfig):
#    jobFile = open(JOBPATH, "w")
#    jobFile.write(codeStrings.jobMergeOutStat%(LOGPATH, LOGPATH, Fileconfig))
#    jobFile.close()


def gen_job(JOBPATH, LOGPATH, Fileconfig, name):
    """
        Generic method to generated job pbs
    """
    jobFile = open(JOBPATH, "w")
    if hasattr(codeStrings, name):
        tmpVar = getattr(codeStrings, name)
        jobFile.write(tmpVar%(LOGPATH, LOGPATH, Fileconfig))
    jobFile.close()


def genJobs(Fileconfig):

    f = file(Fileconfig)
    cfg = Config(f)

    LOGPATH = cfg.chain.logPath
    JOBPATH = cfg.chain.jobsPath

    jobGenCmdFeatures = JOBPATH+"/genCmdFeatures.pbs"
    jobGenJobLaunchFeat = JOBPATH+"/genJobLaunchFeat.pbs"
    jobEnvelope = JOBPATH+"/envelope.pbs"
    jobGenerateRegionShape = JOBPATH+"/generateRegionShape.pbs"
    jobRegionByTiles = JOBPATH+"/regionsByTiles.pbs"
    jobExtractactData = JOBPATH+"/genJobExtractData.pbs"
    jobGenJobDataAppVal = JOBPATH+"/genJobDataAppVal.pbs"
    jobGenJobVectorSampler = JOBPATH+"/genJobVectorSampler.pbs"
    jobGenSamplesMerge = JOBPATH+"/samplesMerge.pbs"
    jobCmdSplitShape = JOBPATH+"/genCmdsplitShape.pbs"
    jobGenJobSplitShape = JOBPATH+"/genJobsplitShape.pbs"
    jobRearrange = JOBPATH+"/reArrangeModel.pbs"
    jobGenCmdStat = JOBPATH+"/genCmdStats.pbs"
    jobGenJobLaunchStat = JOBPATH+"/genJobLaunchStat.pbs"
    jobGenCmdTrain = JOBPATH+"/genCmdTrain.pbs"
    jobGenJobLaunchTrain = JOBPATH+"/genJobLaunchTrain.pbs"
    jobGenCmdClass = JOBPATH+"/genCmdClass.pbs"
    jobGenJobLaunchClass = JOBPATH+"/genJobLaunchClass.pbs"
    jobCmdFusion = JOBPATH+"/genCmdFusion.pbs"
    jobGenJobLaunchFusion = JOBPATH+"/genJobLaunchFusion.pbs"
    jobGenJobNoData = JOBPATH+"/genJobNoData.pbs"
    jobClassifShaping = JOBPATH+"/classifShaping.pbs"
    jobGenCmdConf = JOBPATH+"/genCmdConf.pbs"
    jobGenJobLaunchConfusion = JOBPATH+"/genJobLaunchConfusion.pbs"
    jobfusionConfusion = JOBPATH+"/fusionConfusion.pbs"
    jobGenResults = JOBPATH+"/genResults.pbs"
    jobGenJobLaunchOutStat = JOBPATH+"/genJobLaunchOutStats.pbs"
    jobMergeOutStat = JOBPATH+"/mergeOutStats.pbs"

    if not os.path.exists(JOBPATH):
        print JOBPATH + " has been created"
        os.system("mkdir "+JOBPATH)

    if not os.path.exists(LOGPATH):
        print LOGPATH + " has been created"
        os.system("mkdir "+LOGPATH)
    
    if os.path.exists(jobGenCmdFeatures):
        os.remove(jobGenCmdFeatures)
    #gen_jobGenCmdFeatures(jobGenCmdFeatures,LOGPATH,Fileconfig)
    gen_job(jobGenCmdFeatures,LOGPATH,Fileconfig,"jobGenCmdFeatures")

    if os.path.exists(jobGenJobLaunchFeat):
        os.remove(jobGenJobLaunchFeat)
    #gen_jobGenJobLaunchFeat(jobGenJobLaunchFeat,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchFeat,LOGPATH,Fileconfig,"jobGenJobLaunchFeat")

    if os.path.exists(jobEnvelope):
        os.remove(jobEnvelope)
    #gen_jobEnvelope(jobEnvelope,LOGPATH,Fileconfig)
    gen_job(jobEnvelope,LOGPATH,Fileconfig,"jobEnvelope")

    if os.path.exists(jobGenerateRegionShape):
        os.remove(jobGenerateRegionShape)
    #gen_jobGenerateRegionShape(jobGenerateRegionShape,LOGPATH,Fileconfig)
    gen_job(jobGenerateRegionShape,LOGPATH,Fileconfig,"jobGenerateRegionShape")

    if os.path.exists(jobRegionByTiles):
        os.remove(jobRegionByTiles)
    #gen_jobRegionByTiles(jobRegionByTiles,LOGPATH,Fileconfig)
    gen_job(jobRegionByTiles,LOGPATH,Fileconfig,"jobRegionByTiles")

    if os.path.exists(jobExtractactData):
        os.remove(jobExtractactData)
    #gen_jobExtractactData(jobExtractactData,LOGPATH,Fileconfig)
    gen_job(jobExtractactData,LOGPATH,Fileconfig,"jobExtractactData")

    if os.path.exists(jobGenJobDataAppVal):
        os.remove(jobGenJobDataAppVal)
    #gen_jobGenJobDataAppVal(jobGenJobDataAppVal,LOGPATH,Fileconfig)
    gen_job(jobGenJobDataAppVal,LOGPATH,Fileconfig,"jobGenJobDataAppVal")

    if os.path.exists(jobGenJobVectorSampler):
        os.remove(jobGenJobVectorSampler)
    #gen_jobGenJobVectorSampler(jobGenJobVectorSampler,LOGPATH,Fileconfig)
    gen_job(jobGenJobVectorSampler,LOGPATH,Fileconfig,"jobGenJobVectorSampler")

    if os.path.exists(jobGenSamplesMerge):
        os.remove(jobGenSamplesMerge)
    #gen_jobGenSamplesMerge(jobGenSamplesMerge,LOGPATH,Fileconfig)
    gen_job(jobGenSamplesMerge,LOGPATH,Fileconfig,"jobGenSamplesMerge")

    if os.path.exists(jobCmdSplitShape):
        os.remove(jobCmdSplitShape)
    #gen_jobCmdSplitShape(jobCmdSplitShape,LOGPATH,Fileconfig)
    gen_job(jobCmdSplitShape,LOGPATH,Fileconfig,"jobCmdSplitShape")

    if os.path.exists(jobGenJobSplitShape):
        os.remove(jobGenJobSplitShape)
    #gen_jobGenJobSplitShape(jobGenJobSplitShape,LOGPATH,Fileconfig)
    gen_job(jobGenJobSplitShape,LOGPATH,Fileconfig,"jobGenJobSplitShape")

    if os.path.exists(jobRearrange):
        os.remove(jobRearrange)
    #gen_jobRearrange(jobRearrange,LOGPATH,Fileconfig)
    gen_job(jobRearrange,LOGPATH,Fileconfig,"jobRearrange")

    if os.path.exists(jobGenCmdStat):
        os.remove(jobGenCmdStat)
    #gen_jobGenCmdStat(jobGenCmdStat,LOGPATH,Fileconfig)
    gen_job(jobGenCmdStat,LOGPATH,Fileconfig,"jobGenCmdStat")

    if os.path.exists(jobGenJobLaunchStat):
        os.remove(jobGenJobLaunchStat)
    #gen_jobGenJobLaunchStat(jobGenJobLaunchStat,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchStat,LOGPATH,Fileconfig,"jobGenJobLaunchStat")

    if os.path.exists(jobGenCmdTrain):
        os.remove(jobGenCmdTrain)
    #gen_jobGenCmdTrain(jobGenCmdTrain,LOGPATH,Fileconfig)
    gen_job(jobGenCmdTrain,LOGPATH,Fileconfig,"jobGenCmdTrain")

    if os.path.exists(jobGenJobLaunchTrain):
        os.remove(jobGenJobLaunchTrain)
    #gen_jobGenJobLaunchTrain(jobGenJobLaunchTrain,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchTrain,LOGPATH,Fileconfig,"jobGenJobLaunchTrain")

    if os.path.exists(jobGenCmdClass):
        os.remove(jobGenCmdClass)
    #gen_jobGenCmdClass(jobGenCmdClass,LOGPATH,Fileconfig)
    gen_job(jobGenCmdClass,LOGPATH,Fileconfig,"jobGenCmdClass")

    if os.path.exists(jobGenJobLaunchClass):
        os.remove(jobGenJobLaunchClass)
    #gen_jobGenJobLaunchClass(jobGenJobLaunchClass,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchClass,LOGPATH,Fileconfig,"jobGenJobLaunchClass")
    
    if os.path.exists(jobCmdFusion):
        os.remove(jobCmdFusion)
    #gen_jobCmdFusion(jobCmdFusion,LOGPATH,Fileconfig)
    gen_job(jobCmdFusion,LOGPATH,Fileconfig,"jobCmdFusion")
    
    if os.path.exists(jobGenJobLaunchFusion):
        os.remove(jobGenJobLaunchFusion)
    #gen_jobGenJobLaunchFusion(jobGenJobLaunchFusion,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchFusion,LOGPATH,Fileconfig,"jobGenJobLaunchFusion")

    if os.path.exists(jobGenJobNoData):
        os.remove(jobGenJobNoData)
    #gen_jobGenJobNoData(jobGenJobNoData,LOGPATH,Fileconfig)
    gen_job(jobGenJobNoData,LOGPATH,Fileconfig,"jobGenJobNoData")

    if os.path.exists(jobClassifShaping):
        os.remove(jobClassifShaping)
    #gen_jobClassifShaping(jobClassifShaping,LOGPATH,Fileconfig)
    gen_job(jobClassifShaping,LOGPATH,Fileconfig,"jobClassifShaping")

    if os.path.exists(jobGenCmdConf):
        os.remove(jobGenCmdConf)
    #gen_jobGenCmdConf(jobGenCmdConf,LOGPATH,Fileconfig)
    gen_job(jobGenCmdConf,LOGPATH,Fileconfig,"jobGenCmdConf")

    if os.path.exists(jobGenJobLaunchConfusion):
        os.remove(jobGenJobLaunchConfusion)
    #gen_jobGenJobLaunchConfusion(jobGenJobLaunchConfusion,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchConfusion,LOGPATH,Fileconfig,"jobGenJobLaunchConfusion")

    if os.path.exists(jobfusionConfusion):
        os.remove(jobfusionConfusion)
    #gen_jobfusionConfusion(jobfusionConfusion,LOGPATH,Fileconfig)
    gen_job(jobfusionConfusion,LOGPATH,Fileconfig,"jobfusionConfusion")
    
    if os.path.exists(jobGenResults):
        os.remove(jobGenResults)
    #gen_jobGenResults(jobGenResults,LOGPATH,Fileconfig)
    gen_job(jobGenResults,LOGPATH,Fileconfig,"jobGenResults")
    
    if os.path.exists(jobGenJobLaunchOutStat):
        os.remove(jobGenJobLaunchOutStat)
    #gen_jobGenJobLaunchOutStat(jobGenJobLaunchOutStat,LOGPATH,Fileconfig)
    gen_job(jobGenJobLaunchOutStat,LOGPATH,Fileconfig,"GenJobLaunchOutStat")

    if os.path.exists(jobMergeOutStat):
        os.remove(jobMergeOutStat)
    #gen_jobMergeOutStat(jobMergeOutStat,LOGPATH,Fileconfig)
    gen_job(jobMergeOutStat,LOGPATH,Fileconfig,"jobMergeOutStat")

def launchChain(Fileconfig, reallyLaunch=True):

    """
    IN :
        Fileconfig [string] : path to the configuration file which rule the classification
    this function is the one which launch all process 
    """

    cfg = SCF.serviceConfigFile(Fileconfig)
    cfg.checkConfigParameters()
    chainType = cfg.getParam('chain', 'executionMode')
    MODE = cfg.getParam('chain', 'mode')
    classifier = cfg.getParam('argTrain', 'classifier')
    classificationMode = cfg.getParam('argClassification', 'classifMode')

    if (MODE=="multi_regions" and classificationMode=="fusion" and classifier!="rf") and (MODE=="multi_regions" and classificationMode=="fusion" and classifier!="svm"):
        raise ValueError('If you chose the multi_regions mode, you must use rf or svm classifier')

    if chainType == "parallel":
        genJobs(Fileconfig)
        pathChain = gen_oso_parallel(cfg)
        print pathChain
        os.system("chmod u+rwx "+pathChain)
        if reallyLaunch:
            print "qsub "+pathChain
            os.system("qsub "+pathChain)
    elif chainType == "sequential":
        gen_oso_sequential(cfg)
    else:
        raise Exception("Execution mode "+chainType+" does not exist.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function allows you launch the chain according to a configuration file")
    parser.add_argument("-launch.config",dest = "config",help ="path to configuration file",required=True)
    args = parser.parse_args()
    try:
        launchChain(args.config)
    except Exception as e:
        print e
            
