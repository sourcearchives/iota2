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
import otbApplication as otb
from Common import FileUtils as fu

def extractMatrix(raster, shapeROI, fieldROI, valuesROI, groudTruth, dataField, outcsv):

    vecToRaster = otb.Registry.CreateApplication("Rasterization")
    vecToRaster.SetParameterString("im", raster)
    vecToRaster.SetParameterString("epsg", str(fu.getRasterProjectionEPSG(raster)))
    vecToRaster.SetParameterString("mode", "attribute")
    vecToRaster.SetParameterString("in", shapeROI)
    vecToRaster.SetParameterString("mode.attribute.field", fieldROI)
    vecToRaster.SetParameterString("ram", "10000")
    vecToRaster.Execute()

    ####### useless bandmath
    useless = otb.Registry.CreateApplication("BandMath")
    useless.SetParameterString("exp", "im1b1")
    useless.SetParameterStringList("il", [raster])
    useless.SetParameterString("ram", "10000")
    useless.Execute()
    #######

    maskVal = otb.Registry.CreateApplication("BandMath")
    exp = "("+"?1:".join(["im1b1=="+currentVal for currentVal in valuesROI])+"?1:0)*im2b1"
    maskVal.SetParameterString("exp", exp)
    maskVal.SetParameterString("ram", "10000")
    maskVal.AddImageToParameterInputImageList("il", vecToRaster.GetParameterOutputImage("out"))
    maskVal.AddImageToParameterInputImageList("il", useless.GetParameterOutputImage("out"))
    maskVal.Execute()

    confMatrix = otb.Registry.CreateApplication("ComputeConfusionMatrix")
    confMatrix.SetParameterInputImage("in", maskVal.GetParameterOutputImage("out"))
    confMatrix.SetParameterString("ref.vector.in", groudTruth)
    confMatrix.SetParameterString("nodatalabel", "0")
    confMatrix.SetParameterString("ref", "vector")
    confMatrix.SetParameterString("out", outcsv)
    confMatrix.SetParameterString("ram", "10000")
    confMatrix.UpdateParameters()
    confMatrix.SetParameterStringList("ref.vector.field", [dataField])

    confMatrix.ExecuteAndWriteOutput()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This script compute confusion matrix by region of interest.")
    parser.add_argument("-in.raster", dest="raster", help="path to the raster", default=None, required=True)
    parser.add_argument("-in.shapeROI", dest="shapeROI", help="path to vector containing region of interest", default=None, required=True)
    parser.add_argument("-in.shapeROI.field", dest="fieldROI", help="ROI's field", default=None, required=True)
    parser.add_argument("-in.shapeROI.field.values", dest="valuesROI", help="ROI's values", default=None, required=True, nargs='+')
    parser.add_argument("-in.ground.truth", dest="groudTruth", help="path to the ground truth shape", default=None, required=True)
    parser.add_argument("-in.ground.truth.field", dest="dataField", help="ground truth field", default=None, required=True)
    parser.add_argument("-out", dest="outcsv", help="output csv file", default=None, required=True)
    args = parser.parse_args()

    extractMatrix(args.raster, args.shapeROI, args.fieldROI, args.valuesROI, args.groudTruth, args.dataField, args.outcsv)

#python regionConfusionMatrix.py -out /mnt/data/home/vincenta/tmp/Matrix.csv -in.ground.truth.field CODE -in.ground.truth /mnt/data/home/vincenta/Shape/France_2009_refV3_val03.shp -in.raster /mnt/data/home/vincenta/ClassificationFrance_2016_S2/Classif_Seed_0.tif -in.shapeROI /mnt/data/home/vincenta/Shape/TypoClimat_sieve_1600_final_remove9andClean.shp -in.shapeROI.field DN -in.shapeROI.field.values 1



