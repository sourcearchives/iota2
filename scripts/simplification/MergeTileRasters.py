#!/usr/bin/python
# -*- coding: utf-8 -*-

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

"""
Merge some shapefile simplified and clip them according to an another shape.

"""

import sys, os, argparse, time, shutil
import subprocess
from osgeo import ogr
import osgeo.ogr

try:
    from Common import FileUtils as fut
    from Common import OtbAppBank as oa
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

try:    
    from VectorTools import DeleteDuplicateGeometries as ddg
    from VectorTools import vector_functions as vf
    from VectorTools import AddFieldArea as afa    
except ImportError:
    raise ImportError('Vector tools not well configured / installed')

import VectAndSimp as vas

def init_grass(path, grasslib):

    """
    Initialisation of Grass GIS in lambert 93.
    
    in : 
        path : directory where create grassdata directory
        grasslib : install directory of Grass GIS
    """ 
    
    global gscript  
    
    # Grass folder Initialisation
    if not os.path.exists(os.path.join(path, "grassdata")):
        os.mkdir(os.path.join(path, "grassdata"))
    path_grassdata = os.path.join(path, "grassdata")
    
    # Init Grass environment
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase
    
    # Overwrite and verbose parameters
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']='-1'
    
    # Grass functions import
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    # Init Grass
    gsetup.init(gisbase, gisdb)
    
    # Delete existing location
    if os.path.exists(os.path.join(gisdb, "demolocation")):
        shutil.rmtree(os.path.join(gisdb, "demolocation"))
    
    # Create the location in Lambert 93
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    # Create datas mapset
    if not os.path.exists(os.path.join(gisdb, "/demolocation/datas")) :
        try:
            gscript.start_command("g.mapset", flags="c", mapset = "datas", location = "demolocation", dbase = gisdb)
        except:
            raise Exception("Folder '%s' does not own to current user")%(gisdb)

# get tiles corresponding to the zone
def getTilesFiles(zone, tiles, folder, idTileField, tileNamePrefix, fieldzone = "", valuezone = "", driver = "ESRI Shapefile"):
    
    driver = ogr.GetDriverByName(driver)
    if isinstance(zone, str):
        try:
            shape = driver.Open(zone, 0)
        except:
            raise Exception('%s is not a vector file'%(zone))
        
        lyrZone = shape.GetLayer()
    elif isinstance(zone, osgeo.ogr.Layer):
        lyrZone = zone
        zone = None
        zone = lyrZone.GetName() + '.shp'
    else:
        raise Exception('Zone parameter must be a shapefile or layer object')

    tiles = driver.Open(tiles, 0)    
    lyrTiles = tiles.GetLayer()    
    
    listFilesTiles = []

    # get zone geometry
    fieldType = vf.getFieldType(zone, fieldzone)
    if fieldType == int:
        lyrZone.SetAttributeFilter(fieldzone + " = " + str(valuezone))
    elif fieldType == str:
        lyrZone.SetAttributeFilter(fieldzone + " = \'%s\'"%(valuezone))
    else:
        raise Exception('Field type %s not handled'%(fieldType))

    if lyrZone.GetFeatureCount() != 0:
        for featZone in lyrZone:
            geomZone = featZone.GetGeometryRef()

        # iterate tiles to find intersection
        for featTile in lyrTiles:
            geomTile = featTile.GetGeometryRef()
            nbTile = int(featTile.GetField(idTileField))
            if geomTile.Intersects(geomZone):
                tilename = os.path.join(folder, tileNamePrefix + str(nbTile) + '.tif')
                if os.path.exists(tilename):
                    listFilesTiles.append(tilename)
                else:
                    raise Exception('Tiles folder or prefix name of classification rasters do not exist')

    else:
        raise Exception('No Tile for the given area')

    return listFilesTiles

def mergeTileRaster(path, rasters, fieldclip, valueclip):

    tomerge = []
    for rasttile in rasters:
        rasttiletmp = os.path.join(path, os.path.splitext(os.path.basename(rasttile))[0] + '_nd.tif')
        print rasttiletmp
        bmappli = oa.CreateBandMathApplication({"il":rasttile, "out": rasttiletmp, "exp":'im1b1 < 223 ? im1b1 : 0'})
        bmappli.ExecuteAndWriteOutput()
        tomerge.append(rasttiletmp)

    outraster = os.path.join(path, "tile_" + fieldclip + str(valueclip) + '.tif')
    sx, sy = fut.getRasterResolution(tomerge[0])
    fut.assembleTile_Merge(tomerge, sx, outraster, "Byte")

    return outraster

        
