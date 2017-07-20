# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 15:29:32 2017

@author: donatien
"""
import sys
import os
import argparse
from osgeo import gdal,ogr,osr
from operator import itemgetter
import OSO_functions as osof
from skimage.measure import regionprops
import matplotlib.pyplot as plt
import numpy as np

def ClumpSurface(rasterFile,out, outcsv):
    """
        Retourne un dictionnaire {identifiant:surface}
    """
    #ouvre la classification   
    #classif,xsize,ysize,projection,transform,raster_band = raster_open(rasterFile, 1)  
    #ouvre le clump   
    clump,xsize,ysize,projection,transform,raster_band = osof.raster_open(rasterFile, 2)
    #calcul un ensemble de donnees sur le clump
    regionsDatas = regionprops(clump)

    #tant qu'il y a des entites, recupere son label et son nombre de pixels dans
    #un dictionnaire
    i=0 
    #dic = {}
    #dicBbox = {}
    #dicFillImf = {}
    
    with open(outcsv, "w") as csvfile:
        csvfile.write("id;nbpixels;xmin;ymin;xmax;ymax\n")
        while regionsDatas:
            try:
                #dic.update({regionsDatas[i].label:regionsDatas[i].area})
                #dicBbox.update({regionsDatas[i].label:regionsDatas[i].bbox})
                #dicFillImf.update({regionsDatas[i].label:regionsDatas[i].filled_image})
                identifiant = regionsDatas[i].label
                area = regionsDatas[i].area
                xmin, ymin, xmax, ymax = regionsDatas[i].bbox
                xmin = transform[0] + xmin * transform[1]
                ymin = transform[3] + ymin * transform[5]
                xmax = transform[0] + xmax * transform[1]
                ymax = transform[3] + ymax * transform[5]
                
                csvfile.write("%s;%s;%s;%s;%s;%s\n"%(identifiant, area, xmin, ymin, xmax, ymax))
                i+=1
            except:
                IndexError
                print "Fin"
                break

#    cols_xmin = int((min(pointsX)-transform[0])/transform[1])
#    cols_xmax = int((max(pointsX)-transform[0])/transform[1])
#    cols_ymin = int((max(pointsY)-transform[3])/transform[5])
#    cols_ymax = int((min(pointsY)-transform[3])/transform[5])
    #trie les valeurs (nb pixels) et genere un tableau ensuite

    #trie = dic.items()
    #trie.sort(key=itemgetter(1),reverse=True)
    #arr = np.asarray(trie)
    
    #affiche la distribution croissante des valeurs
    #plt.bar(range(len(trie)), arr[:,1], align='center')
    #plt.show()
    
    sys.exit()
    
    #recupere les x plus grandes surfaces
    nbMax = int(arr.shape[0]*0.01)
    #clumpMax = arr[-nbMax:]
    clumpMax = arr[-10:]
    
    liste_id_entite = []
    #pour chaque identifiant, recupere son etendue sur le clump entier et
    #l'enregistre dans un raster
    for ID in np.nditer(clumpMax[:,0]):
        clump_id_binary = osof.otb_bandmath_ram([rasterFile], "im1b2==%s?1:0"%(ID), 2, 8, False, True, out+"/erase.tif")
        #ouverture du raster
        entite,xsize,ysize,projection,transform,raster_band = osof.raster_open(clump_id_binary, 1)
        #recupere l'index de l'entite
        index_entite = np.argwhere(entite == 1)
        #calcule la bbox
        entite_miny,entite_maxy,entite_minx,entite_maxx = osof.extent(index_entite, xsize, ysize)
        entite_ysize = entite_maxy - entite_miny
        entite_xsize = entite_maxx - entite_minx
        #reduit la taille de la matrice
        array = entite[entite_miny:entite_maxy, entite_minx:entite_maxx]
        #reenregistre le raster selon cette bbox
        osof.raster_save_zone(out+"/entite_%s.tif"%(ID), entite_xsize, entite_ysize, transform, array, projection, gdal.GDT_Byte, entite_minx, entite_miny)
        #ajoute dans une liste les identifiants des entites sauvegardee        
        liste_id_entite.append(ID)
        
    os.remove(out+"/erase.tif")    
    #diminution de la taille des rasters
    return arr, liste_id_entite

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regulararize a raster" \
        "and simplify the corresponding vector ")
        #parser.add_argument("-wd", dest="wd", action="store", \
                            #help="Working directory path", required = True)
                     
        parser.add_argument("-raster", dest="raster", action="store", \
                            help="raster of classif_clump_regularisee", required = True)
        
        parser.add_argument("-outcsv", dest="outcsv", action="store", \
                            help="raster of classif_clump_regularisee", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="raster of classif_clump_regularisee", required = True)
                            
        args = parser.parse_args()
        
        arr = ClumpSurface(args.raster, args.out, args.outcsv)

        #np.savetxt(args.outcsv, arr, fmt='%i', header="id, nbpixels", delimiter=",")
