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

#TODO add function to compute number of selected node ->select=??
#depend from mpiprocs, procs and number of available number of socket threads

def get_common_mask(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N generateCommonMasks -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=1000mb \
               -l walltime=00:10:00 -o " + logPath + "/CommonMasks_out.log \
               -e "+ logPath +"/CommonMasks_err.log "
    return pbs_cmd


def extract_data_region_tiles(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N extractDataRegionTile -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/ExtractData_out.log \
               -e "+ logPath +"/ExtractData_err.log "
    return pbs_cmd


def split_learning_val(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N splitLearningVal -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/SplitLearnVal_out.log \
               -e "+ logPath +"/SplitLearnVal_err.log "
    return pbs_cmd


def split_learning_val_sub(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N splitLearningVal -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/SplitLearnVal_SUB_out.log \
               -e "+ logPath +"/SplitLearnVal_SUB_err.log "
    return pbs_cmd


def vectorSampler(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N vectorSampler -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/VectorSampler_out.log \
               -e "+ logPath +"/VectorSampler_err.log "
    return pbs_cmd


def mergeSample(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N mergeSample -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/mergeSample_out.log \
               -e "+ logPath +"/mergeSample_err.log "
    return pbs_cmd


def stats_by_models(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N modelsStats -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/modelsStats_out.log \
               -e "+ logPath +"/modelsStats_err.log "
    return pbs_cmd


def training(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N training -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/training_out.log \
               -e "+ logPath +"/training_err.log "
    return pbs_cmd


def cmdClassifications(procs, logPath):
    """
    usage : ressources request for PBS to compute commands for classification
            AND masks for classifications
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N classifCmd -l select=1:ncpus="+str(procs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/classifCmd_out.log \
               -e "+ logPath +"/classifCmd_err.log "
    return pbs_cmd


def classifications(procs, mpiprocs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N classifications -l select=1:ncpus="+str(procs)+":mpiprocs="+str(mpiprocs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/classifications_out.log \
               -e "+ logPath +"/classifications_err.log "
    return pbs_cmd


def classifShaping(procs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N classifShaping -l select=1:ncpus="+str(procs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/classifShaping_out.log \
               -e "+ logPath +"/classifShaping_err.log "
    return pbs_cmd


def confusionMatrix(procs, logPath):
    """
    usage : ressources request for PBS to compute get_common_mask step
    
    IN
    param : mpiprocs [str/int] number of MPI process
    param : logPath [string] path to log directory
    
    OUT
    param : pbs_cmd [string] all ressource request
    """
    pbs_cmd = "-N classifShaping -l select=1:ncpus="+str(procs)+":mem=4000mb \
               -l walltime=01:00:00 -o " + logPath + "/confusionMatrix_out.log \
               -e "+ logPath +"/confusionMatrix_err.log "
    return pbs_cmd

