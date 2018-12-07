#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   vector tools
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

import os
import glob
import sys
from sys import argv
from osgeo import ogr, gdal, osr
import random
import numpy
from osgeo.gdalconst import  GDT_Int16, GDT_Float64, GDT_Float32
import osgeo.ogr
import argparse
from shutil import copyfile


#---------------------------------------------------------------------
def openToRead(shapefile, driver="ESRI Shapefile"):
   """ 
   Opens a shapefile to read it and returns the datasource in read mode
   """
   driver = ogr.GetDriverByName(driver)
   if driver.Open(shapefile, 0):
	dataSource = driver.Open(shapefile, 0)
   else:
	print "Not possible to open the file "+shapefile
	sys.exit(1)
   return dataSource

#--------------------------------------------------------------------
def mergeFeatures(shapefile, field="", value=""):

   ds = openToWrite(shapefile)
   layer = ds.GetLayer()
   newGeometry = None
   for feature in layer:
      geometry = feature.GetGeometryRef()
      if newGeometry is None:
         newGeometry = geometry.Clone()
      else:
         newGeometry = newGeometry.Union(geometry)
        
   return newGeometry


#--------------------------------------------------------------------
def openToWrite(shapefile, driver="ESRI Shapefile"):
   """ 
   Opens a shapefile to read it and returns the datasource in write mode
   """
   driver = ogr.GetDriverByName(driver)
   if driver.Open(shapefile, 1):
	dataSource = driver.Open(shapefile, 1)
   else:
	print "Not possible to open the file "+shapefile
	sys.exit(1)
   return dataSource

#--------------------------------------------------------------------
def getNbFeat(shapefile, driver="ESRI Shapefile"):
   """
   Return the number of features of a shapefile
   """
   ds = openToRead(shapefile, driver)
   layer = ds.GetLayer()
   featureCount = layer.GetFeatureCount()
   return int(featureCount)

#--------------------------------------------------------------------
def getGeomType(shapefile, driver="ESRI Shapefile"):
   """
   Return the type of geometry of the file (WKBGeometryType)
   """
   ds = openToRead(shapefile, driver)
   layer = ds.GetLayer()
   return layer.GetGeomType()

#--------------------------------------------------------------------
def getGeomTypeFromFeat(shapefile, driver="ESRI Shapefile"):
   """
   Return the type of geometry of the file
   """

   # get the data layer
   ds = openToRead(shapefile, driver)
   layer = ds.GetLayer()

   # get the first feature
   feature = layer.GetNextFeature()

   geometry = feature.GetGeometryRef()

   return geometry.GetGeometryName()

#--------------------------------------------------------------------
def spatialFilter(vect, clipzone, clipfield, clipvalue, outvect, driverclip = "ESRI Shapefile", drivervect = "ESRI Shapefile", driverout = "ESRI Shapefile"):
   """
   Return features of a vector file  which are intersected by a feature of another vector file
   """

   dsclip = openToRead(clipzone, driverclip)
   dsvect = openToRead(vect, drivervect)
   lyrclip = dsclip.GetLayer()
   lyrvect = dsvect.GetLayer()
   
   fields = getFields(clipzone, driverclip)	
   layerDfnClip = lyrclip.GetLayerDefn()
   fieldTypeCode = layerDfnClip.GetFieldDefn(fields.index(clipfield)).GetType()

   if fieldTypeCode == 4:
      lyrclip.SetAttributeFilter(clipfield+" = \'"+str(clipvalue)+"\'")
   else:
      lyrclip.SetAttributeFilter(clipfield+" = "+str(clipvalue))

   featclip = lyrclip.GetNextFeature()
   geomclip = featclip.GetGeometryRef()
   lyrvect.SetSpatialFilter(geomclip)

   if lyrvect.GetFeatureCount() != 0:   
      drv = ogr.GetDriverByName(driverout)
      outds = drv.CreateDataSource(outvect)
      layerNameOut = os.path.splitext(os.path.basename(outvect))[0]
      outlyr = outds.CopyLayer(lyrvect, layerNameOut)
      del outlyr, outds, lyrclip, lyrvect, dsvect, dsclip
   else:
      print "No intersection between the two vector files"
      del lyrclip, lyrvect, dsvect, dsclip

