#!/usr/bin/python

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

import string
import os
import shutil
import sys
import argparse
import otbApplication as otb
from osgeo import gdal
from osgeo.gdalconst import GA_Update

def superimpose(inImage, referenceImage, outImage, gridStep=100):
    """Superimpose one image on top of another one using the projection
    information"""
    rsApp = otb.Registry.CreateApplication("Superimpose")
    rsApp.SetParameterString("inr", referenceImage)
    rsApp.SetParameterString("inm", inImage)
    rsApp.SetParameterString("out", outImage)
    rsApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_int16)
    rsApp.SetParameterFloat("lms", gridStep)
    rsApp.ExecuteAndWriteOutput()

def subsampleS2(s2ImageIn, s2ImageOut, l8ImageIn):
    """Subsample the Sentinel-2 image to the Landsat-8 resolution"""
    superimpose(s2ImageIn, l8ImageIn, s2ImageOut)

def getLandsatRedBand(l8ImageIn, l8RedBandOut, channel=4):
    """Extract the red band of the Landsat-8 image"""
    extractApp = otb.Registry.CreateApplication("ExtractROI")
    extractApp.SetParameterString("in", l8ImageIn)
    extractApp.SetParameterString("out", l8RedBandOut)
    extractApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_int16)
    extractApp.UpdateParameters()
    extractApp.SetParameterStringList("cl", ["Channel"+str(channel)])
    extractApp.ExecuteAndWriteOutput()

def disparityMapEstimation(s2ImageIn, l8ImageIn, disparityMapOut, \
                           explorationRadius=2, metricRadius=5, \
                           validityLowerThreshold=0, subsamplingRate=3, \
                           metric="CCSM"):
    """Estimate de disparity map between S2 and L8."""
    dmApp = otb.Registry.CreateApplication("FineRegistration")
    dmApp.SetParameterString("ref", s2ImageIn)
    dmApp.SetParameterString("sec", l8ImageIn)
    dmApp.SetParameterString("out", disparityMapOut)
    dmApp.SetParameterInt("erx", explorationRadius)
    dmApp.SetParameterInt("ery", explorationRadius)
    dmApp.SetParameterInt("mrx", metricRadius)
    dmApp.SetParameterInt("mry", metricRadius)
    dmApp.SetParameterFloat("vmlt", validityLowerThreshold)
    dmApp.SetParameterFloat("ssrx", subsamplingRate)
    dmApp.SetParameterFloat("ssry", subsamplingRate)
    dmApp.SetParameterString("m", metric)
    dmApp.ExecuteAndWriteOutput()

def filterDisparityMap(dmIn, dmComponentOut, metricThreshold=0.90, \
                       dmComponent="x", outputInvalidValue=-100):
    """Filter a component (x or y) of the disparity map using a metric validity
    threshold. Only pixels above the threshold will be kept"""
    compStr = "im1b1"
    if dmComponent == "y":
        compStr = "im1b2"
    expression = "im1b3>"+str(metricThreshold)+"?"+compStr+":"+str(outputInvalidValue)
    bmApp = otb.Registry.CreateApplication("BandMath")
    bmApp.SetParameterStringList("il", [dmIn])
    bmApp.SetParameterString("out", dmComponentOut)
    bmApp.SetParameterString("exp", expression)
    bmApp.ExecuteAndWriteOutput()

def estimateMeanShiftAndStdFromDisparityMap(dmComponentIn, backgroundValue=-100,\
                            removeStatsFile=True, \
                            statsFileName="/tmp/stats.xml"):
    """Use image statistics (ignore backgroundValue) to estimate the mean and
    the std of the disparity map component"""
    cisApp = otb.Registry.CreateApplication("ComputeImagesStatistics")
    cisApp.SetParameterStringList("il", [dmComponentIn])
    cisApp.SetParameterString("out", statsFileName)
    cisApp.SetParameterFloat("bv", backgroundValue)
    cisApp.ExecuteAndWriteOutput()
    with open(statsFileName) as sf:
        ls = sf.readlines()
        m = float(string.split(ls[3], '"')[1])
        s = float(string.split(ls[6], '"')[1])
    if removeStatsFile:
        os.remove(statsFileName)
    return(m, s)

