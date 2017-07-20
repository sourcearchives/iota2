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
from osgeo import gdal
from osgeo.gdalconst import *
import argparse,geoToPix,ogr,os,shutil
import numpy as np

def getFieldType(layer,field):
    fieldType = None
    layerDefinition = layer.GetLayerDefn()
    dico = {"String":str,"Real":float,"Integer":int}
    for i in range(layerDefinition.GetFieldCount()):
        if layerDefinition.GetFieldDefn(i).GetName()==field:
            fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
            fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
    return dico[fieldType]

def getFeatureExtent(vector,driverName="ESRI Shapefile",field = "CODE",value = "None"):

    driver = ogr.GetDriverByName(driverName)
    dataSource = driver.Open(vector, 0)
    layer = dataSource.GetLayer()

    fieldType = getFieldType(layer,field)

    extents = [currentFeat.GetGeometryRef().GetEnvelope() for currentFeat in layer if fieldType(currentFeat.GetField(field)) == fieldType(value)]
    if len(extents) > 1 : raise Exception(str(value)+" is not unique")
    elif len(extents) == 0 : raise Exception(str(value)+" not find")
    return extents[0]

def extractAndSplit(raster,vecteur,dataField,dataFieldValue,outDirectory,outputName,X,Y,WdPath,mode="polygon"):

    import geoToPix
    border = 1 #in pix
    if not os.path.exists(outDirectory) : os.mkdir(outDirectory)

    outputDir = outDirectory
    if WdPath : outputDir = WdPath
    
    ulx = 0
    uly = 0
    rasterSource = gdal.Open(raster, GA_ReadOnly)
    lry, lrx = int(rasterSource.RasterYSize), int(rasterSource.RasterXSize)

    if mode == "polygon":
        Xmin,Xmax,Ymin,Ymax = getFeatureExtent(vecteur,driverName="ESRI Shapefile",field = "CODE_DEPT",value = dataFieldValue)

        ulx,uly=geoToPix.geoToPix(raster,Xmin,Ymax)
        lrx,lry=geoToPix.geoToPix(raster,Xmax,Ymin)

        ulx=ulx-border
        uly=uly-border
        lrx=lrx+border
        lry=lry+border

    xSize = (lrx-ulx)/X
    intervalX = np.arange(ulx,lrx,xSize)
    
    ySize = (lry-uly)/Y
    intervalY = np.arange(uly,lry,ySize)
    split=1
    outputs = []
    for y in range(Y):
	for x in range(X):
            startx = intervalX[x]
            starty = intervalY[y]
            sizex = xSize
            sizey = ySize
            if x==len(intervalX)-2:sizex = lrx-intervalX[x]
            if y==len(intervalY)-2:sizey = lry-intervalY[y]
            outputTif = outputDir+"/"+outputName+"_"+str(split)+".tif"
            cmd = "otbcli_ExtractROI -startx "+str(startx)+" -starty "+str(starty)+" -sizex "+str(sizex)+\
                  " -sizey "+str(sizey)+" -in "+raster+" -out "+outputTif+" uint8"
            outputs.append(outputTif)
            split+=1
            print cmd
            os.system(cmd)
    if WdPath:
        outputs_wd = []
	for currentOut in outputs:
		print "copy "+currentOut+" in "+outDirectory
		shutil.copy(currentOut,outDirectory)
                outputs_wd.append(outDirectory+currentOut.split("/")[-1])
    return outputs

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "extract from raster polygon extent and split it in mosaic")
    parser.add_argument("-in.raster",dest = "raster",help ="path to the raster",default=None,required=True)
    parser.add_argument("-in.vector",dest = "vector",help ="path to the vectors",default=None,required=True)
    parser.add_argument("-field",dest = "dataField",help ="dataField",default=None,required=True)
    parser.add_argument("-dataFieldValue",dest = "dataFieldValue",help ="field value",default=None,required=True)
    parser.add_argument("-out.directory",dest = "outDirectory",help ="output directory",default=None,required=True)
    parser.add_argument("-out.name",dest = "outputName",help ="output name",default=None,required=True)
    parser.add_argument("-X",dest = "X",help ="number of split in X",type = int,default=5,required=False)
    parser.add_argument("-Y",dest = "Y",help ="number of split in Y",type = int,default=5,required=False)
    parser.add_argument("-workingDirectory",dest = "WdPath",help ="working directory",required=False,default=None)
    parser.add_argument("-mode",dest = "mode",choices = ["polygon","entire"],\
                        help ="split from polygon extent or entire raster",required=False,default="polygon")
    args = parser.parse_args()

    extractAndSplit(args.raster,args.vector,args.dataField,args.dataFieldValue,\
                    args.outDirectory,args.outputName,args.X,args.Y,args.WdPath,args.mode)

#Ex : python ~/tmp/extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 2 -out.name corseDuNord -out.directory /mnt/data/home/vincenta/tmp/outputROI -dataFieldValue 1 -field CODE_DEPT -in.vector /mnt/data/home/vincenta/Corse2016/vector/departementsCorse.shp -in.raster /mnt/data/home/vincenta/Corse2016/Classif_Seed_0.tif