#--------------------------------------------------------------------
def getLayerName(shapefile, driver = "ESRI Shapefile", layernb = 0):
   """
   Return the name of the nth layer of a vector file
   """
   ds = openToRead(shapefile, driver)
   layer = ds.GetLayer(layernb)
   return layer.GetName()

#--------------------------------------------------------------------
def random_shp_points(shapefile, nbpoints, opath, driver = "ESRI Shapefile"):
   """
   Takes an initial shapefile of points and randomly select an input nb of wanted points .
   Returns the name of the ouput file 
   """
   layer = openToWrite(shapefile)
   FID = []
   for f in layer:
      FID.append(f.GetFID())
   pointsToSelect = random.sample(FID, nbpoints)
   expr = ""
   for p in range(0,len(pointsToSelect)-1):
      expr = "FID = "+str(pointsToSelect[p])+" OR "+expr
   expr = expr+" FID = "+str(pointsToSelect[-1])
   layer.SetAttributeFilter(expr)
   outname = opath+"/"+str(nbpoints)+"points.shp"
   CreateNewLayerPoint(layer, outname)
   return outname

#--------------------------------------------------------------------
def intersect(f1,fid1,f2,fid2):
   """
   This function checks two features in a file to see if they intersect.
   It takes 4 arguments, f1 for the first file, fid1 for the index of the
   first file's feature, f2 for the second file, fid2 for the index of the
   second file's feature. Returns whether the intersection is True or False.
   """
   test = False
   ds1 =  openToRead(f1)
   layer1 = ds1.GetLayer()
   feat1 = layer1.GetFeature(fid1)
   geom1 = feat1.GetGeometryRef()
   ds2 = openToRead(f2)
   layer2 = ds2.GetLayer()
   feat2 = layer2.GetFeature(fid2)
   geom2 = feat2.GetGeometryRef()
   if geom1.Intersect(geom2) == 1:
      print "INTERSECTION IS TRUE"
      test = True
   else:
      print "INTERSECTION IS FALSE"
      test = False
   return test

#--------------------------------------------------------------------
def getFields(shp, driver="ESRI Shapefile"):
   """
   Returns the list of fields of a vector file
   """
   if not isinstance(shp, osgeo.ogr.Layer):
      ds = openToRead(shp, driver)
      lyr = ds.GetLayer()
   else:
      lyr = shp  
   
   inLayerDefn = lyr.GetLayerDefn()
   field_name_list = []
   for i in range(inLayerDefn.GetFieldCount()):
      field =  inLayerDefn.GetFieldDefn(i).GetName()
      field_name_list.append(field)
   return field_name_list

#--------------------------------------------------------------------

def getFieldType(shp, field):

   ds = openToRead(shp)
   layer = ds.GetLayer()
   layerDefinition = layer.GetLayerDefn()
   dico = {"String":str, "Real":float, "Integer":int, "Integer64":int}
   for i in range(layerDefinition.GetFieldCount()):
      if layerDefinition.GetFieldDefn(i).GetName()==field:
         fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
         fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)

   return dico[fieldType]

#--------------------------------------------------------------------

def getFirstLayer(shp):

   ds = openToRead(shp)
   lyr = ds.GetLayer()
   layer = ds.GetLayerByIndex(0)
   layerName = layer.GetName()

   return layerName
   
#--------------------------------------------------------------------

def ListValueFields(shp, field):
   """
   Returns the list of fields of a shapefile
   """
   if not isinstance(shp, osgeo.ogr.Layer):
      ds = openToRead(shp)
      lyr = ds.GetLayer()
   else:
      lyr = shp
      
   values = []
   for feat in lyr:
   	if not feat.GetField(field) in values:
		values.append(feat.GetField(field))
   return values

