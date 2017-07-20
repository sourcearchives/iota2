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
import argparse,extractAndSplit,os,shutil
import fileUtils as fu

def generateJobs(jobFile,splitsName,nbSplits,expressionFile,bandMathExe,splitsDirectory,shareDirectory):
    
    with open(jobFile,"w") as job :
        job.write("\
#!/bin/bash\n\
#PBS -N subBandMath\n\
#PBS -l select=1:ncpus=20:mem=100000mb\n\
#PBS -l walltime=100:00:00\n\
#PBS -J 1-%s:1\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=20\n\
exe=%s\n\
splitDirectory=%s\n\
splitsName=%s\n\
expressionFile=%s\n\
shareDirectory=%s\n\
cp \"$shareDirectory/\"$splitsName\"_${PBS_ARRAY_INDEX}.tif\" $TMPDIR\n\
$exe \"$TMPDIR\"/\"$splitsName\"_${PBS_ARRAY_INDEX}.tif $expressionFile $TMPDIR/\"$splitsName\"_\"${PBS_ARRAY_INDEX}\"_filtered.tif\n\
cp $TMPDIR/\"$splitsName\"_\"${PBS_ARRAY_INDEX}\"_filtered.tif $shareDirectory\n\
        "%(nbSplits,bandMathExe,splitsDirectory,splitsName,expressionFile,shareDirectory))

def bandMathSplit(rasterIn,rasterOut,expressionFile,workingDirectory,mode="hpc",X=5,Y=5,bandMathExe=None,shareDirectory=None):

    print "bandMathSplit application"
    subRasterName = "bandMathSplit"
    spx,spy = fu.getRasterResolution(rasterIn)
    outDirectory,OutName = os.path.split(rasterOut)

    splits = extractAndSplit.extractAndSplit(rasterIn,None,None,None,workingDirectory,subRasterName,X,Y,None,"entire")
    
    if mode == "hpc" and not shareDirectory : raise Exception("in hpc mode, you need a sharing directory")
    for split in splits:
        shutil.copy(split,shareDirectory)

    if mode == "hpc":
        job = workingDirectory+"/"+subRasterName+".pbs"
        generateJobs(job,subRasterName,len(splits),expressionFile,bandMathExe,workingDirectory,shareDirectory)
        print "qsub -W block=true "+job
        os.system("qsub -W block=true "+job)

    else:
        allCmd = []
        for split in splits:
            outputName = split.split("/")[-1].split(".")[0]+"_filtered"
            splitAfterBandMath = workingDirectory+"/"+outputName+".tif"
            allCmd.append(bandMathExe+" "+split+" "+expressionFile+" "+splitAfterBandMath)
            os.system(bandMathExe+" "+split+" "+expressionFile+" "+splitAfterBandMath)
        return allCmd

    bandMathOutput = fu.fileSearchRegEx(shareDirectory+"/*filtered.tif")
    fu.assembleTile_Merge(bandMathOutput,spx,workingDirectory+"/"+OutName,"Byte")
    for currentTif in bandMathOutput:
        os.remove(currentTif)

    #check if raster is not alterate
    if fu.getRasterExtent(rasterIn)!=fu.getRasterExtent(workingDirectory+"/"+OutName):
        raise Exception("Error during splitting bandMath")
    shutil.copy(workingDirectory+"/"+OutName,rasterOut)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "split raster into sub-raster and apply to each bandMathExpression")
    parser.add_argument("-in",dest = "rasterIn",help ="path to the raster to split",default=None,required=True)
    parser.add_argument("-out",dest = "rasterOut",help ="output raster",default=None,required=True)
    parser.add_argument("-expression.file",dest = "expressionFile",help ="path to the file containing bandMath expression"\
                        ,default=None,required=True)
    parser.add_argument("-wd",dest = "workingDirectory",help ="working directory",default=None,required=True)
    parser.add_argument("-mode",dest = "mode",help ="mode selection",choices = ["hpc","cmd"],default="hpc",required=True)
    parser.add_argument("-X",dest = "X",help ="split number in X",default="5",required=False,type=int)
    parser.add_argument("-Y",dest = "Y",help ="split number in Y",default="5",required=False,type=int)
    parser.add_argument("-bandMathExe",dest = "bandMathExe",help ="path to the bandMath exe",required=True)
    parser.add_argument("-share.Directory",dest = "shareDirectory",help ="path to a sharing directory (hpc mode)",default = None,required=False)
    args = parser.parse_args()
    bandMathSplit(args.rasterIn,args.rasterOut,args.expressionFile,args.workingDirectory,\
                  args.mode,args.X,args.Y,args.bandMathExe,args.shareDirectory)
    #python /home/uz/vincenta/tmp/bandMathSplit.py -share.Directory $shareDirectory -bandMathExe /work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/Exe/iota2BandMathFile -in /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/classif/Classif_T32TLT_model_2_seed_0.tif -out /work/OT/theia/oso/TMP/rasterMerged.tif -expression.file /home/uz/vincenta/tmp/bandMathExpression.txt -wd $TMPDIR -mode hpc

