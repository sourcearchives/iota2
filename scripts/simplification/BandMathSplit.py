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

"""
Apply a bandmath expression on sub-rasters produced by ExtractAndSplit.py script

"""

import argparse, os, shutil, glob
import ExtractAndSplit as eas

try:
    import otbAppli
    import fileUtils as fu
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

def generateJobs(jobFile, splitsName, nbSplits, expressionFile, bandMathExe, splitsDirectory, shareDirectory, threads, pixType):

    #print threads, jobFile
    if bandMathExe == 'otbcli_BandMath':
        exp = open(expressionFile, 'r').read()
        strexe = 'otbcli_BandMath -il %s -out %s %s -exp "%s"'%('\"$TMPDIR\"/\"$splitsName\"_${PBS_ARRAY_INDEX}.tif', \
                                                                '$TMPDIR/\"$splitsName\"_\"${PBS_ARRAY_INDEX}\"_filtered.tif', \
                                                                pixType, \
                                                                exp)
    else:
        strexe = '$exe \"$TMPDIR\"/\"$splitsName\"_${PBS_ARRAY_INDEX}.tif $expressionFile $TMPDIR/\"$splitsName\"_\"${PBS_ARRAY_INDEX}\"_filtered.tif 2'
        
    with open(jobFile,"w") as job :
        job.write("\
#!/bin/bash\n\
#PBS -N subBandMath\n\
#PBS -l select=1:ncpus=%s:mem=2gb\n\
#PBS -l walltime=15:00:00\n\
#PBS -J 1-%s:1\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
exe=%s\n\
splitDirectory=%s\n\
splitsName=%s\n\
expressionFile=%s\n\
shareDirectory=%s\n\
cp \"$shareDirectory/\"$splitsName\"_${PBS_ARRAY_INDEX}.tif\" $TMPDIR\n\
%s\n\
cp $TMPDIR/\"$splitsName\"_\"${PBS_ARRAY_INDEX}\"_filtered.tif $shareDirectory\n\
"%(threads, nbSplits, threads, bandMathExe, splitsDirectory, splitsName, expressionFile, shareDirectory, strexe))

def generateIndivJobs(jobFile, splitnumber, splitsName, expressionFile, bandMathExe, splitsDirectory, shareDirectory, threads, pixType):

    if bandMathExe == 'otbcli_BandMath':
        exp = open(expressionFile, 'r').read()
        strexe = 'otbcli_BandMath -il %s -out %s %s -exp "%s"'%('\"$TMPDIR\"/\"$splitsName\"_$splitnumber.tif', \
                                                                '$TMPDIR/\"$splitsName\"_\"$splitnumber\"_filtered.tif', \
                                                                pixType, \
                                                                exp)
    else:
        strexe = '$exe \"$TMPDIR\"/\"$splitsName\"_$splitnumber.tif $expressionFile $TMPDIR/\"$splitsName\"_\"$splitnumber\"_filtered.tif'
        
    with open(jobFile,"w") as job :
        job.write("\
#!/bin/bash\n\
#PBS -N subBandMath%s\n\
#PBS -l select=1:ncpus=%s:mem=2gb\n\
#PBS -l walltime=25:00:00\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
splitnumber=%s\n\
exe=%s\n\
splitDirectory=%s\n\
splitsName=%s\n\
expressionFile=%s\n\
shareDirectory=%s\n\
cp \"$shareDirectory/\"$splitsName\"_$splitnumber.tif\" $TMPDIR\n\
%s\n\
cp $TMPDIR/\"$splitsName\"_\"$splitnumber\"_filtered.tif $shareDirectory\n\
"%(splitnumber, threads, threads, splitnumber, bandMathExe, splitsDirectory, splitsName, expressionFile, shareDirectory, strexe))        