#--------------------------------------------------------------------

def copyShapefile(shape, outshape):

    folderout = os.path.dirname(os.path.realpath(outshape))
    basefileout = os.path.splitext(os.path.basename(outshape))[0]
    folder = os.path.dirname(os.path.realpath(shape))
    basefile = os.path.splitext(os.path.basename(shape))[0]
    for root, dirs, files in os.walk(folder):
        for name in files:
            if os.path.splitext(name)[0] == basefile:
                copyfile(folder + '/' + name, folderout + '/' + basefileout +  os.path.splitext(name)[1].lower())

#--------------------------------------------------------------------

def copyShp(shp, keyname):
   """
   Creates an empty new layer based on the properties and attributs of an input file
   """
   outShapefile = shp.split('.')[0]+'-'+keyname+'.shp'
   print outShapefile
   ds = openToRead(shp)
   layer = ds.GetLayer()
   inLayerDefn = layer.GetLayerDefn()
   field_name_target = getFields(shp)
   outDriver = ogr.GetDriverByName("ESRI Shapefile")
   #if file already exists, delete it
   if os.path.exists(outShapefile):
      outDriver.DeleteDataSource(outShapefile)
   outDataSource = outDriver.CreateDataSource(outShapefile)
   out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
   #Get the spatial reference of the input layer
   srsObj = layer.GetSpatialRef()
   #Creates the spatial reference of the output layer
   outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=getGeomType(shp) )
   # Add input Layer Fields to the output Layer if it is the one we want
   for i in range(0, inLayerDefn.GetFieldCount()):
      fieldDefn = inLayerDefn.GetFieldDefn(i)
      fieldName = fieldDefn.GetName()
      if fieldName not in field_name_target:
         continue
      outLayer.CreateField(fieldDefn)
   # Get the output Layer's Feature Definition
   outLayerDefn = outLayer.GetLayerDefn()
   #print layer.GetFeatureCount()
   print "New file created : %s" %(outShapefile)
   return outShapefile
#--------------------------------------------------------------------
def CreateNewLayer(layer, outShapefile):
      """
      This function creates a new shapefile with a layer as input
          ARGs:
            -layer: the input layer
            -outShapefile: the name of the output shapefile
    
      """
      inLayerDefn = layer.GetLayerDefn()
      field_name_target = []
      for i in range(inLayerDefn.GetFieldCount()):
          field =  inLayerDefn.GetFieldDefn(i).GetName()
          field_name_target.append(field)

      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      #if file already exists, delete it
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      #Get the spatial reference of the input layer
      srsObj = layer.GetSpatialRef()
      #Creates the spatial reference of the output layer
      outLayer = outDataSource.CreateLayer(out_lyr_name, srsObj, geom_type=layer.GetGeomType() )
      # Add input Layer Fields to the output Layer if it is the one we want

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
      return outShapefile


#--------------------------------------------------------------------
def copyFeatInShp(inFeat, shp):
   """
   Copy a feature into a new file verifyng thad does not exist in the new file
   """
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   outLayer_defn = layer.GetLayerDefn()
   inGeom = inFeat.GetGeometryRef()
   layer.SetSpatialFilter(inGeom)
   
   if layer.GetFeatureCount() == 0:
   	layer.SetSpatialFilter(None)
   	field_name_list = getFields(shp)
   	outFeat = ogr.Feature(outLayer_defn)
    	for field in field_name_list:
		inValue = inFeat.GetField(field)
		outFeat.SetField(field, inValue)
   	geom = inFeat.GetGeometryRef()
   	outFeat.SetGeometry(geom)
   	layer.CreateFeature(outFeat)
   	layer.SetFeature(outFeat)
	print "Feature copied"
   	ds.ExecuteSQL('REPACK '+layer.GetName())
   elif layer.GetFeatureCount() >=1:
	layer2 = ds.GetLayer()
   	layer2.SetSpatialFilter(inGeom)	
   	v = 0
  	for k in layer2:
		geom2 = k.GetGeometryRef() 
		if geom2:
			if inGeom.Equal(geom2) is True:
				v += 1
			elif inGeom.Equal(geom2) is False:
				v += 0
   		if v == 0:
   			field_name_list = getFields(shp)
   			outFeat = ogr.Feature(outLayer_defn)
   			for field in field_name_list:
				inValue = inFeat.GetField(field)
				outFeat.SetField(field, inValue)
			geom = inFeat.GetGeometryRef()
			outFeat.SetGeometry(geom)
			layer.CreateFeature(outFeat)
			layer.SetFeature(outFeat)
			print "Feature copied"
			ds.ExecuteSQL('REPACK '+layer.GetName())

