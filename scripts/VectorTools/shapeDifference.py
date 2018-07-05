#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
	Bibliothèque pour des traitements sur fichier vector
	Dépendances : rtree
	Rq: field name should contain 10 characters maximum, otherwise field name is cutting
"""
import os, sys, osr
import shutil
import math
import random
from osgeo import gdal, ogr, osr
import argparse

#--------------------------------------------------------------
def init_fields(in_lyr, out_lyr):
	in_lyr_defn = in_lyr.GetLayerDefn()
	for id in range(in_lyr_defn.GetFieldCount()):
		#Get the Field Definition
		field = in_lyr_defn.GetFieldDefn(id)
		fname = field.GetName()
		ftype = field.GetTypeName()
		fwidth = field.GetWidth()       
		#Copy field definitions from source 
		if ftype == 'String':
			fielddefn = ogr.FieldDefn(fname, ogr.OFTString)
			fielddefn.SetWidth(fwidth)
		else:
			fielddefn = ogr.FieldDefn(fname, ogr.OFTInteger) 
		out_lyr.CreateField(fielddefn)	


#--------------------------------------------------------------				
def addMultiPolygon(simplePolygon, feature, out_lyr):
	"""
		Link with multipart2singlepart (above)
	"""
	featureDefn = out_lyr.GetLayerDefn()
	polygon = ogr.CreateGeometryFromWkb(simplePolygon)
	out_feat = ogr.Feature(featureDefn)
	out_feat.SetGeometry(polygon)
	# Loop over each field from the source, and copy onto the new feature
	for id in range(feature.GetFieldCount()):
		data = feature.GetField(id)
		out_feat.SetField(id, data)
	out_lyr.CreateFeature(out_feat) 

#--------------------------------------------------------------		
def diffBetweenLayers(layer1, layer2, layer_out):
	"""
		Difference of layer1 with layer2, save is done in layer_out
		ARGs:
			INPUT:
				- layer1: layer 1 
				- layer2: layer 2
				- layer_out: output layer
        """
	layer1.ResetReading()
	layer2.ResetReading()
	feature1 = layer1.GetNextFeature()
	while feature1:
		layer2.ResetReading()
		geom1 = feature1.GetGeometryRef()
		if geom1 == None:
			continue
		feature2 = layer2.GetNextFeature()
		newgeom = geom1
		while feature2:
			geom2 = feature2.GetGeometryRef()
			if geom2 == None:
				continue
			if newgeom == None:
				continue
						
			if geom1.Intersects(geom2) == 1:
				newgeom = newgeom.Difference(geom2)			
			feature2.Destroy()
			feature2 = layer2.GetNextFeature()
		if newgeom.GetGeometryName() == 'MULTIPOLYGON':
			for geom_part in newgeom:
				addMultiPolygon(geom_part.ExportToWkb(), feature1, layer_out)
		else:
			addMultiPolygon(newgeom.ExportToWkb(), feature1, layer_out)		
		feature1.Destroy()
		feature1 = layer1.GetNextFeature()


#--------------------------------------------------------------		

def diffBetweenLayersSpeedUp(layer2, layer1, layer_out, field_name=""):	
	"""
		Difference of layer1 with layer2, save is done in layer_out
		ARGs:
			INPUT:
				- layer1: layer 1 
				- layer2: layer 2
				- layer_out: output layer
				- field_name: attribute to look for difference
		(Inspire from http://snorf.net/blog/2014/05/12/using-rtree-spatial-indexing-with-ogr/)
	"""
	# RTree Spatial Indexing with OGR
	#-- Index creation
        try:
                import rtree
        except ImportError as e:
                raise ImportError(str(e) + "\n\n Please install rtree module if it isn't installed yet")

	print "Index creation..."
	index = rtree.index.Index(interleaved=False)

	for fid1 in range(0,layer1.GetFeatureCount()):
		feat1 = layer1.GetFeature(fid1)
		geom1 = feat1.GetGeometryRef()
		if geom1 == None:
			continue
		xmin, xmax, ymin, ymax = geom1.GetEnvelope()
		index.insert(fid1, (xmin, xmax, ymin, ymax))
		feat1.Destroy()
	#-- Search for all features in layer1 that intersect each feature in layer2
	print "Research..."
	for fid2 in range(0,layer2.GetFeatureCount()):
		feat2 = layer2.GetFeature(fid2)
		geom2 = feat2.GetGeometryRef()
		if geom2 == None:
			continue
		newgeom = geom2
		xmin, xmax, ymin, ymax = geom2.GetEnvelope()
		for fid1 in list(index.intersection((xmin, xmax, ymin, ymax))):
			# if fid1 != fid2: ???
			feat1 = layer1.GetFeature(fid1)
			geom1 = feat1.GetGeometryRef()
			if geom1 == None:
				continue
                        if field_name is not None:
                                if (geom2.Intersects(geom1)) and (feat1.GetField(field_name) != feat2.GetField(field_name)):
				        if newgeom == None:
					        continue
				        newgeom = newgeom.Difference(geom1)                                        
                        else:
                                if (geom2.Intersects(geom1)):
				        if newgeom == None:
					        continue
				        newgeom = newgeom.Difference(geom1)
			feat1.Destroy()
		if newgeom == None:
			continue
		if newgeom.GetGeometryName() == 'MULTIPOLYGON':
			for geom_part in newgeom:
				addMultiPolygon(geom_part.ExportToWkb(), feat2, layer_out)
		else:
			addMultiPolygon(newgeom.ExportToWkb(), feat2, layer_out)		
		feat2.Destroy()


#--------------------------------------------------------------		
def shapeDifference(shp_in1, shp_in2, shp_out, speed, field=""):
	"""
		Mergeby taking account field_name attribute
		ARGs:
			INPUT:
				- shp_in1: input filename 1
				- shp_in2: input filename 2
				- shp_out: name of output file
				- field_name: name of field to merge
		Use of R Tree Spatial Index (faster)
		TO DELETE SUPERPOSED POLYGONS OF SAME FIELD_NAME USED UNIONBUFFER()
	"""
	driver = ogr.GetDriverByName("ESRI Shapefile")
	shp1 = driver.Open(shp_in1, 0)
	shp2 = driver.Open(shp_in2, 0)

	if shp1 is None:
		print "Could not open file ", shp_in1
		sys.exit(1)
                
	if shp2 is None:
		print "Could not open file ", shp_in2
		sys.exit(1)
                
	layer1 = shp1.GetLayer()
	layer2 = shp2.GetLayer()
	
	#-- Create output file
	if os.path.exists(shp_out):
		os.remove(shp_out)
	try:
		output = driver.CreateDataSource(shp_out)
	except:
		print 'Could not create output datasource ', shp_out
		sys.exit(1)
                
	newLayer = output.CreateLayer('SymmetricDifference', geom_type = ogr.wkbPolygon, srs=layer1.GetSpatialRef())

	if newLayer is None:
                print "Could not create output layer"
		sys.exit(1)

        newLayerDef = newLayer.GetLayerDefn()
	init_fields(layer1, newLayer) ## shapefile 2 should have the same fields as
	
	#-- Processing
        if not speed:
	        diffBetweenLayers(layer1, layer2, newLayer)
        else:
                diffBetweenLayersSpeedUp(layer1, layer2, newLayer, field)
	
	shp1.Destroy()
	shp2.Destroy()	
			

speed = False
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Difference shapefile of" \
        "first shapefile with second shapefile, save is done in an output shapefile")
        parser.add_argument("-s1", dest="inshapefile", action="store", \
                            help="First shapefile", required = True)
        parser.add_argument("-s2", dest="reshapefile", action="store", \
                            help="Second shapefile", required = True)
        parser.add_argument("-o", dest="shapefileout", action="store", \
                            help="Output shapefile", required = True)        
        parser.add_argument("-speed", action="store_true", \
                            help="Use of R Tree Spatial Index (faster)", default = False)
        parser.add_argument("-f", dest="field", action="store", \
                            help="field to look for difference")        
	args = parser.parse_args()

        if not args.speed:
                print 'ici'
                shapeDifference(args.inshapefile, args.reshapefile, args.shapefileout, False, None)
        else:
                try:
                        import rtree
                except ImportError as e:
                        raise ImportError(
                                str(e)
                                + "\n\n Please install rtree module if it isn't installed yet")
                
                shapeDifference(args.inshapefile, args.reshapefile, args.shapefileout, True, args.field)