def tilesRastersMergeVectSimp(path, tiles, out, grass, mmu, \
                              fieldclass, clipfile, fieldclip, valueclip, tileId, tileNamePrefix, tilesfolder, \
                              douglas, hermite, angle):

    timeinit = time.time()

    # Find vector tiles concerned by the given zone
    if clipfile != "":
        if isinstance(tiles, str):
            listTilesFiles = tiles
        elif isinstance(tiles, list):
            listTilesFiles = getTilesFiles(clipfile, tiles[0], tilesfolder, tileId, tileNamePrefix, fieldclip, valueclip)            
        else:
            raise Exception("'tiles' parameter must be string (vector file of tiles) or list (list of files)")
    else:
        listTilesFiles = tiles
        
    # Merge rasters
    finalraster = mergeTileRaster(path, listTilesFiles, fieldclip, valueclip)

    timemerge = time.time()     
    print " ".join([" : ".join(["Merge Tiles", str(timemerge - timeinit)]), "seconds"])

    # Raster vectorization and simplification
    outvect = finalraster[:-4] + '.shp'
    vas.simplification(path, finalraster, grass, outvect, douglas, hermite, mmu, angle)    

    timevect = time.time()     
    print " ".join([" : ".join(["Vectorisation and Simplification", str(timevect - timemerge)]), "seconds"])
    
    # Get clip shafile layer    
    
    if clipfile is not None:
        if vf.getNbFeat(clipfile) != 1:
            clip = os.path.join(path, "clip.shp")
            layer = vf.getFirstLayer(clipfile)
            fieldType = vf.getFieldType(clipfile, fieldclip)

            if fieldType == str:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = \'%s\'\" %s %s"%(layer, \
                                                                                       fieldclip, \
                                                                                       valueclip, \
                                                                                       clip, \
                                                                                       clipfile)
            elif fieldType == int or fieldType == float:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = %s\" %s %s"%(layer, \
                                                                                   fieldclip, \
                                                                                   valueclip, \
                                                                                   clip, \
                                                                                   clipfile)
            else:
                raise Exception('Field type %s not handled'%(fieldType))
        else:
            clip = clipfile
            print "'%s' shapefile has only one feature which will used to clip data"%(clip)
            
        os.system(command)
        
        # clip
        clipped = os.path.join(path, "clipped.shp")
        command = "ogr2ogr -select %s -clipsrc %s %s %s"%(fieldclass, \
                                                          clip, \
                                                          clipped, \
                                                          outvect)
        os.system(command)
        
    else:
        clipped = os.path.join(path, "merge.shp")

    timeclip = time.time()     
    print " ".join([" : ".join(["Clip final shapefile", str(timeclip - timevect)]), "seconds"])            
        
    # Delete duplicate geometries
    outshape = ddg.DeleteDupGeom(clipped)
    
    for ext in [".shp",".shx",".dbf",".prj"]:
        shutil.copy(os.path.splitext(outshape)[0] + ext, os.path.join(path, "clean") + ext)    

    timedupli = time.time()     
    print " ".join([" : ".join(["Delete duplicated geometries", str(timedupli - timeclip)]), "seconds"])            
        
    # Input shapefile
    init_grass(path, grass)
    gscript.run_command("v.in.ogr", flags="e", input=os.path.join(path, "clean.shp"), output="cleansnap", snap="1e-07")             
    
    # Rename column
    if fieldclass == 'cat':
        gscript.run_command("v.db.renamecolumn", map="cleansnap@datas", column="cat_,class")
    else:
        gscript.run_command("v.db.renamecolumn", map="cleansnap@datas", column="%s,class"%(fieldclass))
    
    # Export shapefile
    outtmp = os.path.join(path, os.path.basename(out))
    gscript.run_command("v.out.ogr", flags = "s", input = "cleansnap@datas", dsn = outtmp, format = "ESRI_Shapefile")

    # Check geom
    vf.checkValidGeom(outtmp)
    
    # Add Field Area (hectare)
    afa.addFieldArea(outtmp, 10000)
    
    timeprodvect = time.time()     
    print " ".join([" : ".join(["Production of final shapefile geometry", str(timeprodvect - timeinit)]), "seconds"])

    for ext in ['.shp', '.dbf', '.shx', '.prj']:
        shutil.copyfile(os.path.splitext(outtmp)[0] + ext, os.path.splitext(out)[0] + ext)
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Merge and clip vector tiles " \
        "on a given vector zone")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)

        parser.add_argument("-listTiles", dest="listTiles", nargs='+', \
                                help="list of tiles shapefiles or tiles file", required = True)

        parser.add_argument("-tileId", dest="tileId", action="store", \
                                help="Field to unambiguous identify tiles")        

        parser.add_argument("-prefix", dest="prefix", action="store", \
                                help="classification vector name prefix (tiled)")
        
        parser.add_argument("-tileFolder", dest="tileFolder", action="store", \
                                help="vectors of classification (tiled) folder")   
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)

        parser.add_argument("-out", dest="out", action="store", \
                                help="out name file and directory", required = True)
        
        parser.add_argument("-mmu", dest="mmu", action="store", \
                                help="Mininal Mapping Unit (shapefile area unit)", type = int, required = True)                

        parser.add_argument("-extract", dest="extract", action="store", \
                                help="clip shapefile")

        parser.add_argument("-field", dest="field", action="store", \
                                help="Field to select feature to clip")

        parser.add_argument("-value", dest="value", action="store", \
                                help="Value of the field to select feature to clip")

        parser.add_argument("-fieldclass", dest="fieldclass", action="store", \
                                help="Field to keep in final vector file")
        
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="Douglas-Peucker reduction value, if empty no Douglas-Peucker reduction")   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="Hermite smoothing level, if empty no Hermite smoothing reduction")   
                            
        parser.add_argument("-angle", action="store_true", \
                            help="Smooth corners of pixels (45°), if empty no corners smoothing", default = False)           
        
	args = parser.parse_args()
        
        tilesRastersMergeVectSimp(args.path, args.listTiles, args.out, args.grass, args.mmu, \
                                  args.fieldclass, args.extract, args.field, args.value, args.tileId, args.prefix, args.tileFolder, \
                                  args.douglas, args.hermite, args.angle)


#python chaineIOTA/iota2/scripts/simplification/MergeTileRasters.py -wd $TMPDIR -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017 -listTiles /work/OT/theia/oso/classifications/Simplification/2017/production/out/oso2017_grid.shp -out /work/OT/theia/oso/classifications/Simplification/2017/production/out/departements/departement_8.shp -mmu 1000 -extract /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/FranceDepartements.shp -field CODE_DEPT -value "08" -fieldclass cat -tileId FID -prefix tile_ -tileFolder /work/OT/theia/oso/classifications/Simplification/2017/production/out/voisins -douglas 10 -hermite 10 -angle    
