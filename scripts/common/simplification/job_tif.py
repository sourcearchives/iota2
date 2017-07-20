# -*- coding: utf-8 -*-
"""
Create a raster according to an area (from tile in grid) to serialise simplification step.
"""

import sys
import os
import argparse
import time
from osgeo import gdal,ogr,osr
import csv
from osgeo.gdalconst import *
import numpy as np
import OSO_functions as osof
import shutil


def tilesClip(raster, xsize, ysize, xsize_tile, ysize_tile, cols_xmin, cols_ymin, NumIter, ngrid, inpath, outfile):

    XSizeClip = xsize_tile * (3 + (NumIter * 2))
    YSizeClip = ysize_tile * (3 + (NumIter * 2))
    
    Xstart = cols_xmin - (xsize_tile * (NumIter + 1)) -1 
    Ystart = cols_ymin - (ysize_tile * (NumIter + 1))
    
    print "Xstart", Xstart, "Ystart", Ystart
    print "XSizeClip",XSizeClip, "YSizeClip",YSizeClip
    
    if Xstart < 0 or cols_xmin < 0 :
        if Xstart + XSizeClip > xsize :
            nbcols = xsize
            Xstart = 0
        else :
            nbcols = XSizeClip + Xstart
            Xstart = 0
                    
    elif Xstart + XSizeClip > xsize :
        nbcols = XSizeClip - ((Xstart + XSizeClip) - xsize)
                    
    else :
        nbcols = XSizeClip
                    
    if Ystart < 0 or cols_ymin < 0 :
        if Ystart + YSizeClip > ysize :
            nbrows = ysize
            Ystart = 0
        else :
            nbrows = YSizeClip + Ystart
            Ystart = 0
                    
    elif Ystart + YSizeClip > ysize :
        nbrows = YSizeClip - ((Ystart + YSizeClip) - ysize)
                    
    else :
        nbrows = YSizeClip

    print "nbcols", nbcols,"nbrows", nbrows
                
    # extrait la zone dans laquelle rechercher l'etendue des entites de la tuile
    tif_raster_extract = inpath + "/" + str(ngrid) + "/" + outfile + "_%s.tif"%(NumIter)
    command = "gdal_translate -srcwin {} {} {} {} -ot UInt32 {} {}".format(Xstart, Ystart, nbcols, nbrows, raster, tif_raster_extract) 
    os.system(command)                     
    
    #shutil.copy(tif_raster_extract, outpath + "/" + str(ngrid) + "/" + outfile + "_%s.tif"%(NumIter))

    return Xstart, Ystart, nbrows, nbcols, tif_raster_extract


def manageEnvi(inpath, outpath, ngrid):

    # creation du repertoire de travail de la tuile
    if not os.path.exists(inpath+"/"+str(ngrid)):
        os.mkdir(inpath+"/"+str(ngrid))
    
    # creation du repertoire où enregistrer les donnees dans le working directory
    if not os.path.exists(inpath + "/" + str(ngrid) + "/outfiles"):
        os.mkdir(inpath + "/" + str(ngrid) + "/outfiles")
    
    # creation du repertoire où enregistrer les resultats dans le out path
    if not os.path.exists(outpath + "/" + str(ngrid)):        
        os.mkdir(outpath + "/" + str(ngrid))
    if not os.path.exists(outpath + "/" + str(ngrid) + "/outfiles"):           
            os.mkdir(outpath + "/" + str(ngrid) + "/outfiles")
    
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "w") as csvfile :
        csvfile.close()

def listTileEntities(tif_raster_extract, outpath, ngrid, feature):

    # ouvre le clump et la classification de la zone ayant ete decoupee
    datas_classif, xsize_classif, ysize_classif, projection_classif, transform_classif, raster_band_classif = osof.raster_open(tif_raster_extract, 1)
    datas_clump,xsize_clump,ysize_clump,projection_clump,transform_clump,raster_band_clump = osof.raster_open(tif_raster_extract, 2)
                        
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
                        