def copyFeatInShp2(inFeat, shp):
   """
   Copy a feature into a new file verifyng thad does not exist in the new file
   """
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   outLayer_defn = layer.GetLayerDefn()
   inGeom = inFeat.GetGeometryRef()
   layer.SetSpatialFilter(inGeom)
   field_name_list = getFields(shp)
   outFeat = ogr.Feature(outLayer_defn)
   for field in field_name_list:
	inValue = inFeat.GetField(field)
	outFeat.SetField(field, inValue)
   geom = inFeat.GetGeometryRef()
   outFeat.SetGeometry(geom)
   layer.CreateFeature(outFeat)
   layer.SetFeature(outFeat)
   #print "Feature copied"
   ds.ExecuteSQL('REPACK '+layer.GetName())


#--------------------------------------------------------------------
def deleteInvalidGeom(shp):
   """
   Delete the invalide geometries in a file.
   """
   print "Verifying geometries validity"
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)
   count = 0
   corr = 0
   fidl = []
   #for i in range(0,nbfeat):
   for feat in layer:
	#feat = layer.GetFeature(i)
	fid =  feat.GetFID()
	if feat.GetGeometryRef() is None:
		#print fid
		geom = feat.GetGeometryRef()
		if geom is None:
			fidl.append(fid)
		else:
			valid = geom.IsValid()
			ring =  geom.IsRing()
			simple =  geom.IsSimple()
			if valid == False:
				fidl.append(fid)
   listFid = []
   if len(fidl) != 0:
   	for f in fidl:
		listFid.append("FID!="+str(f))
	chain = []
      	for f in listFid:
          chain.append(f)
          chain.append(' AND ')
        chain.pop()
        fchain =  ''.join(chain)
   	layer.SetAttributeFilter(fchain)
   	CreateNewLayer(layer, "valide_entities.shp")
	print "New file: valide_entities.shp was created"
   else:
	print "All geometries are valid. No file created"
         
   return 0

#--------------------------------------------------------------------
def checkValidGeom(shp):
  	"""
  	Check the validity of geometries in a file. If geometry is not valid then buffer 0 to correct
  	Works for files with polygons
   	"""
	print "Verifying geometries validity"
	ds = openToWrite(shp)
	layer = ds.GetLayer()
	nbfeat = getNbFeat(shp)
	count = 0
	corr = 0
	fidl = []
	#print layer.GetFeature(24667)

	for feat in layer:
		#feat = layer.GetFeature(i)
		fid =  feat.GetFID()
		if feat.GetGeometryRef() is None:
			print fid
			layer.DeleteFeature(fid)
			ds.ExecuteSQL('REPACK '+layer.GetName())
			layer.ResetReading()
		else:
			geom = feat.GetGeometryRef()
			valid = geom.IsValid()
			ring =  geom.IsRing()
			simple =  geom.IsSimple()
			if valid == False:
				fidl.append(fid)
				buffer_test =  feat.SetGeometry(geom.Buffer(0))
				layer.SetFeature(feat)
				if buffer_test == 0:
					print "Feature %d has been corrected" % feat.GetFID()
					corr += 1
				else:
					print "Feature %d could not be corrected" % feat.GetFID()
				count += 1
		
	print "From %d invalid features, %d were corrected" %(count, corr)
	ds.ExecuteSQL('REPACK '+layer.GetName())
	return shp