def bandMathSplit(rasterIn, \
                  rasterOut,\
                  expressionFile, \
                  workingDirectory,
                  pixType = 'uint8', \
                  mode = "hpc", \
                  X = 5, Y = 5, \
                  bandMathExe = None, \
                  shareDirectory = None, \
                  threads = '1', \
                  restart = False):

    subRasterName = "bandMathSplit"
    spx,spy = fu.getRasterResolution(rasterIn)
    outDirectory, OutName = os.path.split(rasterOut)

    if mode == "hpc" and not shareDirectory : raise Exception("in hpc mode, you need a sharing directory")    
    
    if not restart:
        splits = eas.extractAndSplit(rasterIn,\
                                     None,None,None,\
                                     shareDirectory,\
                                     subRasterName,\
                                     X,Y,\
                                     None,"entire",'gdal','UInt32', threads) #threads remplace par 5 (statique)
            
        #for split in splits:
        #    shutil.copy(split, shareDirectory)
    else:
        splits = glob.glob(os.path.join(shareDirectory, subRasterName + '*_filtered.tif'))
    
    if mode == "hpc":
        if not restart:
            job = workingDirectory+"/"+subRasterName+".pbs"
            #generateJobs(job, subRasterName, len(splits), expressionFile, bandMathExe, workingDirectory, shareDirectory, threads, pixType)
            generateJobs(job, subRasterName, len(splits), expressionFile, bandMathExe, workingDirectory, shareDirectory, 2, pixType)            
            os.system("qsub -W block=true " + job)
        else:
            nocomputTiles = range(1, X * Y, 1)
            for split in splits:
                nocomputTiles.remove(int(split.split('_')[1]))

            jobfiles = []
            for nbTile in nocomputTiles:
                job = workingDirectory + "/" + subRasterName + "_%s.pbs"%(nbTile)
                jobfiles.append(job)
                generateIndivJobs(job, nbTile, subRasterName, expressionFile, bandMathExe, workingDirectory, shareDirectory, threads, pixType)

            i = 0
            for jobTile in jobfiles:
                if i < (len(jobfiles)) - 1:
                    print "qsub "+ jobTile
                    os.system("qsub "+ jobTile)
                    i += 1
                else:
                    print "qsub -W block=true " + jobTile
                    os.system("qsub -W block=true " + jobTile)
                    i += 1
                
    else:
        # TODO Multithread execution (from multiprocessing import Pool) 
        if bandMathExe == 'otbcli_BandMath':
            for split in splits:
                outputName = split.split("/")[-1].split(".")[0]+"_filtered"
                splitAfterBandMath = os.path.join(workingDirectory, outputName + ".tif")
                exp = open(expressionFile, 'r').read()
                bandMathAppli = otbAppli.CreateBandMathApplication({"il": split,
                                                                    "exp": exp,
                                                                    "pixType": pixType,
                                                                    "out": splitAfterBandMath})
                bandMathAppli.ExecuteAndWriteOutput()
        else:
            allCmd = []
            for split in splits:
                outputName = split.split("/")[-1].split(".")[0]+"_filtered"
                splitAfterBandMath = os.path.join(workingDirectory, outputName + ".tif")
                allCmd.append(bandMathExe + " " + split + " " + expressionFile + " " + splitAfterBandMath)
                os.system(bandMathExe + " " + split + " " + expressionFile + " " + splitAfterBandMath)
            return allCmd


    bandMathOutput = fu.fileSearchRegEx(shareDirectory + "/*filtered.tif")

    fu.assembleTile_Merge(bandMathOutput, spx, os.path.join(workingDirectory, OutName), "UInt32")
    #print os.system("gdalinfo %s"%(os.path.join(workingDirectory, OutName)))
    
    # check if raster is not alterate
    rasterInExtent = [int(val) for val in fu.getRasterExtent(rasterIn)]
    #print os.path.dirname(os.path.realpath(rasterIn)), rasterIn
    #print workingDirectory, OutName
    #/tmp/pbs.3368518.admin01/1 /tmp/pbs.3368518.admin01/1/raster_extract.tif
    #/tmp/pbs.3368518.admin01 ClumpIdBinTemp.tif
    #print os.system("gdalinfo %s"%(rasterIn))
    rasterOutExtent =  [int(val) for val in fu.getRasterExtent(os.path.join(workingDirectory, OutName))]
    if rasterInExtent != rasterOutExtent:
        raise Exception("Error during splitting bandMath")
    
    shutil.copy(os.path.join(workingDirectory, OutName), rasterOut)


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
    parser.add_argument("-threads",dest = "threads",help ="number of threads",required=False,default="2")
    parser.add_argument("-share.Directory",dest = "shareDirectory",help ="path to a sharing directory (hpc mode)",default = None,required=False)
    parser.add_argument("-restart", action='store_true', help ="restart mode (if cluster time kill)", default = False)
    
    args = parser.parse_args()
    bandMathSplit(args.rasterIn,args.rasterOut,args.expressionFile,args.workingDirectory,\
                  args.mode,args.X,args.Y,args.bandMathExe,args.shareDirectory,args.threads, args.restart)

