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
    from Common import Utils    
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

try:    
    from VectorTools import DeleteDuplicateGeometriesSqlite as ddg
    from VectorTools import vector_functions as vf
    from VectorTools import AddFieldArea as afa
    from simplification import VectAndSimp as vas
    
except ImportError:
    raise ImportError('Vector tools not well configured / installed')

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


def getTilesFiles(zone, tiles, folder, idTileField, tileNamePrefix, localenv, fieldzone = "", valuezone = "", driver = "ESRI Shapefile"):

    for ext in ['.shp', '.dbf', '.shx', '.prj']:
        shutil.copy(os.path.splitext(zone)[0] + ext, localenv)
        
    zone = os.path.join(localenv, os.path.basename(zone))
    
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
        
        nbinter = 0
        # iterate tiles to find intersection
        for featTile in lyrTiles:
            geomTile = featTile.GetGeometryRef()
            nbTile = int(featTile.GetField(idTileField))
            if geomTile.Intersects(geomZone):
                nbinter += 1
                tilename = os.path.join(folder, tileNamePrefix + str(nbTile) + '.tif')
                if os.path.exists(tilename):
                    listFilesTiles.append(tilename)
                else:
                    raise Exception('Tiles folder or prefix name of classification rasters do not exist')          

        if nbinter == 0:
            raise Exception('No Tile for the given area')          
    
    return listFilesTiles

def mergeTileRaster(path, rasters, fieldclip, valueclip, localenv):

    tomerge = []
    for rasttile in rasters:
        rasttiletmp = os.path.join(localenv, os.path.splitext(os.path.basename(rasttile))[0] + '_nd.tif')
        bmappli = oa.CreateBandMathApplication({"il":rasttile, "out": rasttiletmp, "exp":'im1b1 < 223 ? im1b1 : 0'})
        bmappli.ExecuteAndWriteOutput()
        tomerge.append(rasttiletmp)

    outraster = os.path.join(localenv, "tile_" + fieldclip + "_" + str(valueclip) + '.tif')
    sx, sy = fut.getRasterResolution(tomerge[0])
    fut.assembleTile_Merge(tomerge, sx, outraster, "Byte")

    for rasttile in tomerge:
        os.remove(rasttile)

    return outraster

def getListValues(checkvalue, clipfile, clipfield, clipvalue=""):

    listvalues = []
    if checkvalue:
        listvalues.append([val for val in vf.ListValueFields(clipfile, clipfield)])
    else:
        if clipvalue in vf.ListValueFields(clipfile, clipfield):
            listvalues.append([clipvalue])
        else:
            raise Exception("Value {} does not exist in the zone file {} for field {}".format(clipvalue, clipfile, clipfield))

    return listvalues[0]