#--------------------------------------------------------------------
def checkEmptyGeom(shp):
   """
   Check if a geometry is empty and create a new file with no empty geometries, if empty geometries is null, do nothing
   """
   print "Verifying empty geometries"
   ds = openToRead(shp)
   layer = ds.GetLayer()
   allFID = []
   count = 0
   for feat in layer:
	fid = feat.GetFID()
	geom = feat.GetGeometryRef()
        if geom is not None:
	   empty = geom.IsEmpty()
	   if empty is False:
	      allFID.append(fid)
	   elif empty is True:
	      count += 1
   if count == 0:
	print "No empty geometries"
	outShapefile = shp
   else:
	for fid in allFID:
        	allFID.append("FID="+str(fid))
	#Add the word OR
      	allList = []
      	for item in allFID:
        	allList.append(item)
        	allList.append(' OR ')
      	allList.pop()

        ch = ' '.join(allList)
	layer.SetAttributeFilter(ch)
	outShapefile = shp.split('.')[0]+"-NoEmpty.shp"
        CreateNewLayer(layer, outShapefile)
	print ("%d empty geometries were deleted") %(len(allFID))

   return outShapefile

#--------------------------------------------------------------------
def checkIsRingGeom(shp):
   """
   Check if all the geometries in the shapefile are closed rings
   """
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)

#--------------------------------------------------------------------
def explain_validity(shp):
   
   from shapely.wkt import loads
   from shapely.geos import lgeos
   """
   Explains the validity reason of each feature in a shapefile
   """
   ds = openToRead(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)
   for feat in layer:
	geom = feat.GetGeometryRef()
	ob = loads(geom.ExportToWkt())
	print lgeos.GEOSisValidReason(ob._geom)
	a = raw_input()
   return 0

#--------------------------------------------------------------------
def checkIntersect(shp, distance, fieldin):
   """
   Check if each feature intersects another feature in the same file. If True compute the difference. The common part is deleted
   """
   print "Verifying intersection"
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)
   outShp = copyShp(shp, 'nointersct')
   layerDef = layer.GetLayerDefn()
   fields = getFields(shp)
   for i in range(0,nbfeat):
	print i
	feat1 = layer.GetFeature(i)
	geom1 = feat1.GetGeometryRef()
   	centroid = geom1.Centroid()
   	x = centroid.GetX()
   	y = centroid.GetY()
	minX = x - float(distance)
	minY = y - float(distance)
	maxX = x + float(distance)
	maxY = y + float(distance)
	layer.SetSpatialFilterRect(float(minX), float(minY), float(maxX), float(maxY))
	nbfeat2 =  layer.GetFeatureCount()
	intersection = False
	listFID = []
	listID = []
	for j in range(0,nbfeat2):
		feat2 = layer.GetFeature(j)
		#print feat1.GetFID()
		#print feat2.GetFID()
		geom1 = feat1.GetGeometryRef()
		geom2 = feat2.GetGeometryRef()
		if geom1.Intersects(geom2) == True and not geom1.Equal(geom2):
			listFID.append(feat2.GetFID())
			listID.append(feat2.GetField('id'))
				
	if len(listFID) == 0:
		outds = openToRead(outShp)
		outlayer = outds.GetLayer()
		if VerifyGeom(geom1,outlayer) == False:
			copyFeatInShp(feat1, outShp)
	elif len(listFID) == 1:
		for f in listFID:
			feat2 = layer.GetFeature(f)
			geom2 = feat2.GetGeometryRef()
			if feat1.GetFieldAsString(fieldin) == feat2.GetFieldAsString(fieldin):
				print feat1.GetFieldAsString('id')+" "+feat2.GetFieldAsString('id')
				newgeom =  Union(geom1, geom2)
			else:
				newgeom =  Difference(geom1, geom2)
			#newgeom =  Difference(geom1, geom2)
			newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
			newFeature = ogr.Feature(layerDef)
			newFeature.SetGeometry(newgeom2)
			for field in fields:
				newFeature.SetField(field, feat1.GetField(field))
		        copyFeatInShp(newFeature, outShp)
	elif len(listFID) > 1:
		for f in listFID:
			feat2 = layer.GetFeature(f)
			geom2 = feat2.GetGeometryRef()
			if feat1.GetFieldAsString(fieldin) == feat2.GetFieldAsString(fieldin):
				newgeom =  Union(geom1, geom2)
			else:
				newgeom =  Difference(geom1, geom2)
			#newgeom =  Difference(geom1, geom2)
			newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
			newFeature = ogr.Feature(layerDef)
			newFeature.SetGeometry(newgeom2)
			geom1 = newFeature.GetGeometryRef()
			for field in fields:
				newFeature.SetField(field, feat1.GetField(field))
			copyFeatInShp(newFeature, outShp)
	
   return outShp