def estimateMeanShiftAndStd(l8ImageIn, s2ImageIn, removeTemporaryFiles=True, \
                 workingDir="/tmp", s2SubsamplingRate=3, l8RedChannel=4):
    """Estimates the mean shift in X and Y together with standard deviations"""
    lowResS2 = workingDir+"/lrs2.tif"
    redl8 = workingDir+"/redl8.tif"
    disparityMap = workingDir+"/dm.tif"
    disparityMapX = workingDir+"/dmx.tif"
    disparityMapY = workingDir+"/dmy.tif"
    filesToRemove = [lowResS2, redl8, disparityMap, disparityMapX, \
                     disparityMapY]
    subsampleS2(s2ImageIn, lowResS2, l8ImageIn)
    getLandsatRedBand(l8ImageIn, redl8, l8RedChannel)
    disparityMapEstimation(lowResS2, redl8, disparityMap)
    filterDisparityMap(disparityMap, disparityMapX, dmComponent="x")
    (dx, stdx) = estimateMeanShiftAndStdFromDisparityMap(disparityMapX)
    filterDisparityMap(disparityMap, disparityMapY, dmComponent="y")
    (dy, stdy) = estimateMeanShiftAndStdFromDisparityMap(disparityMapY)
    if removeTemporaryFiles:
        for f in filesToRemove:
            os.remove(f)
    return (dx, stdx, dy, stdy)

def shiftImage(l8ImageIn, dx, dy, backupOriginalImage=True):
    """Modify the image meta-data to apply a global shift"""
    if backupOriginalImage:
        shutil.copy2(l8ImageIn, l8ImageIn+".original")
    ds = gdal.Open(l8ImageIn, GA_Update)
    val = ds.ReadAsArray()
    proj = ds.GetProjection()
    gt = ds.GetGeoTransform()
    gt2 = (gt[0]+dx, gt[1], gt[2], gt[3]+dy, gt[4], gt[5])
    ds.SetGeoTransform(gt2)

def landsatShift(l8ImageIn, s2ImageIn, removeTemporaryFiles=True, \
                 workingDir="/tmp", s2SubsamplingRate=3, l8RedChannel=4):
    """Estimates the shift and then applies the meta-data modification"""
    (dx, stdx, dy, stdy) = estimateMeanShiftAndStd(l8ImageIn, s2ImageIn, \
                                                 removeTemporaryFiles, \
                                                 workingDir, s2SubsamplingRate, \
                                                 l8RedChannel)
    print "Estimated shift"
    print "dx (std) = ", str(dx)+"("+str(stdx)+")"
    print "dy (std) = ", str(dy)+"("+str(stdy)+")"
    #A test on std could be included here
    shiftImage(l8ImageIn, -dx, -dy)
    shutil.copy2(l8ImageIn, "tmp_"+l8ImageIn)
    superimpose("tmp_"+l8ImageIn, s2ImageIn, l8ImageIn)
    os.remove("tmp_"+l8ImageIn)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Shifts a Landsat-8 \
        image by modifying its meta-data. The shift is estimated by \
        correlation over a reference Sentinel-2 image")
        parser.add_argument("-l8", dest="l8Image", action="store", \
                            help="Landsat-8 image to shift", required=True)
        parser.add_argument("-s2", dest="s2Image", action="store", \
                            help="Reference Sentinel-2 image", required=True)
        parser.add_argument("-rtf", dest="removeTemp", action="store", \
                            help="Remove temporary files (y/n)", \
                            default="n")
        parser.add_argument("-wd", dest="workingDir", action="store", \
                            help="Working directory for temporary files", \
                            default="/tmp/")
        args = parser.parse_args()
        landsatShift(args.l8Image, args.s2Image, bool(args.removeTemp == "y"), \
                     args.workingDir)