def tilesRastersMergeVectSimp(path, tiles, out, grass, mmu, \
                              fieldclass, clipfile, fieldclip, valueclip, tileId, tileNamePrefix, tilesfolder, \
                              douglas, hermite, angle):

    timeinit = time.time()

    # local environnement
    localenv = os.path.join(path, "tmp%s"%(str(valueclip)))
    if os.path.exists(localenv):shutil.rmtree(localenv)
    os.mkdir(localenv)

    # Find vector tiles concerned by the given zone
    listTilesFiles = getTilesFiles(clipfile, tiles, tilesfolder, tileId, tileNamePrefix, localenv, fieldclip, valueclip)
    
    # Merge rasters
    localListTilesFiles = []
    for tile in listTilesFiles:
        shutil.copy(tile, localenv)
        localListTilesFiles.append(os.path.join(localenv, os.path.basename(tile))) 
        
    finalraster = mergeTileRaster(path, localListTilesFiles, fieldclip, valueclip, localenv)

    timemerge = time.time()     
    print " ".join([" : ".join(["Merge Tiles", str(timemerge - timeinit)]), "seconds"])

    # Raster vectorization and simplification
    outvect = os.path.join(localenv, finalraster[:-4] + '.shp')
    if os.path.exists(outvect):os.remove(outvect)
    vas.simplification(localenv, finalraster, grass, outvect, douglas, hermite, mmu, angle)    

    # Delete raster after vectorisation
    os.remove(finalraster)
    
    timevect = time.time()     
    print " ".join([" : ".join(["Vectorisation and Simplification", str(timevect - timemerge)]), "seconds"])
    
    # Get clip shafile layer    
    if clipfile is not None:
        for ext in ['.shp', '.dbf', '.shx', '.prj']:            
            shutil.copy(os.path.splitext(clipfile)[0] +  ext, localenv)

        clipfile = os.path.join(localenv, os.path.basename(clipfile))
            
        if vf.getNbFeat(os.path.join(localenv, clipfile)) != 1:
            clip = os.path.join(localenv, "clip.shp")
            layer = vf.getFirstLayer(clipfile)
            fieldType = vf.getFieldType(os.path.join(localenv, clipfile), fieldclip)

            if fieldType == str:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = \'%s\'\" %s %s"%(layer, \
                                                                                       fieldclip, \
                                                                                       valueclip, \
                                                                                       clip, \
                                                                                       clipfile)
                Utils.run(command)
            elif fieldType == int or fieldType == float:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = %s\" %s %s"%(layer, \
                                                                                   fieldclip, \
                                                                                   valueclip, \
                                                                                   clip, \
                                                                                   clipfile)
                Utils.run(command)             
            else:
                raise Exception('Field type %s not handled'%(fieldType))
        else:
            clip = os.path.join(localenv, clipfile)
            print "'%s' shapefile has only one feature which will used to clip data"%(clip)
        
        # clip
        clipped = os.path.join(localenv, "clipped.shp")
        command = "ogr2ogr -select cat -clipsrc %s %s %s"%(clip, \
                                                           clipped, \
                                                           outvect)
        Utils.run(command)

        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            if os.path.exists(os.path.splitext(outvect)[0] + ext):
                os.remove(os.path.splitext(outvect)[0] + ext)
            if os.path.exists(os.path.splitext(clipfile)[0] + ext):
                os.remove(os.path.splitext(clipfile)[0] + ext)
            if os.path.exists(os.path.splitext(clip)[0] + ext):
                os.remove(os.path.splitext(clip)[0] + ext)
        
    else:
        clipped = os.path.join(localenv, "merge.shp")

    timeclip = time.time()     
    print " ".join([" : ".join(["Clip final shapefile", str(timeclip - timevect)]), "seconds"])            
        
    # Delete duplicate geometries
    ddg.deleteDuplicateGeometriesSqlite(clipped)
    
    for ext in [".shp",".shx",".dbf",".prj"]:
        shutil.copy(os.path.splitext(clipped)[0] + ext, os.path.join(localenv, "clean") + ext)
        os.remove(os.path.splitext(clipped)[0] + ext)

    timedupli = time.time()     
    print " ".join([" : ".join(["Delete duplicated geometries", str(timedupli - timeclip)]), "seconds"])            
        
    # Input shapefile
    init_grass(path, grass)
    gscript.run_command("v.in.ogr", flags="e", input=os.path.join(localenv, "clean.shp"), output="cleansnap", snap="1e-07")             
    
    # Rename column
    if fieldclass:
        gscript.run_command("v.db.renamecolumn", map="cleansnap@datas", column="cat_,%s"%(fieldclass))
    
    # Export shapefile
    outtmp = os.path.join(localenv, os.path.splitext(os.path.basename(out))[0] + str(valueclip) + os.path.splitext(os.path.basename(out))[1])

    if os.path.exists(outtmp):os.remove(outtmp)
    gscript.run_command("v.out.ogr", flags = "s", input = "cleansnap@datas", output = outtmp, format = "ESRI_Shapefile")

    # Check geom
    vf.checkValidGeom(outtmp)
    
    # Add Field Area (hectare)
    afa.addFieldArea(outtmp, 10000)
    
    timeprodvect = time.time()     
    print " ".join([" : ".join(["Production of final shapefile geometry", str(timeprodvect - timeinit)]), "seconds"])

    for ext in ['.shp', '.dbf', '.shx', '.prj']:
        shutil.copyfile(os.path.splitext(outtmp)[0] + ext, os.path.splitext(out)[0] + str(valueclip) + ext)
        if os.path.exists(os.path.splitext(outtmp)[0] + ext):
            os.remove(os.path.splitext(outtmp)[0] + ext)
        if os.path.exists(os.path.join(localenv, "clean%s"%(ext))):
            os.remove(os.path.join(localenv, "clean%s"%(ext)))
        if os.path.exists(os.path.join(localenv, "clipped%s"%(ext))):
            os.remove(os.path.join(localenv, "clipped%s"%(ext)))
            
    if os.path.exists(os.path.join(localenv, "grassdata")):
        shutil.rmtree(os.path.join(localenv, "grassdata"))

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

        parser.add_argument("-listTiles", dest="listTiles", action="store", \
                                help="tiles file", required = True)

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

        parser.add_argument("-extract", dest="extract", action="store", required = True, \
                                help="clip shapefile")

        parser.add_argument("-field", dest="field", action="store", \
                                help="Field to select feature to clip")

        parser.add_argument("-value", dest="value", action="store", \
                                help="Value of the field to select feature to clip")

        parser.add_argument("-fieldclass", dest="fieldclass", action="store", \
                                help="land-cover field name of output vector file")
        
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


