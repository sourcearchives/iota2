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

Lbands = 7
Sbands = 4
interp = 0
maskC = "MaskCommunSL.tif"
maskCshp = "MaskCommunSL.shp"
#maskCshp = "MaskL30m.shp"
maskL = "MaskL30m.tif"
maskLshp = "MaskL30m.shp"
pathAppGap = "/mnt/data/home/ingladaj/Dev/builds/TemporalGapfilling/applications/"
#pathAppGap = "/mnt/data/home/otbtest/Dev/builds/temporalgapfilling/applications/"
CropCol = "CROP"
ClassCol = "CODE"
expr = CropCol+"=1" #Used in the fonction GetCropSamples
random = [6832, 2001, 932, 6392, 3453, 1512, 3054, 3442, 876, 7632]
bound = [0, 1]
delta = 5
res = 10
#res = 20
pixelotb = 'int16'
pixelgdal = 'Float32'
#pixelotb = 'int16'
#pixelgdal = 'Int16'
indices = ['NDVI', 'Brightness']#, 'NDWI'
def bandSpot():
    bandS={}
    bandS["green"]=1
    bandS["red"]=2
    bandS["NIR"]=3
    bandS["SWIR"]=4
    return bandS


def bandLandsat():
    bandL={}
    bandL["aero"]=1
    bandL["blue"]=2
    bandL["green"]=3
    bandL["red"]=4
    bandL["NIR"]=5
    bandL["SWIR1"]=6
    bandL["SWIR2"]=7
    return bandL

