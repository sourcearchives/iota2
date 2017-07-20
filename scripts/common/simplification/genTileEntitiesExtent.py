# -*- coding: utf-8 -*-
"""
Calculate tile entities extent shapefile

"""

import sys
import os
import argparse
from osgeo import gdal,ogr,osr
import csv
from osgeo.gdalconst import *
import numpy as np
import OSO_functions as osof
import shutil
from skimage.measure import regionprops

def listTileEntities(raster, outpath, ngrid, feature):

    # ouvre le clump et la classification de la zone ayant ete decoupee
    datas_classif, xsize_classif, ysize_classif, projection_classif, transform_classif, raster_band_classif = osof.raster_open(raster, 1)
    datas_clump, xsize_clump, ysize_clump, projection_clump, transform_clump, raster_band_clump = osof.raster_open(raster, 2)
    print "\nXsize de la zone de recherche", xsize_classif,"Ysize de la zone de recherche",ysize_classif                    
                        
    # calcule l'emprise de la tuile en lignes,colonne d'apres le fichier vecteur grille
    cols_xmin_decoup, cols_xmax_decoup, cols_ymin_decoup, cols_ymax_decoup = osof.coords_cell(feature, transform_classif)

    # extrait un sous tableau de la tuile afin de selectionner les identifiants et classes
    tile_classif = datas_classif[cols_ymin_decoup:cols_ymax_decoup, cols_xmin_decoup:cols_xmax_decoup]                
    tile_id_all = datas_clump[cols_ymin_decoup:cols_ymax_decoup, cols_xmin_decoup:cols_xmax_decoup]
                    
    # supprime les variables plus necessaires et couteuses en ram
    del datas_classif, datas_clump
                    
    # genere la liste des indentifiants des entites incluses dans la tuile
    tile_id = np.unique(np.where(((tile_classif > 1) & (tile_classif < 250)), tile_id_all, 0)).tolist()
                    
    # enleve de la liste les entites nodata
    tile_id = [x for x in tile_id if x != 0]

    return tile_id

def Extent(tile_id, Params, xsize, ysize):

    subParams = {x:Params[x] for x in tile_id}
    valsExtents = list(subParams.values()) 

    minCol = min([y for x, y, z, w in valsExtents])
    minRow = min([x for x, y, z, w in valsExtents])
    maxCol = max([w for x, y, z, w in valsExtents])       
    maxRow = max([z for x, y, z, w in valsExtents])
    
    #soustrait et ajoute 1 pixels (si ce n'est pas au bord du raster) pour effectuer un otb dilate
    if minRow > 0:
        minRow -= 1
    if minCol > 0:
        minCol -= 1
    if maxRow < ysize:
        maxRow += 1
    if maxCol < xsize:
        maxCol += 1

    return [minRow, minCol, maxRow, maxCol]

def genEnveloppe(transform, minRow, minCol, maxRow, maxCol):
    
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    minX = xOrigin + pixelWidth * minCol
    minY = yOrigin + pixelHeight * minRow
    maxX = xOrigin + pixelWidth * maxCol
    maxY = yOrigin + pixelHeight * maxRow
    
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX, minY)
    ring.AddPoint(maxX, minY)
    ring.AddPoint(maxX, maxY)
    ring.AddPoint(minX, maxY)
    ring.AddPoint(minX, minY)

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    return poly

def genGrid(shapeEnvelop, list_geom_envelop):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.CreateDataSource(shapeEnvelop)
    layerName = shapeEnvelop.split("/")[-1].split(".")[0]
    print layerName
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(2154)
    layer = data_source.CreateLayer(layerName, srs, geom_type=ogr.wkbPolygon)
    field_tile = ogr.FieldDefn("Tile", ogr.OFTInteger)
    field_tile.SetWidth(5)
    layer.CreateField(field_tile)

    for geom in list_geom_envelop:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Tile", geom[0])
        feature.SetGeometry(geom[1])
        layer.CreateFeature(feature)
        
    layer = feature = data_source = None

#------------------------------------------------------------------------------         
def genTileEntitiesExtent(inpath, raster, grid, outpath, shapeEnvelop):
    """
        
        in : 
            inpath : working directory with datas
            raster : name of raster
            grid : grid name for serialisation
            outpath : name of output directory    
            
        out :
            shapeEnvelop : tile entities extent shapefile 
    """        

    # ouverture de la classification regularise pour recuperer ses informations geographiques
    clump = raster[:-4] + '_clump.tif'
    command = "gdal_translate -ot Uint32 %s %s"%(raster, clump)
    os.system(command)
    
    rasterfile = gdal.Open(clump, 0)    
    clumpBand = rasterfile.GetRasterBand(2)
    clumpArray = clumpBand.ReadAsArray()    
    clumpProps = regionprops(clumpArray)

    transform = rasterfile.GetGeoTransform()
    xsize = rasterfile.RasterXSize
    ysize = rasterfile.RasterYSize

    rasterfile = None
    
    #generation dictionnaire label:bbox
    Params = {}
    i=0
    while clumpProps:
        try:
            Params[clumpProps[i].label] = clumpProps[i].bbox
            i+=1
        except:
            IndexError
            print "Fin generation dicitonnaire label:bbox"
            break
    
    #genere un dictionnai
    print "Xsize", xsize, "Ysize", ysize
    
    # ouvre le fichier grille dans le dossier parent
    grid_open = osof.shape_open(grid,0)
    grid_layer = grid_open.GetLayer()

    list_geom_envelop = []

    # pour chaque tuile    
    for feature in grid_layer :
        
        #recupere son id
        ngrid = int(feature.GetField("FID"))

        print "-------------------------------------------------------\n\nTuile",\
        ngrid
            
        #genere liste entites
        listTileId = listTileEntities(clump, outpath, ngrid, feature)
        print "Nombre d'entites dans la tuile : %s"%(len(listTileId))
        
        if len(listTileId) != 0:
            #calcule l'emprise de la zone à decouper +1 et -1 pixel (pour effectuer otb dilate)
            #exemple de sortie : [0L, 0L, 163L, 236L] soit [minRow, minCol, maxRow, maxCol]
            listExtent = Extent(listTileId, Params, xsize, ysize)

            list_geom_envelop.append([ngrid, genEnveloppe(transform, listExtent[0], listExtent[1], listExtent[2], listExtent[3])])
            
        else:
            print "Aucun calcul d'emprise des entités"

    genGrid(inpath + '/' + shapeEnvelop, list_geom_envelop)


#------------------------------------------------------------------------------
      
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Calculate tile entities extent shapefile")
        
        parser.add_argument("-wd", dest="path", action="store", \
                            help="working directory", required = True)
   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of raster bi-bands : classification (regularized) + clump (patches of pixels)", required = True)
                                
        parser.add_argument("-grid", dest="grid", action="store", \
                            help="grid name", required = True)                                
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="outname directory", required = True)   

        parser.add_argument("-env", dest="shapeEnvelop", action="store", \
                            help="Entities extent shapefile", required = True)       
                                
    args = parser.parse_args()

    genTileEntitiesExtent(args.path, args.classif, args.grid,  args.out, args.shapeEnvelop)

    for ext in ["shp","shx","dbf","prj"] :
        if os.path.exists(args.path + "/" + args.shapeEnvelop):
            shutil.copy(args.path + "/" + args.shapeEnvelop[:-4] + '.' + ext, \
                        args.out + "/"+ args.shapeEnvelop[:-4] + '.' + ext)