#------------------------------------------------------------------------------         
def serialisation_tif(inpath, raster, ram, grid, outfiles, tmp, cluster, outpath, ngrid):
    """
        
        in : 
            inpath : working directory with datas
            raster : name of raster
            ram : number of strips for otb
            grid : grid name for serialisation
            outfiles : name of output directory
            tmp : Keep temporary files ? True, False
            cluster : Do this step in command line ? True, False
            out : output path
            ngrid : tile number
            
        out :
            raster with normelized name (tile_ngrid.tif)
    """
    # Gestion des repertoires
    manageEnvi(inpath, outpath, ngrid)
        
    timer = osof.Timer()
    debut_tif_tile = time.time()   

    # ouverture de la classification regularise pour recuperer ses informations geographiques
    rasterfile = gdal.Open(raster, 0)
    transform = rasterfile.GetGeoTransform()
    xsize = rasterfile.RasterXSize
    ysize = rasterfile.RasterYSize
    rasterfile = None
    
    print "Xsize", xsize, "Ysize", ysize
    
    # ouvre le fichier grille dans le dossier parent
    grid_open = osof.shape_open(grid,0)
    grid_layer = grid_open.GetLayer()
        
    # pour chaque tuile    
    for feature in grid_layer :
        
        #recupere son id
        i = int(feature.GetField("FID"))
        
        #si l'id correspond au numero de grille recherche
        if int(i) == int(ngrid) :
            print "-------------------------------------------------------\n\nTuile",\
            int(feature.GetField("FID"))
            
            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write(("Tuile %s \n"%(ngrid)))
                csvfile.close()
                
            # calcule l'emprise de la cellule de la grille par rapport au raster entier
            cols_xmin, cols_xmax, cols_ymin, cols_ymax = osof.coords_cell(feature, transform)
            
            # taille d'une tuile en X et Y            
            xsize_tile = cols_xmax - cols_xmin
            ysize_tile = cols_ymax - cols_ymin
            
            print "Xsize tuile",xsize_tile,"Ysize tuile",ysize_tile
            
            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write(("Xsize de la tuile : %s; Ysize de la tuile : %s \n"%(xsize_tile,ysize_tile)))
                csvfile.close()
            
            # variables permettant d'incrementer le nombre de tuiles a selectionner
            NumIter = 0
        
            #variable permettant d'incrementer l'etape de selection des entites de la tuile
            entities_tile_extent = True
        
            #tant que l'on ne parvient pas a selectionner toutes les entites de la tuile (agrandir zone)
            while entities_tile_extent :
                
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write(("\nITERATION %s \n"%(NumIter+1)))
                    csvfile.close()
                    
                print "Calcul de la zone de recherche des entites de la tuile"
                
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Calcul de la zone de recherche des entites de la tuile \n")
                    csvfile.close()
                
                time_zone_recherche = time.time()
                
                # Calcul de l'origine et de la taille de la zone raster a decouper
                Xstart, Ystart, nbrows, nbcols, tif_raster_extract = tilesClip(raster, xsize, ysize, xsize_tile, ysize_tile, \
                                                                               cols_xmin, cols_ymin, NumIter, ngrid, inpath, \
                                                                               "raster_extract")
                
                if tmp :
                    shutil.copy(inpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(NumIter), \
                                outpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(NumIter))
                                
                # ouverture de la zone decoupee pour calculer ses coordonnees
                rasterExtract = gdal.Open(tif_raster_extract, 0)
                transformExtract = rasterExtract.GetGeoTransform()
                xsizeExtract = rasterExtract.RasterXSize
                ysizeExtract = rasterExtract.RasterYSize
                rasterExtract = None
                
                #affiche les coordonnees du raster contenant l'etendue des entites de la tuile
                print "Coordonnees geographiques du raster : ulx :%s, uly :%s , lrx :%s, lry :%s"%(transformExtract[0], \
                                                                                                       transformExtract[3], \
                                                                                                       transformExtract[0] + \
                                                                                                       xsizeExtract * transformExtract[1],\
                                                                                                       transformExtract[3] + \
                                                                                                       ysizeExtract * transformExtract[5])
                
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Coordonnees geographiques du raster : ulx :%s, uly :%s, lrx :%s, lry :%s \n"%(transformExtract[0], \
                                                                                                                       transformExtract[3], \
                                                                                                                       transformExtract[0] + \
                                                                                                                       xsizeExtract * transformExtract[1],\
                                                                                                                       transformExtract[3] + \
                                                                                                                       ysizeExtract * transformExtract[5]))
                    csvfile.close()
                        
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write(("nbrows : %s, nbcols : %s \n"%(nbrows, nbcols)))
                    csvfile.close()
        
                # met en ram le raster bi-bande dans 2 variables differentes puis, dans une seule
                memory_tif_raster_extract_1 = osof.otb_MiseEnRam([tif_raster_extract], "im1b1", 8)
                memory_tif_raster_extract_2 = osof.otb_MiseEnRam([tif_raster_extract], "im1b2", 32)
                memory_tif_raster_extract = osof.otb_MiseEnRamConcatenate([memory_tif_raster_extract_1, memory_tif_raster_extract_2],32)     
                
                fin_time_zone_recherche = time.time() - time_zone_recherche
                
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes \n"%(round(fin_time_zone_recherche,2)))
                    csvfile.close()
                    
                # si premiere iteration
                if NumIter == 0 :
                    time_gen_liste = time.time()

                    ############Identification des entites de la tuile############
                    print "Genere la liste des entites de la tuile %s \n"%(i)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Genere la liste des entites de la tuile %s \n"%(i))
                        csvfile.close()
                        
                    tile_id = listTileEntities(tif_raster_extract, outpath, ngrid, feature)
                    
                    fin_time_gen_liste = time.time() - time_gen_liste
                    print "TEMPS : %s secondes \n"%(round(fin_time_gen_liste,2))
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(fin_time_gen_liste,2)))
                        csvfile.close()
                        
                # si la liste de la tuile ne contient pas d'identifiants
                if len(tile_id) == 0 :          
                    entities_tile_extent = False
                    print "Aucune entite dans la tuile.Fin"
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Aucune entite dans la tuile.Fin")
                        csvfile.close()
                        
                    sys.exit()
                
                # s'il y a des entites dans la tuile
                else : 
                    # compte le nombre d'entites
                    nb_features_tile = len(tile_id)
                    
                    # si premiere selection
                    if NumIter == 0 :
                        print "Nombre d'entites dans la tuile %s :"%(i), nb_features_tile
                        
                        with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                            csvfile.write("Nombre d'entites dans la tuile %s : %s \n"%(i,nb_features_tile))
                            csvfile.close()
                        
                        timer.start()
                        
                        print "Generation de la condition de selection des entites de la tuile %s \n"%(i)
                        
                        with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                            csvfile.write("Generation de la condition de selection des entites de la tuile %s \n"%(i))
                            csvfile.close()
                            
                        # genere la liste de conditions pour l'executer sur la bande 2 du raster bi-bande (clump)
                        conditions_tile = osof.genere_liste_conditions(tile_id,2)
                    
                        timer.stop()
                        time_condition_tile = timer.interval
                        
                        print "TEMPS : %s secondes \n"%(round(time_condition_tile,2))
                        
                        with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                            csvfile.write("TEMPS : %s secondes \n"%(round(time_condition_tile,2)))
                            csvfile.close()
                            
                    timer.start()      
                    
                                            
                    print "Calcul de l'emprise des entites de la tuile %s \n"%(i)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Calcul de l'emprise des entites de la tuile %s \n"%(i))
                        csvfile.close()
                            
                    #si premiere selection
                    if NumIter == 0 :
                            
                        #rajoute un test a la condition permettant de selectionner l'etendue des entites de la tuile
                        conditions_id_tile = conditions_tile + "?1:0"

                        #genere un raster binaire pour identifier l'etendue des entites de la tuile
                        clump_id_bin = osof.otb_bandmath_ram([memory_tif_raster_extract], conditions_id_tile, ram, 8, True, True, \
                                                             inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter))
                        
                        if tmp :
                            shutil.copy(inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter), \
                                        outpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter))
                        
                        memory_clump_id_bin = osof.otb_MiseEnRam([clump_id_bin], "im1b1", 8)
                    
                    #sinon, puisque la premiere zone n'a pas suffit a selectionner l'etendue totale des entites de la tuile 
                    else :

                        ############ Recherche des entites de la couronne de tuiles ############
                    
                        #redimensionne le raster de la boucle precedente avec le raster actuel pour qu'ils fassent la meme dimension
                        memory_init_mask_tile = osof.otb_Superimpose(tif_raster_extract, \
                                                                     inpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(NumIter-1), \
                                                                     ram, 8)

                        memory_mask_tile = osof.otb_bandmath_ram([memory_init_mask_tile], "im1b1==2?0:im1b1", ram, 8, True, False)
                        
                        #redimensionne le raster binaire de la boucle precedente avec le raster actuel pour qu'ils fassent la meme dimension
                        memory_clump_id_bin = osof.otb_Superimpose(tif_raster_extract, \
                                                                   inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter - 1), \
                                                                   ram, 8)
                        memory_clump_id_bin_extend = osof.otb_bandmath_ram([memory_clump_id_bin], "im1b1==2?0:im1b1", ram, 8, True, False)
                        
                        #rajoute le resultat du test de la liste de condition + utilise un masque pour ne pas effectuer
                        #la recherche de l'emprise dans la zone deja connue
                        conditions_id_tile = "((im2b1==0) && "+ conditions_tile + ")?1:0"
                        memory_clump_id_bin_temp = osof.otb_bandmath_ram([memory_tif_raster_extract, memory_mask_tile], \
                                                                         conditions_id_tile, ram, 8, True, False)                      
                        
                        #fusion du nouveau clump_id_bin avec l'ancien
                        clump_id_bin = osof.otb_bandmath_ram([memory_clump_id_bin_temp, memory_clump_id_bin_extend], \
                                                             "((im1b1==1)||(im2b1==1))?1:0",ram, 8, True, True, \
                                                             inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter))
                        
                        if tmp :
                            shutil.copy(inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter), \
                                        outpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(NumIter))
                        
                        memory_clump_id_bin = osof.otb_MiseEnRam([clump_id_bin], "im1b1", 8)
                        
                    timer.stop()
                    time_extent_tile = timer.interval
                    print "TEMPS : %s secondes \n"%(round(time_extent_tile,2))
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(time_extent_tile,2)))
                        csvfile.close()
                    
                    print "Test de l'etendue des entites de la tuile %s \n"%(i)
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Test de l'etendue des entites de la tuile %s \n"%(i))
                        csvfile.close()
                    
                    ##ouvre l'image correspondant a l'emprise des entites de la tuile
                    datas_clump_id_bin, xsize_clump_id_bin, ysize_clump_id_bin, \
                        projection_clump_id_bin, transform_clump_id_bin, raster_band_clump_id_bin = osof.raster_open(clump_id_bin, 1)
                    
                    
                        
                    ##recupere l'index des pixels ayant pour valeur 1, cad les entites de la tuile
                    index_clump_id_bin = np.argwhere(datas_clump_id_bin == 1)
                    
                    ##determine l'etendu de la zone correspondant aux entites de la tuile
                    id_bin_miny,id_bin_maxy,id_bin_minx,id_bin_maxx = osof.extent(index_clump_id_bin, \
                                                                                  xsize_clump_id_bin, \
                                                                                  ysize_clump_id_bin)

                    if ((id_bin_minx == 0) and (transform_clump_id_bin[0] != transform[0])) \
                        or ((id_bin_miny == 0) and (transform_clump_id_bin[3] != transform[3])) \
                        or ((id_bin_maxx == xsize_clump_id_bin) and ((transform_clump_id_bin[0] + xsize_clump_id_bin * \
                                                                      transform_clump_id_bin[1]) != (transform[0]+xsize*transform[1]))) \
                        or ((id_bin_maxy == ysize_clump_id_bin) and ((transform_clump_id_bin[3] + ysize_clump_id_bin * \
                                                                      transform_clump_id_bin[5]) != (transform[3]+ysize*transform[5]))):                                       
                            
                            print "L'emprise des entites est en bordure du raster, augmentation de la zone de recherche \n"
                            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                                csvfile.write("L'emprise des entites est en bordure du raster, augmentation de la zone de recherche \n")
                                csvfile.close()
                                
                            NumIter += 1
                        
                    else :
                        print "\n######## Phase 2, selection des voisins ######## \n"
                        
                        with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                            csvfile.write("\n ######## Phase 2, selection de la couronne ######## \n")
                            csvfile.close()
                        
                        entities_tile_extent = False
                        
                    ###########################################################
            
            #initialise des varables de temps et autre pour les incrementer
            time_extent_max_tile = 0
            time_select_id_neighbors = 0
            nb_features_neighbors = 0
            time_extent_neighbors = 0           
            ysize_couronne = 0
            xsize_couronne = 0
            search_emprise_voisins = True
            NumIterVoisin = 1
            NumIterEntite = NumIter
            
            #tant que l'etendue des voisins n'est pas identifiee totalement
            while search_emprise_voisins :
                
                print "\nITERATION VOISIN %s"%(NumIterVoisin)
                                    
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("\nITERATION VOISIN %s\n"%(NumIterVoisin))
                    csvfile.close()
                    
                if NumIterEntite < NumIter :  

                        
                    print "Calcul de la zone de recherche des voisins"
                
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Calcul de la zone de recherche des voisins \n")
                        csvfile.close()
                    
                    timer.start()
                        
                    Xstart, Ystart, nbrows, nbcols, tif_raster_extract_voisin = tilesClip(raster, \
                                                                                          xsize, \
                                                                                          ysize, \
                                                                                          xsize_tile, \
                                                                                          ysize_tile, \
                                                                                          cols_xmin, \
                                                                                          cols_ymin, \
                                                                                          NumIter, \
                                                                                          ngrid, \
                                                                                          inpath, \
                                                                                          "raster_extract_voisin")
                                                                                          
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/raster_extract_voisin_%s.tif"%(NumIter), \
                                    outpath + "/" + str(ngrid) + "/raster_extract_voisin_%s.tif"%(NumIter))
                                
                    # ouverture de la zone decoupee pour calculer ses coordonnees
                    rasterExtract = gdal.Open(tif_raster_extract_voisin, 0)
                    transformExtract = rasterExtract.GetGeoTransform()
                    xsizeExtract = rasterExtract.RasterXSize
                    ysizeExtract = rasterExtract.RasterYSize
                    rasterExtract = None
                    
                    #affiche les coordonnees du raster contenant l'etendue des entites de la tuile
                    print "Coordonnees geographiques du raster : ulx :%s, uly :%s , lrx :%s, lry :%s"%(transformExtract[0], \
                                                                                                           transformExtract[3], \
                                                                                                           transformExtract[0] + \
                                                                                                           xsizeExtract * transformExtract[1],\
                                                                                                           transformExtract[3] + \
                                                                                                           ysizeExtract * transformExtract[5])
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Coordonnees geographiques du raster : ulx :%s, uly :%s, lrx :%s, lry :%s \n"%(transformExtract[0], \
                                                                                                                           transformExtract[3], \
                                                                                                                           transformExtract[0] + \
                                                                                                                           xsizeExtract * transformExtract[1],\
                                                                                                                           transformExtract[3] + \
                                                                                                                           ysizeExtract * transformExtract[5]))
                        
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write(("nbrows : %s, nbcols : %s \n"%(nbrows, nbcols)))
                        csvfile.close()
                    
                    # met en ram le raster bi-bande dans 2 variables differentes puis, dans une seule
                    memory_tif_raster_extract_voisin_1 = osof.otb_MiseEnRam([tif_raster_extract_voisin], "im1b1", 8)
                    memory_tif_raster_extract_voisin_2 = osof.otb_MiseEnRam([tif_raster_extract_voisin], "im1b2", 32)
                    memory_tif_raster_extract_voisin = osof.otb_MiseEnRamConcatenate([memory_tif_raster_extract_voisin_1, \
                                                                                      memory_tif_raster_extract_voisin_2],32)     
                     
                    # mise a l'echelle du clump_id_bin pour l'utiliser selon la zone de recherche des voisins
                    memory_clump_id_bin_voisin = osof.otb_Superimpose(memory_tif_raster_extract_voisin, \
                                                                      memory_clump_id_bin, ram, 8, True)
                    clump_id_bin_extend_voisin = osof.otb_bandmath_ram([memory_clump_id_bin_voisin], \
                                                                       "im1b1==2?0:im1b1", ram, 8, True, True, \
                                                                       inpath + "/" + str(ngrid) + "/clump_id_bin_extend_voisin.tif")               
                    timer.stop()
                    time_extent_max_tile = timer.interval

                    print "TEMPS : %s secondes \n"%(time_extent_max_tile)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(time_extent_max_tile,2)))
                        csvfile.close()
                
                #si la zone de recherche des voisins n'a pas encore ete augmentee
                if NumIterEntite == NumIter :
                    
                    timer.start() 
                    
                    print "Genere la liste des identifiants des voisins de la tuile %s \n"%(i)
                
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Genere la liste des identifiants des voisins de la tuile %s \n"%(i))
                        csvfile.close()
                    
                    #fait une dilution d'un pixel du clump_id_bin
                    memory_clump_id_dilate = osof.otb_dilate(memory_clump_id_bin,ram,8, True, False)
                    
                    #recupere uniquement la partie qui a changee, c'est a dire la frontiere
                    clump_id_boundaries = osof.otb_bandmath_ram([memory_clump_id_bin, \
                                                                 memory_clump_id_dilate],\
                                                                "(im1b1==0 && im2b1==1)?1:0", \
                                                                ram, 8, True, True, \
                                                                inpath + "/" + str(ngrid) + "/clump_id_boundaries.tif")
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/clump_id_boundaries.tif", \
                                    outpath + "/" + str(ngrid) + "/clump_id_boundaries.tif")
                    
                    #ouvre les rasters boundaries, classif de la zone et clump de la zone pour generer la liste des voisins
                    boundaries, xsize_boundaries, ysize_boundaries, \
                        projection_boundaries, transform_boundaries, raster_band_boundaries = osof.raster_open(clump_id_boundaries,1)
                    datas_classif_voisin, xsize_classif_voisin, ysize_classif_voisin, \
                        projection_classif_voisin, transform_classif_voisin, \
                        raster_classif_voisin = osof.raster_open(inpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(NumIter),1)
                    datas_clump_voisin, xsize_clump_voisin, ysize_clump_voisin, \
                        projection_clump_voisin, transform_clump_voisin, \
                        raster_clump_voisin = osof.raster_open(inpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(NumIter),2)
                    
                    #parcours chaque pixel de la frontiere pour connaitre l'id du voisin
                    liste_id_couronne = np.unique(np.where(((datas_classif_voisin > 1) & \
                                                            (datas_classif_voisin < 250) & \
                                                            (boundaries == 1)),datas_clump_voisin,0)).tolist()

                    liste_id_couronne = [x for x in liste_id_couronne if x != 0] 
                    
                    timer.stop()
                    print "TEMPS : %s secondes \n"%(timer.interval)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
                        csvfile.close()     
                    
                    nb_features_neighbors += len(liste_id_couronne)              
             
                    print "Nombre de voisins de la tuile %s : %s \n"%(i, nb_features_neighbors)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Nombre de voisins de la tuile %s : %s \n"%(i, nb_features_neighbors))
                        csvfile.close()
                    
                #test la presence de la mer pour savoir si l'on ajoute les entite de la tuile + ceux de la couronne a la liste
                if len(liste_id_couronne) != 0 :
                    if NumIterEntite == NumIter :
                        if np.any((boundaries == 1) & (datas_classif_voisin == 255)):
                            liste_id_couronne = liste_id_couronne + tile_id
                        elif len(liste_id_couronne) != 0 :
                            liste_id_couronne = liste_id_couronne                       
                    
                    print "Calcul de l'emprise des voisins de la tuile %s \n"%(i)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Calcul de l'emprise des voisins de la tuile %s \n"%(i))
                        csvfile.close()
                        
                    timer.start()
                    
                    #selon la liste des conditions, identifie l'emprise des voisins
                    if NumIterEntite == NumIter :
                        conditions_id_couronne = osof.genere_liste_conditions(liste_id_couronne,2)        
                        conditions_id_couronne = conditions_id_couronne + "?0:1"
                        couronne = osof.otb_bandmath_ram([memory_tif_raster_extract], \
                                                         conditions_id_couronne, \
                                                         ram, 8, True, True, \
                                                         inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter))
                        if tmp :
                            shutil.copy(inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter), \
                                        outpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter))

                        memory_couronne = osof.otb_MiseEnRam([couronne], "im1b1", 8)
                        
                    else :
                        
                        #changement taille raster couronne precedent pour le fusion par la suite
                        memory_couronne_temp = osof.otb_Superimpose(tif_raster_extract_voisin, \
                                                                    inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter-1), \
                                                                    ram, 8)
                        memory_couronne_extend = osof.otb_bandmath_ram([memory_couronne_temp], \
                                                                       "im1b1==2?3:im1b1", ram, 8, True, False)
                        
                        #selon la liste des conditions et d'un raster masque, identifie l'emprise des voisins dans la nouvelle zone
                        conditions_id_couronne = osof.genere_liste_conditions(liste_id_couronne,2)
                        conditions_id_couronne = "(im2b1==3 &&(" + conditions_id_couronne + "))?0:1"                  
                        memory_couronne_new_extent = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin, \
                                                                            memory_couronne_extend], \
                                                                           conditions_id_couronne, ram, 8, True, False)
                        
                        #fusion de la nouvelle couronne avec l'ancienne
                        couronne = osof.otb_bandmath_ram([memory_couronne_extend, \
                                                          memory_couronne_new_extent], \
                                                         "((im1b1==0)||(im2b1==0))?0:1",\
                                                         ram, 8, True, True, \
                                                         inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter))
                        if tmp :
                            shutil.copy(inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter), \
                                        outpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter))
                        
                        memory_couronne = osof.otb_MiseEnRam([couronne], "im1b1", 8)
                        
                    #ouvre le fichier couronne pour recuperer l'etendue des pixels correspondants aux voisins
                    datas_couronne, xsize_couronne, ysize_couronne, \
                        projection_couronne, transform_couronne, raster_band_couronne = osof.raster_open(couronne,1)
                        
                    #genere l'index des entites    
                    index_couronne = np.argwhere(datas_couronne == 0)
                    
                    timer.stop()
                    time_extent_neighbors = timer.interval
                    print "TEMPS : %s secondes \n"%(time_extent_neighbors)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(time_extent_neighbors,2)))
                        csvfile.close()
                
                elif len(liste_id_couronne) == 0 :
                    #s'il n'y a pas de voisins
                    print "Aucun voisins, utilisation de l'etendue des entites de la tuile %s \n"%(i)
                    
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("Aucun voisins, utilisation de l'etendue des entites de la tuile %s \n"%(i))
                        csvfile.close()
                    
                    if NumIterEntite == NumIter :
                        #utilise comme couronne de raster des entites de la tuile, s'il n'y a pas eu d'augmentation de zone
                        datas_couronne, xsize_couronne, ysize_couronne, \
                            projection_couronne, transform_couronne, raster_band_couronne = osof.raster_open(clump_id_bin,1)
                    else :
                        #utilise comme couronne de raster des entites de la tuile etendue, s'il y a eu une augmentation de zone
                        datas_couronne, xsize_couronne, ysize_couronne, \
                            projection_couronne, transform_couronne, raster_band_couronne = osof.raster_open(clump_id_bin_extend_voisin,1)
                    
                    #genere l'index des entites (1 dans ce clump_id_bin)   
                    index_couronne = np.argwhere(datas_couronne == 1)
                
                print "Test de l'etendue des voisins de la tuile %s \n"%(i)
                
                with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Test de l'etendue des voisins de la tuile %s \n"%(i))
                    csvfile.close()
                        
                ##determine l'etendu des entites de la couronne
                id_couronne_miny, id_couronne_maxy, \
                    id_couronne_minx, id_couronne_maxx = osof.extent(index_couronne, xsize_couronne, ysize_couronne)
                        
                if ((id_couronne_minx == 0) and (transform_couronne[0] != transform[0])) \
                    or ((id_couronne_miny == 0) and (transform_couronne[3] != transform[3])) \
                    or ((id_couronne_maxx == xsize_couronne) and ((transform_couronne[0] + xsize_couronne * transform_couronne[1])\
                                                                  != (transform[0] + xsize * transform[1]))) \
                    or ((id_couronne_maxy == ysize_couronne) and ((transform_couronne[3] + ysize_couronne * transform_couronne[5])\
                                                                  != (transform[3]+ysize*transform[5]))):                                       
                        print "L'emprise des voisins est en bordure du raster, augmentation de la zone de recherche \n"
                        with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                            csvfile.write("L'emprise des voisins est en bordure du raster, augmentation de la zone de recherche \n")
                            csvfile.close()

                        NumIter += 1
                        NumIterVoisin += 1
                    
                else :
                    print "\n ######## Phase 3, export du raster ######## \n"
                        
                    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                        csvfile.write("\n ######## Phase 3, export du raster ######## \n")
                        csvfile.close()

                    search_emprise_voisins = False
                    
            print "Generation du raster distinguant les entites de la tuile et leurs voisins \n"
            
            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Generation du raster distinguant les entites de la tuile et leurs voisins \n")
                csvfile.close()
                        
            timer.start() 
            
            #change la condition des identifiants de la tuile pour distinguer les pixels de classif et de clump
            conditions_id_extract = conditions_tile + "?im1b1:im1b2"                              
            
            #si le fichier couronne existe
            if os.path.exists(inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(NumIter)) :
                if NumIterEntite < NumIter :
                    #Genere un fichier tif avec des valeurs de classe et des identifiants
                    memory_intermediaire_tile = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin], \
                                                                      conditions_id_extract, ram, 32, True, False)
                    #assigne la valeur de 0 aux entites qui ne sont pas entite de la tuile et pas entite voisines
                    out = osof.otb_bandmath_ram([memory_intermediaire_tile, memory_couronne], \
                                                "(im2b1 == 1 && im1b1 > 255)?0:im1b1", \
                                                ram, 32, True, True, \
                                                inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i))
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i), \
                                    outpath + "/" + str(ngrid) + "/tile_with_0_%s.tif"%(i))
                    
                else :
                    #Genere un fichier tif avec des valeurs de classe et des identifiants
                    memory_intermediaire_tile = osof.otb_bandmath_ram([memory_tif_raster_extract], \
                                                                      conditions_id_extract, \
                                                                      ram, 32, True, False)

                    #assigne la valeur de 0 aux entites qui ne sont pas entite de la tuile et pas entite voisines
                    out = osof.otb_bandmath_ram([memory_intermediaire_tile, memory_couronne], \
                                                "(im2b1 == 1 && im1b1 > 255)?0:im1b1", \
                                                ram, 32, True, True, \
                                                inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i))
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i), \
                                    outpath + "/" + str(ngrid) + "/tile_with_0_%s.tif"%(i))
            
            #n'ayant pas de voisins
            else :
                if NumIterEntite < NumIter :
                    #Genere un fichier tif avec des valeurs de classe et des identifiants
                    out = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin], \
                                                conditions_id_extract, \
                                                ram, 32, True, True, \
                                                inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i))
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i), \
                                    outpath + "/" + str(ngrid) + "/tile_with_0_%s.tif"%(i))
                else :
                    #Genere un fichier tif avec des valeurs de classe et des identifiants
                    out = osof.otb_bandmath_ram([memory_tif_raster_extract], \
                                                conditions_id_extract, \
                                                ram, 32, True, True, \
                                                inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i))
                    if tmp :
                        shutil.copy(inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i), \
                                    outpath + "/" + str(ngrid) + "/tile_with_0_%s.tif"%(i))
         
            print "Changement des valeurs 0 en nodata \n"
            
            #change les valeurs 0 en nodata pour ne pas les vectoriser lors de l'etape de simplification
            command = "gdal_translate -a_nodata 0 %s/tile_%s.tif %s/tile_%s_ndata.tif"%(inpath + "/" + str(ngrid) + "/outfiles",\
                                                                                        i,\
                                                                                        inpath + "/" + str(ngrid) + "/outfiles",i) 
            os.system(command)
            os.remove(inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i))
            os.rename("%s/tile_%s_ndata.tif"%(inpath + "/" + str(ngrid) + "/outfiles",i),\
                      "%s/tile_%s.tif"%(inpath + "/" + str(ngrid) + "/outfiles",i))
            
            timer.stop()
            print "TEMPS : %s secondes \n"%(round(timer.interval,2))    
            
            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
                csvfile.close()    
                
            time_tif_tile = time.time() - debut_tif_tile
            print "Temps de traitement total de la tuile %s : %s secondes \n"%(i, round(time_tif_tile,2))
            
            with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Temps de traitement total de la tuile %s : %s secondes \n"%(i, round(time_tif_tile,2)))
                csvfile.close()   
                
        else :                    
          continue

    for iteration in range(NumIter+1):
        try:
            os.remove(inpath + "/" + str(ngrid) + "/clump_id_bin_%s.tif"%(iteration))
        except:
            pass
        try:
            os.remove(inpath + "/" + str(ngrid) + "/raster_extract_%s.tif"%(iteration))
        except:
            pass
        try:
            os.remove(inpath + "/" + str(ngrid) + "/raster_extract_voisin_%s.tif"%(iteration))
        except:
            pass
        try:
            os.remove(inpath + "/" + str(ngrid) + "/couronne_%s.tif"%(iteration))
        except:
            pass
        
    try:
        os.remove(inpath + "/" + str(ngrid) + "/clump_id_boundaries.tif")
    except:
        pass
    try:
        os.remove(inpath + "/" + str(ngrid) + "/clump_id_bin_extend_voisin.tif")
    except:
        pass
    
    if str(cluster) == "False" :
        if os.path.exists(inpath +"/" + str(ngrid) + "/outfiles/tile_%s.tif"%(ngrid)): 
            shutil.copy(inpath +"/"+str(ngrid)+"/outfiles/tile_%s.tif"%(ngrid), \
                        outpath + "/"+str(ngrid)+"/outfiles/tile_%s.tif"%(ngrid))
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
                            
        parser.add_argument("-ngrid", dest="ngrid", action="store", \
                            help="ngrid value", required = True)     
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="outname directory", required = True)   
                            
        parser.add_argument("-tmp", action="store_true", \
                            help="keep temporary files ?", default = False) 
                            
        parser.add_argument("-cluster", action="store_true", \
                            help="If True, don't pool simplification phase", default = False) 
                                
    args = parser.parse_args()
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
    
    serialisation_tif(args.path, args.classif, args.ram, args.grid, "outfiles", args.tmp, args.cluster, args.out, args.ngrid)
     
    if os.path.exists(args.path + "/" + str(args.ngrid) + "/outfiles" + "/tile_%s.tif"%(args.ngrid)): 
        shutil.copy(args.path + "/" + str(args.ngrid) + "/outfiles" + "/tile_%s.tif"%(args.ngrid), \
                    args.out + "/"+ str(args.ngrid) + "/outfiles" +"/tile_%s.tif"%(args.ngrid))
