#!/usr/bin/python

import ogr
import os, sys
import argparse
from math import *
import os, re, sys, glob, time

def create_grid(base_shp, out_grid, distance_line):
    """
    Function to build a grid with the same extend that input shapefile (base_shp)
    
    :param base_shp: Reference shapefile
    :type base_shp: str
    :param out_grid: Path of the output grid
    :type out_grid: str
    :param distance_line: Distance between every line in meter
    :type distance_line: int
    """
    
    # import ogr variable
    data_source = ogr.GetDriverByName('ESRI Shapefile').Open(base_shp, 0)
        
    if data_source is None:
        print('Could not open file')
        sys.exit(1)
        
    shp_ogr = data_source.GetLayer()
    
    # Extract extent
    extent_shp = shp_ogr.GetExtent()
    # Coordinate to build a set of line in a list

    nb_x = int(ceil((extent_shp[1] - extent_shp[0])/float(distance_line)))
    nb_y = int(ceil((extent_shp[3] - extent_shp[2])/float(distance_line)))    
    
    # Projection
    # Import input shapefile projection
    srsObj = shp_ogr.GetSpatialRef()
    # Conversion to syntax ESRI
    srsObj.MorphToESRI() 
           
    ## Remove the output shapefile if it exists
    if os.path.exists(out_grid):
        data_source.GetDriver().DeleteDataSource(out_grid)
    out_ds = data_source.GetDriver().CreateDataSource(out_grid)
    
    if out_ds is None:
        print('Could not create file')
        sys.exit(1)
        
    #  Specific output layer
    out_layer = out_ds.CreateLayer(str(out_grid), srsObj, geom_type=ogr.wkbLineString)
        
    # Add a integer field (ID)
    new_field = ogr.FieldDefn("ID", 0)
    out_layer.CreateField(new_field)
    # Feature for the ouput shapefile
    featureDefn = out_layer.GetLayerDefn()
    
    # Loop on the number of line nb_x next nb_y   
    cnt = 0
    for l in range(nb_x):

        # Define line string
        line = ogr.Geometry(ogr.wkbLineString)
        
        # Add a line
        line.AddPoint(extent_shp[0] + l * float(distance_line), extent_shp[3])
        line.AddPoint(extent_shp[0] + l * float(distance_line), extent_shp[2])
        
        # Create a new polygon
        out_feature = ogr.Feature(featureDefn)
        # Set the polygon geometry and attribute
        out_feature.SetGeometry(line)
        out_feature.SetField("ID", int(cnt))
        cnt = cnt + 1
            
        # Append polygon to the output shapefile
        out_layer.CreateFeature(out_feature)

        # Destroy polygons
        out_feature.Destroy() 
    
    for l in range(nb_y):

        # Define line string
        line = ogr.Geometry(ogr.wkbLineString)
        
        # Add a line
        line.AddPoint(extent_shp[0], extent_shp[3] - l * float(distance_line))
        line.AddPoint(extent_shp[1], extent_shp[3] - l * float(distance_line))
        
        # Create a new polygon
        out_feature = ogr.Feature(featureDefn)
        # Set the polygon geometry and attribute
        out_feature.SetGeometry(line)
        out_feature.SetField("ID", int(cnt))
        cnt = cnt + 1
            
        # Append polygon to the output shapefile
        out_layer.CreateFeature(out_feature)

        # Destroy polygons
        out_feature.Destroy()   
        
    # Close data
    out_ds.Destroy()  
    
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Function to build "\
                                         " a grid with the same extend that input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Reference shapefile", required = True)
        parser.add_argument("-d", dest="distance", action="store", \
                            help="Distance between every line in meter", required = True)
        parser.add_argument("-o", dest="outpath", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
	args = parser.parse_args()
        create_grid(args.shapefile, args.outpath, args.distance)
