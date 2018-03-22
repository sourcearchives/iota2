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
import argparse,shutil,os
from config import Config
import otbApplication as otb
from osgeo import gdal,ogr,osr
import fileUtils as fu

def genGeometries(origin,size,X,Y,overlap):
	geom_grid = []
	for y in range(Y):
		raw=[]
		for x in range(X):
			if x == 0 :minX=origin[0]
			else : minX = float((origin[0]+x*size*1000)-1000*overlap*x)
			maxX= minX+size*1000
			if y == 0 : minY=origin[1]
			else : minY=float((origin[1]+y*size*1000)-1000*overlap*y)
			maxY=minY+size*1000

			ring = ogr.Geometry(ogr.wkbLinearRing)
			ring.AddPoint(minX, minY)
			ring.AddPoint(maxX, minY)
			ring.AddPoint(maxX, maxY)
			ring.AddPoint(minX, maxY)
			ring.AddPoint(minX, minY)
			
			poly = ogr.Geometry(ogr.wkbPolygon)
			poly.AddGeometry(ring)
	
			raw.append(poly)
		geom_grid.append(raw)
	return geom_grid

def generateTif(vectorFile,pixSize):

	minX,minY,maxX,maxY = fu.getShapeExtent(vectorFile)
	cmd = "gdal_rasterize -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)+" -a Tile -tr "+str(pixSize)+" "+str(pixSize)+" "+vectorFile+" "+vectorFile.replace(".shp",".tif")
	print cmd
	os.system(cmd)

def genGrid(outputDirectory,X=10,Y=10,overlap=10,size=100,raster = "True",pixSize = 100):

    origin = (500100,6211230)#lower left
    geom_grid = genGeometries(origin,size,X,Y,overlap)
    driver = ogr.GetDriverByName("ESRI Shapefile")  
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(2154)

    tile = 1
    for raw in geom_grid:
        for col in raw:
            outTile = outputDirectory+"/Tile"+str(tile)+".shp"
            if os.path.exists(outTile): driver.DeleteDataSource(outTile)
            data_source = driver.CreateDataSource(outTile)
            layerName = outTile.split("/")[-1].split(".")[0]
            layer = data_source.CreateLayer(layerName, srs, geom_type=ogr.wkbPolygon)
            field_tile = ogr.FieldDefn("Tile", ogr.OFTInteger)
            field_tile.SetWidth(5)
            layer.CreateField(field_tile)
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("Tile", tile)
            feature.SetGeometry(col)
            layer.CreateFeature(feature)
            tile+=1
            feature = None
            data_source = None

            if raster == "True":
                generateTif(outTile,pixSize)
                #if os.path.exists(outTile):
                #    driver.DeleteDataSource(outTile)
                                
				
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "generate grid")
	parser.add_argument("-outputDirectory",dest = "outputDirectory",help ="output ",default=None,required=True)
	parser.add_argument("-Xgrid",dest = "X",help ="number of tiles in X",type = int,default=10,required=True)
	parser.add_argument("-Ygrid",dest = "Y",help ="number of tiles in Y",type = int,default=10,required=True)
	parser.add_argument("-overlap",dest = "overlap",help ="overlap in km",type = float,default=10,required=True)
	parser.add_argument("-size",dest = "size",help ="tile's size",type = float,default=100,required=True)
	parser.add_argument("-generateRaster",dest = "raster",help ="",default = "True",required=False,choices = ["True","False"])
	parser.add_argument("-raster.pixSize",dest = "pixSize",help ="",type = float,default=30,required=False)

	args = parser.parse_args()

	genGrid(args.outputDirectory,args.X,args.Y,args.overlap,args.size,args.raster)

#python test_genGrid.py -outputDirectory /mnt/data/home/vincenta/IOTA2/test_data/test_envelope -size 100 -overlap 10 -Ygrid 10 -Xgrid 10



