# -*- coding: utf-8 -*-
"""

"""
import sys
import os
import argparse
import numpy as np
import OSO_functions as osof
import shutil

#------------------------------------------------------------------------------         
def list_tiles(inpath, raster, ram, grid):
    """
        
        in : 
            path : working directory with datas
            raster : name of raster
            ram : number of strippe for otb
            grid : grid name for serialisation
            outfiles : name of output directory
            
        out :
            raster with nomelized name (tile_ngrid.tif)
    """
    #ouverture de la classification regularise
    datas,xsize,ysize,projection,transform,raster_band = osof.raster_open(raster, 1)
    
    #ouverture du clump
    datas_clump,xsize_clump,ysize_clump,projection_clump,transform_clump,raster_band_clump = osof.raster_open(raster, 2)
    
    #ouvre le fichier grille dans le dossier parent
    grid_open = osof.shape_open(grid,0)
    grid_layer = grid_open.GetLayer()
    
    liste_tiles_process = []    
    #pour chaque cellule    
    for feature in grid_layer :           
        i = int(feature.GetField("FID"))
            
        #emprise de la cellule de la grille
        cols_xmin, cols_xmax, cols_ymin, cols_ymax = osof.coords_cell(feature, transform)
        
        #extrait un sous tableau pour obtenir la liste des id, attention les x y 
        #s'inversent dans la cellule
        tile_id_all = datas_clump[cols_ymin:cols_ymax, cols_xmin:cols_xmax]
        tile_classe = datas[cols_ymin:cols_ymax, cols_xmin:cols_xmax]
        
        #genere la liste des indentifiants
        tile_id = np.unique(np.where(((tile_classe > 1) & (tile_classe < 250)), tile_id_all, 0)).tolist()

        #nettoie la liste
        tile_id = [x for x in tile_id if x != 0]

        #si la cellule ne contient qu'un seul identifiant, c'est probablement
        #une cellule composee uniquement de nodata, donc on passe
        if len(tile_id) == 0 :
            continue           
        else : 
            liste_tiles_process.append(i)

    return liste_tiles_process
    
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "tif generation for simplification")
        
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)
   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of raster bi-bands : classification (regularized) + clump (patches of pixels)", required = True)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-strippe", dest="ram", action="store", \
                            help="Number of strippe for otb process", required = True)
                                
        parser.add_argument("-grid", dest="grid", action="store", \
                            help="grid name", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="outname directory", required = True)
                                
    args = parser.parse_args()
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
        
    liste_tiles_process = list_tiles(args.path, args.classif, args.ram, args.grid)
    
    np.savetxt(args.path + "/list_tiles_process.csv",liste_tiles_process,  fmt="%s")
    
    #with open(args.path + "/list_tiles_process.csv", "w") as csvfile:
        #csvfile.write(','.join([str(i) for i in liste_tiles_process]))
    
    shutil.copy(args.path + "/list_tiles_process.csv", args.out + "/list_tiles_process.csv")