#--------------------------------------------------------------------

def checkIntersect2(shp, fieldin, fieldinID):
   """
   Check if each feature intersects another feature in the same file. If True compute the difference. The common part is deleted
   """
   print "Verifying intersection"
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)
   outShp = copyShp(shp, 'nointersct')
   layerDef = layer.GetLayerDefn()
   fields = getFields(shp)
   for i in range(0,nbfeat):
	print i
	feat1 = layer.GetFeature(i)
	geom1 = feat1.GetGeometryRef()
   	centroid = geom1.Centroid()
   	layer.SetSpatialFilter(geom1)
	nbfeat2 =  layer.GetFeatureCount()
	intersection = False
	listFID = []
	listID = []
	for j in range(0,nbfeat2):
		feat2 = layer.GetFeature(j)
		#print feat1.GetFID()
		#print feat2.GetFID()
		geom1 = feat1.GetGeometryRef()
		geom2 = feat2.GetGeometryRef()
		if geom1.Intersects(geom2) == True and not geom1.Equal(geom2):
			listFID.append(feat2.GetFID())
			listID.append(feat2.GetField(fieldinID))
	if len(listFID) == 0:
		outds = openToRead(outShp)
		outlayer = outds.GetLayer()
		if VerifyGeom(geom1,outlayer) is False:
			copyFeatInShp2(feat1, outShp)
	elif len(listFID) == 1:
		for f in listFID:
			feat2 = layer.GetFeature(f)
			geom2 = feat2.GetGeometryRef()
			if feat1.GetFieldAsString(fieldin) == feat2.GetFieldAsString(fieldin):
				print feat1.GetFieldAsString(fieldinID)+" "+feat2.GetFieldAsString(fieldinID)
				newgeom =  Union(geom1, geom2)
			else:
				newgeom =  Difference(geom1, geom2)
			#newgeom =  Difference(geom1, geom2)
			newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
			newFeature = ogr.Feature(layerDef)
			newFeature.SetGeometry(newgeom2)
			for field in fields:
				newFeature.SetField(field, feat1.GetField(field))
		        copyFeatInShp2(newFeature, outShp)
	elif len(listFID) > 1:
		for f in listFID:
			feat2 = layer.GetFeature(f)
			geom2 = feat2.GetGeometryRef()
			if feat1.GetFieldAsString(fieldin) == feat2.GetFieldAsString(fieldin):
				newgeom =  Union(geom1, geom2)
			else:
				newgeom =  Difference(geom1, geom2)
			#newgeom =  Difference(geom1, geom2)
			newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
			newFeature = ogr.Feature(layerDef)
			newFeature.SetGeometry(newgeom2)
			geom1 = newFeature.GetGeometryRef()
			for field in fields:
				newFeature.SetField(field, feat1.GetField(field))
			copyFeatInShp2(newFeature, outShp)
	
   return outShp

