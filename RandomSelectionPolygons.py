#!/usr/bin/python

import sys
from sys import argv
import os
import osr
from osgeo import ogr
import random
import string

def RandomInSitu(shapefile, field, nbdraws,perc_learn, opath):
   """
   This function creates 2 * nbdraws new shapefiles by selecting % of polygons of each crop class present for \n
   a learning file and the remaining % for a validation file
       ARGs:
            -shapefile: the input shapefile
            -field: the name of the field in which selection will be based 
            -nbdraws: the number of random selections wanted
            -opath: the output path
           
       OUTPUT:
            -2 * nbdraws new shapefiles
    
   """

 
   classes = []
   field = field
   dicoprop = {}
   allFID = []
   nbtirage = int(nbdraws)
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   count = float(layer.GetFeatureCount())
   print "The original file has "+str(count)+" features"
   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)

   for tirage in range(0,nbtirage):
      listallid = []
      for cl in classes:
         listid = []
         layer = dataSource.GetLayer()
	 #ATTENTION
         #layer.SetAttributeFilter(field+" = \'"+str(cl)+"\'")
         layer.SetAttributeFilter(field+" = "+str(cl))
         featureCount = float(layer.GetFeatureCount())
         polbysel = round(featureCount / (100/float(perc_learn)))
         if polbysel <= 1:
	    polbysel = 1
         #print polbysel
         prop = float((featureCount/count)*100)
         dicoprop[cl] = prop
         for feat in layer:
            _id = feat.GetFID()
            listid.append(_id)
            listid.sort()
         listToChoice = random.sample(listid, int(polbysel))
         #print listToChoice
         for fid in listToChoice:
            listallid.append(fid)  
       
      listallid.sort()
      #print listallid
      ch = ""
      listFid = []
      for fid in listallid:
         listFid.append("FID="+str(fid))

      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()

      chA =  ''.join(resultA)
      layer.SetAttributeFilter(chA)
      outShapefile = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_learn.shp"
      CreateNewLayer(layer, outShapefile)

      listValid = []
      for i in allFID:
         if i not in listallid:
            listValid.append(i)

      chV = ""
      listFidV = []
      for fid in listValid:
         listFidV.append("FID="+str(fid))

      resultV = []

      for e in listFidV:
          resultV.append(e)
          resultV.append(' OR ')
      resultV.pop()

      chV =  ''.join(resultV)
      layer.SetAttributeFilter(chV)
      outShapefile2 = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_val.shp"
      CreateNewLayer(layer, outShapefile2)

def getFields(layer):
   """
   Returns the list of fields of a shapefile
   """
   inLayerDefn = layer.GetLayerDefn()
   field_name_list = []
   for i in range(inLayerDefn.GetFieldCount()):
      field =  inLayerDefn.GetFieldDefn(i).GetName()
      field_name_list.append(field)
   return field_name_list

# 
def CreateNewLayer(layer, outShapefile):
      """
      This function creates a new shapefile
          ARGs:
            -layer: the input shapefile
            -outShapefile: the name of the output shapefile
    
      """

      #Warning: used to S2AGRI data model, next line to change, modify name of attributs
      field_name_target = getFields(layer)
      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      #if file already exists, delete it
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      #Get the spatial reference of the input layer
      srsObj = layer.GetSpatialRef()
      #Creates the spatial reference of the output layer
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
    usage= 'usage: <infile> <field> <nb_draws> <percentage> <opath>'
    if len(sys.argv) != 6:
    	print usage
	sys.exit(1)
    else:
	RandomInSitu(argv[1], argv[2], argv[3], argv[4], argv[5])

