# -*- coding: utf-8 -*-
"""
Merge some shapefile simplified and clip them according to an another shape.

"""

import shutil
import sys
import os
import time
import argparse
import glob
import vector_functions as vf
import DeleteDuplicateGeometries
import OSO_functions as osof

def shape_export_simplification(path, shape_mask, grid, ndept, out):
    """
    Merge and clip shapefile tiles.
    
    in : 
        shape_mask : clip shapefile
        grid : grid from generate grid
        ndept : out directory name (departement name)
        shape_out : name of the shape out
        
    out :
        shape_out
    """
    
    debut_export_zone = time.time()
    
    #open shapefile
    grid_shape = osof.shape_open(grid,0)
    mask_shape = osof.shape_open(shape_mask,0)
    grid_layer = grid_shape.GetLayer()
    mask_layer = mask_shape.GetLayer()
    
    #list of cells from grid intersected by shape layer
    list_id_cells = []
    #list_files_tiles_tif = []
    
    #liste les cellules intersectees par le mask et recupere leur identifiant
    #dans une liste
    for feature1 in mask_layer:
        if int(feature1.GetField("CODE_DEPT")) == int(ndept):
            geom1 = feature1.GetGeometryRef()
            for feature2 in grid_layer:        
                geom2 = feature2.GetGeometryRef()
                if geom2.Intersects(geom1):
                    list_id_cells.append(int(feature2.GetField("FID")))
                    #list_files_tiles_tif.append(out + "/" + str(tile) + "/outfiles/tile_%s.tif"%(tile))
                    
    if len(list_id_cells) == 0:
        print "Il n'y a aucune tuile intersectant le departement %s ou celui-ci n'existe pas, arret."%(ndept)
        shutil.rmtree(out + "/dept_%s/"%(args.ndept))
        sys.exit()
        
    #selection de .shp qui se trouvent dans un dossier
    list_files_tiles = []
    
    for tile in list_id_cells :
        if os.path.isfile(out + "/" + str(tile) + "/outfiles/tile_%s.shp"%(tile)) :
            list_files_tiles.append(out + "/" + str(tile) + "/outfiles/tile_%s.shp"%(tile))
    
    osof.create_shape(path+"/dept_%s/merge.shp"%(ndept), 2154)

    #merge les shapes   
    for fichier in list_files_tiles :
        command = "ogr2ogr -update -addfields %s/merge.shp %s"%(path +"/dept_"+ndept, fichier)
        os.system(command)
    
    #command = "gdal_merge.py -n 0 -o %s/%s.tif %s"%(shape_out, shape_out,' '.join(list_files_tiles_tif))
    #os.system(command)
        
    #recupere la forme du departement
    command = "ogr2ogr -sql \"SELECT * FROM %s WHERE CODE_DEPT = \'%s\'\" %s %s"%(os.path.basename(shape_mask).split(".")[0], ndept, path+"/dept_"+ndept+"/dept_"+ndept+".shp", shape_mask)
    os.system(command)
    #clip selon la forme du departement
    command = "ogr2ogr -select value -clipsrc %s %s %s/merge.shp"%(path+"/dept_"+ndept+"/dept_"+ndept+".shp", path+"/dept_"+ndept+"/departement_"+ndept+".shp", path+"/dept_"+ndept)
    os.system(command)

    #va supprimer l'ensemble des geometries dupliquee
    DeleteDuplicateGeometries.DeleteDupGeom(path+"/dept_"+ndept+"/departement_"+ndept+".shp")

    #list_erase = glob.glob("dept_"+ndept+"/*")
    
    for paths, dirs, fichiers in os.walk(path):
        for fichier in fichiers :
            if not "nodoublegeom" in fichier :
                try :
                    os.remove(paths + "/dept_"+ndept + "/" + fichier)
                except :
                    continue
    
    for paths, dirs, fichiers in os.walk(path):
        for fichier in fichiers :
            try :
                os.rename(path + "/dept_"+ndept + "/" + fichier, path + "/dept_"+ndept+"/departement_"+ndept+".%s"%(fichier.split(".")[1]))
            except:
                continue
                
    fin_export_zone = time.time() - debut_export_zone
    
    for paths, dirs, fichiers in os.walk(path):
        for fichier in fichiers :
            try :
                shutil.copy(path + "/dept_" + ndept + "/" + fichier, out + "/dept_" + ndept + fichier)
            except :
                continue
    
    return fin_export_zone
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Merge, clip and calc stats" \
        "on simplification")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where tiles are located", required = True)
                                
        parser.add_argument("-grid", dest="grid", action="store", \
                                help="grid name", required = True)
                                
        parser.add_argument("-extract", dest="extract", action="store", \
                                help="departements shapefile", required = True)
                                
        parser.add_argument("-ndept", dest="ndept", action="store", \
                                help="departement number for directory and selection", required = True)
        
        parser.add_argument("-out", dest="out", action="store", \
                                help="out name directory", required = True)
                                
	args = parser.parse_args()
                   
        #os.chdir(args.path)
        if not os.path.exists(args.out+"/dept_%s"%(args.ndept)):
            os.mkdir(args.out+"/dept_%s"%(args.ndept))
        else :
            print "le repertoire de travail est %s."%("dept_"+args.ndept)
        
         
        if not os.path.exists(args.path+"/dept_%s"%(args.ndept)) :  
            os.mkdir(args.path+"/dept_%s"%(args.ndept))
        else :
            print "le repertoire de sortie est %s."%("dept_"+args.ndept)
            
        debut_total = time.time()                
        #merge shapefiles from mask
        time_export_zone = shape_export_simplification(args.path, args.extract, args.grid, args.ndept, args.out)
        
        with open(args.path + "/log_%s_zone_extract.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("time_export_zone\n")
            csvfile.close()
            
        #initialise un fichier log de serialisation tif
        with open(args.path + "/log_%s_zone_extract.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s\n"%(round(time_export_zone,0)))
            csvfile.close()
        
        #copy log
        shutil.copy(args.path + "/log_%s_zone_extract.csv"%(args.ndept), args.out + "/dept_%s"%(args.ndept) + "/log_%s_zone_extract.csv"%(args.ndept))
        
        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.path + "/dept_%s"%(args.ndept) + "/departement_%s.%s"%(args.ndept, ext)):
                shutil.copy(args.path + "/dept_%s"%(args.ndept) + "/departement_%s.%s"%(args.ndept, ext), args.out + "/dept_%s"%(args.ndept) + "/departement_%s.%s"%(args.ndept, ext))