#--------------------------------------------------------------------

def checkIntersect3(shp, fieldin, fieldinID):
   """
   Check if each feature intersects another feature in the same file. If True compute the difference. The common part is deleted
   """
   print "Verifying intersection"
   ds = openToWrite(shp)
   layer = ds.GetLayer()
   nbfeat = getNbFeat(shp)
   layerDef = layer.GetLayerDefn()
   fields = getFields(shp)
   listFID = []
   for i in range(0,nbfeat):
	feat1 = layer.GetFeature(i)
	geom1 = feat1.GetGeometryRef()
   	centroid = geom1.Centroid()
        layer2 = ds.GetLayer()
	layer2.SetSpatialFilter(None)
   	layer2.SetSpatialFilter(geom1)
	nbfeat2 =  layer2.GetFeatureCount()
	intersection = False
	listID = []
	for feat2 in layer2:
		geom2 = feat2.GetGeometryRef()
		if geom1.Intersects(geom2) == True and not geom1.Equal(geom2):
			listFID.append(feat2.GetFID())
			if feat1.GetFieldAsString(fieldin) == feat2.GetFieldAsString(fieldin):
				newgeom =  Union(geom1, geom2)
				newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
				newFeature = ogr.Feature(layerDef)
				newFeature.SetGeometry(newgeom2)
				geom1 = newFeature.GetGeometryRef()
				for field in fields:
					newFeature.SetField(field, feat1.GetField(field))
   				layer.CreateFeature(newFeature)
   				layer.SetFeature(newFeature)
			else:
				newgeom =  Difference(geom1, geom2)
				newgeom2 =  ogr.CreateGeometryFromWkb(newgeom.wkb)
				newFeature = ogr.Feature(layerDef)
				newFeature.SetGeometry(newgeom2)
				geom1 = newFeature.GetGeometryRef()
				for field in fields:
					newFeature.SetField(field, feat1.GetField(field))
   				layer.CreateFeature(newFeature)
   				layer.SetFeature(newFeature)

   for fid in range(0,len(listFID)):
	layer.DeleteFeature(listFID[fid])

   ds.ExecuteSQL('REPACK '+layer.GetName())
	
#------------------------------------------------------------------

def VerifyGeom(geom,layer):
	verif = False
	for feat in layer:
		geom2 = feat.GetGeometryRef()
		if geom and geom2:
			if geom.Equal(geom2):
				verif = True

	return verif

#--------------------------------------------------------------------

def Difference(geom1, geom2):

   from shapely.wkt import loads
   """
   Returns the difference of 2 geometries
   """
   obj1 = loads(geom1.ExportToWkt())
   obj2 = loads(geom2.ExportToWkt())
   return obj1.difference(obj2)

#--------------------------------------------------------------------
def Union(geom1, geom2):

   from shapely.wkt import loads
   """
   Returns the difference of 2 geometries
   """
   obj1 = loads(geom1.ExportToWkt())
   obj2 = loads(geom2.ExportToWkt())
   print obj1.union(obj2)
   return obj1.union(obj2)

#--------------------------------------------------------------------

def CheckDoubleGeomTwofiles(shp1, shp2):
   """Priority to file No. 1 """
   distance = 5000
   ds1 = openToRead(shp1)
   lyr1 = ds1.GetLayer()
   for feat1 in lyr1:
      if feat1.GetGeometryRef():
         geom1 = feat1.GetGeometryRef()
	 centroid = geom1.Centroid()
   	 x = centroid.GetX()
   	 y = centroid.GetY()
	 minX = x - float(distance)
	 minY = y - float(distance)
	 maxX = x + float(distance)
	 maxY = y + float(distance)
   	 ds2 = openToWrite(shp2)
   	 lyr2 = ds2.GetLayer()
	 lyr2.SetSpatialFilter(geom1)
         if lyr2.GetFeatureCount() == 0:
		lyr1.GetNextFeature()
	 else:
	    print lyr2.GetFeatureCount()
	    for feat2 in lyr2:
                fid = feat2.GetFID()
	    	geom2 = feat2.GetGeometryRef() 
		if geom1.Equal(geom2) == True:	
		   lyr2.DeleteFeature(fid)
                   ds2.ExecuteSQL('REPACK '+lyr2.GetName())
         lyr2.ResetReading()

