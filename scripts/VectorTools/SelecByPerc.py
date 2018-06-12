#!/usr/bin/python

import sys
from sys import argv
import os
import osr
from osgeo import ogr
import random
import string



def shpPercentageSelection(infile, field, percentage, opath):
   classes = []
   shapefile = infile
   allFID = []
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()
   count = float(layer.GetFeatureCount())
   for feature in layer:
      pid = feature.GetFID()
      allFID.append(pid)
      cl =  feature.GetField(field)
      if cl not in classes:
         classes.append(cl)
   listallid = []
   for cl in classes:
      listid = []
      layer = dataSource.GetLayer()
      layer.SetAttributeFilter(field+" = "+str(cl))
      featureCount = float(layer.GetFeatureCount())
      polbysel = int((featureCount*float(percentage))/100)
      for feat in layer:
         _id = feat.GetFID()
         listid.append(_id)
         listid.sort()
      listToChoice = random.sample(listid, int(polbysel))
      for fid in listToChoice:
         listallid.append(fid)  
   listallid.sort()
   ch = ""
   listFid = []
   for fid in listallid:
      listFid.append("FID="+str(fid))
   listToCh = []
   for Fid in listFid:
      listToCh.append(Fid)
      listToCh.append(' OR ')
   listToCh.pop()
   per = string.replace(str(percentage),'.','p') 
   finalCh =  ''.join(listToCh)
   layer.SetAttributeFilter(finalCh)
 
   outShapefile = opath+"/"+namefile[-1]+"-"+str(per)+"perc.shp"
   CreateNewLayer(layer, outShapefile)

   return outShapefile



def CreateNewLayer(layer, outShapefile):
      inLayerDefn = layer.GetLayerDefn()
      field_name_target = []
      for i in range(inLayerDefn.GetFieldCount()):
         field =  inLayerDefn.GetFieldDefn(i).GetName()
         field_name_target.append(field)
         outDriver = ogr.GetDriverByName("ESRI Shapefile")
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      srsObj = layer.GetSpatialRef()
      outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon )
      # Add input Layer Fields to the output Layer if it is the one we want
      inLayerDefn = layer.GetLayerDefn()
      for i in range(0, inLayerDefn.GetFieldCount()):
         fieldDefn = inLayerDefn.GetFieldDefn(i)
         fieldName = fieldDefn.GetName()
         if fieldName not in field_name_target:
             continue
         outLayer.CreateField(fieldDefn)
     # Get the output Layer's Feature Definition
      outLayerDefn = outLayer.GetLayerDefn()

     # Add features to the ouput Layer
      for inFeature in layer:
      # Create output Feature
         outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
         for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in field_name_target:
                continue

            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))
        # Set geometry as centroid
         geom = inFeature.GetGeometryRef()
         outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
         outLayer.CreateFeature(outFeature)

if __name__=='__main__':
    usage= 'usage: <infile> <field> <percentage> <opath>'
    if len(sys.argv) != 5:
    	print usage
	sys.exit(1)
    else:
	shpPercentageSelection(argv[1], argv[2], argv[3], argv[4])