#--------------------------------------------------------------------

def CheckDoubleGeomTwofilesCopy(shp1, shp2, field):

   """Priority to file No. 1 """

   ds1 = openToRead(shp1)
   lyr1 = ds1.GetLayer()
   ds2 = openToRead(shp2)
   lyr2 = ds2.GetLayer()
   newshp = copyShp(shp1, "commonshape")
   dict1 = dict()
   dict2 = dict()
   dict3 = dict()
   for feat in lyr1:
	values= []
	ge = feat.GetGeometryRef()
	f =  feat.GetFID()
	code = feat.GetField(field1)
	values.append(ge.ExportToWkt())
	values.append(code)
	dict1[f] = values
   for feat in lyr2:
	values= []
	ge = feat.GetGeometryRef()
	f =  feat.GetFID()
	code = feat.GetField(field1)
	values.append(ge.ExportToWkt())
	values.append(code)
	dict2[f] = values
   for k1,v1 in dict1:
	for k2, v2 in dict2:
		new_feat = lyr1.GetFeat(k1)
		copyFeatInShp2(new_feat, newshp)

#--------------------------------------------------------------------
		
def getFieldNames(shp_in):
	"""
		Get list of field names
		ARGs:
			INPUT:
				- shp_in: input shapefile
			OUTPUT:
				- list_field_names: list of field names
			(Other solution(?):
				ogrinfo -so shp_in short_shp_in
	"""
	list_field_names = []
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shp_in, 0)
	layer = dataSource.GetLayer()
	layerDefn = layer.GetLayerDefn()
	for i in range(layerDefn.GetFieldCount()):
		list_field_names.append(layerDefn.GetFieldDefn(i).GetName())
	return list_field_names


#--------------------------------------------------------------------

valid = False
empty = False
intersect = False
explain = False
delete = False
none = False

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Verify shapefile geometries." \
        "You have to choose only one option")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-v", action='store_true', \
                            help="Check the validity of geometries of input file." \
  	                    "If geometry is not valid then buffer 0 to correct", default = False)
        parser.add_argument("-e", action='store_true', \
                            help="Check if a geometry is empty and create a new file with no empty geometries", default = False)
        parser.add_argument("-i", action='store_true', \
                            help="Check if each feature intersects another feature in the same file." \
                            "If True compute the difference. The common part is deleted", default = False)
        parser.add_argument("-ev", action='store_true', \
                            help="Explains the validity reason of each feature in a shapefile", default = False)
        parser.add_argument("-d", action='store_true', \
                            help="Delete the invalide geometries in a file", default = False)
        
	args = parser.parse_args()

        if args.v or args.e or args.i or args.ev or args.d:
            if args.v:
                valid = True
            if args.e:
                empty = True
            if args.i:
                intersect = True
            if args.ev:
                explain = True
            if args.d:
                delete = True
        else:
            none = True
            
        if valid:
       	    checkValidGeom(args.shapefile)

       	if empty:
            checkEmptyGeom(args.shapefile)	

       	if intersect:
            checkIntersect3(args.shapefile, 'CODE','ID')

       	if explain:
            explain_validity(args.shapefile)

       	if delete:
            deleteInvalidGeom(args.shapefile)

        if none:
            prog = os.path.basename(sys.argv[0])
            print '      '+sys.argv[0]+' [options]' 
            print "     Help : ", prog, " --help"
            print "        or : ", prog, " -h"
            sys.exit(-1)  



