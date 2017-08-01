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
from skimage.measure import regionprops
import shutil

#------------------------------------------------------------------------------         
def serialisation_tif(inpath, raster, ram, grid, outfiles, tmp, cluster, out, ngrid):
    """
        
        in : 
            path : working directory with datas
            raster : name of raster
            ram : number of strippe for otb
            grid : grid name for serialisation
            outfiles : name of output directory
            tmp : Keep tomprary files ? True, False
            cluster : Do this step in command line ? True, False
            ngrid : tile number
            
        out :
            raster with nomelized name (tile_ngrid.tif)
    """
    #creation du repertoire de travail de la tuile
    if not os.path.exists(inpath+"/"+str(ngrid)):
        os.mkdir(inpath+"/"+str(ngrid))
    
    #cree repertoire où enregistrer les donnees dans le wd
    if not os.path.exists(inpath + "/" + str(ngrid) + "/outfiles"):
        os.mkdir(inpath + "/" + str(ngrid) + "/outfiles")
    
    #cree repertoire où enregistrer les resultats
    if not os.path.exists(out + "/" + str(ngrid)):        
        os.mkdir(out + "/" + str(ngrid))
    if not os.path.exists(out + "/" + str(ngrid) + "/outfiles"):           
            os.mkdir(out + "/" + str(ngrid) + "/outfiles")
        
    #se place dans le dossier de la tuile
    os.chdir(inpath+"/"+str(ngrid))
    
    timer = osof.Timer()
    debut_tif_tile = time.time()   

    #ouverture de la classification regularise pour recuperer ses informations geographiques
    datas,xsize,ysize,projection,transform,raster_band = osof.raster_open(raster, 1)
    del datas
    
    #ouvre le fichier grille dans le dossier parent
    grid_open = osof.shape_open(grid,0)
    grid_layer = grid_open.GetLayer()
        
    #pour chaque cellule    
    for feature in grid_layer :
            
        i = int(feature.GetField("FID"))
        
        if int(i) == int(ngrid):
            print "-------------------------------------------------------\n\nTuile",\
            int(feature.GetField("FID"))
            
            #emprise de la cellule de la grille par rapport au raster entier
            cols_xmin, cols_xmax, cols_ymin, cols_ymax = osof.coords_cell(feature, transform)

            #ouverture des rasters classif et clump
            datas_classif,xsize_classif,ysize_classif,projection_classif,transform_classif,raster_band_classif = osof.raster_open(raster, 1)
            datas_clump,xsize_clump,ysize_clump,projection_clump,transform_clump,raster_band_clump = osof.raster_open(raster, 2)
            
            #calcul un ensemble d'informations pour le clump                    
            PropsClump = regionprops(datas_clump)
        
            #extrait un sous tableau de la tuile afin de selectionner les identifiants et classes
            tile_classif = datas_classif[cols_ymin:cols_ymax, cols_xmin:cols_xmax]                
            tile_id_all = datas_clump[cols_ymin:cols_ymax, cols_xmin:cols_xmax]
            
            #supprime des variables
            del datas_classif, datas_clump
            
            #genere la liste des indentifiants
            tile_id = np.unique(np.where(((tile_classif > 1) & (tile_classif < 250)), tile_id_all, 0)).tolist()
            
            #nettoie la liste
            tile_id = [x for x in tile_id if x != 0]

            #initialise un tableau numpy pour stocker les proprietes
            #des entites de la tuile
            PropsTab = np.zeros([len(tile_id), 6])
            row = 0
            
            #pour chacune des entites, recupere des proprietes
            for IdEntite in tile_id:
                PropsTab[row,0] = PropsClump[IdEntite-301].label
                PropsTab[row,1] = PropsClump[IdEntite-301].area
                #xmin, ymin, xmax, ymax = PropsClump[IdEntite-301].bbox
                PropsTab[row,2], PropsTab[row,3], PropsTab[row,4], PropsTab[row,5] = PropsClump[IdEntite-301].bbox
                
                #coords geographiques des bbox des clumps
                #xmin = transform[0] + xmin * transform[1]
                #ymin = transform[3] + ymin * transform[5]
                #xmax = transform[0] + xmax * transform[1]
                #ymax = transform[3] + ymax * transform[5]

                row+=1

                #si la cellule ne contient pas d'identifiants, c'est probablement
                #une cellule composee uniquement de nodata, donc on passe
                if len(tile_id) == 0 :          
                    entities_tile_extent = False
                    print "Aucune entite dans la tuile."
                    sys.exit()
                    
                else : 
                    nb_features_tile = len(tile_id)
                    
                    #si c'est la premiere recherche de l'etendue des entites de la tuile
                    if NumIter == 0 :
                        print "Nombre d'entites dans la tuile %s :"%(i), nb_features_tile
                        timer.start()
                    
                        #genere la liste de conditions pour l'executer sur la bande 2 d'un raster
                        conditions_tile = osof.genere_liste_conditions(tile_id,2)
                        
                        #genere la liste de conditions pour l'executer sur la bande 1 d'un raster
                        #conditions_tile1 = osof.genere_liste_conditions(tile_id,1)
                    
                        timer.stop()
                        time_condition_tile = timer.interval
                        print "Fin de la sélection des identifiants de la tuile %s"%(i), time_condition_tile,"\n"
                    
                    print "Début de la lecture des identifiants de la tuile %s"%(i)
                    timer.start()      
                    
                    #si c'est la premiere recherche de l'etendue des entites de la tuile
                    if NumIter == 0 :
                        #rajoute le resultat du test de la liste de condition
                        conditions_id_tile = conditions_tile + "?1:0"
                        #genere le masque de l'emprise des entites de la tuile sur l'ensemble du raster
                        clump_id_bin = osof.otb_bandmath_ram([memory_tif_raster_extract], conditions_id_tile, ram, 8, True, True, "clump_id_bin_%s.tif"%(NumIter))
                        memory_clump_id_bin = osof.otb_MiseEnRam([clump_id_bin], "im1b1", 8)
                    else :
                        #augmente l'etendue de la classification precedente et en fait un masque ou le nodata = 1
                        memory_init_mask_tile = osof.otb_Superimpose(tif_raster_extract, "raster_extract_%s.tif"%(NumIter-2), ram, 8)
                        memory_mask_tile = osof.otb_bandmath_ram([memory_init_mask_tile], "im1b1==2?0:im1b1", ram, 8, True, False)
                        
                        #augmente l'etendue du resulat precedent
                        memory_clump_id_bin = osof.otb_Superimpose(tif_raster_extract, "clump_id_bin_%s.tif"%(NumIter-2),  ram, 8)
                        memory_clump_id_bin_extend = osof.otb_bandmath_ram([memory_clump_id_bin], "im1b1==2?0:im1b1", ram, 8, True, False)
                        
                        #rajoute le resultat du test de la liste de condition + utilise un masque pour ne pas effectuer
                        #la recherche de l'emprise dans la zone deja connue
                        conditions_id_tile = "((im2b1==0) && "+ conditions_tile + ")?1:0"
                        memory_clump_id_bin_temp = osof.otb_bandmath_ram([memory_tif_raster_extract, memory_mask_tile], conditions_id_tile, ram, 8, True, False)                      
                        
                        #fusion du nouveau clump_id_bin avec l'ancien
                        clump_id_bin = osof.otb_bandmath_ram([memory_clump_id_bin_temp, memory_clump_id_bin_extend], "((im1b1==1)||(im2b1==1))?1:0",ram, 8, True, True, "clump_id_bin_%s.tif"%(NumIter))
                        memory_clump_id_bin = osof.otb_MiseEnRam([clump_id_bin], "im1b1", 8)
                        
                    timer.stop()
                    time_extent_tile = timer.interval
                    print "Fin de la lecture des identifiants de la tuile %s"%(i), time_extent_tile,"\n"
                    
                    #teste si l'emprise des entites de la tuile correspond au X et/ou Y de la decoupe 3x3 tuiles                    
                    ##ouvre l'image
                    datas_clump_id_bin,xsize_clump_id_bin,ysize_clump_id_bin,projection_clump_id_bin,transform_clump_id_bin,raster_band_clump_id_bin = osof.raster_open(clump_id_bin, 1)
                    
                    ##recupere l'index des pixels ayant pour valeur 2
                    index_clump_id_bin = np.argwhere(datas_clump_id_bin == 1)
                    
                    ##determine l'etendu de la zone à 1
                    id_bin_miny,id_bin_maxy,id_bin_minx,id_bin_maxx = osof.extent(index_clump_id_bin, xsize_clump_id_bin, ysize_clump_id_bin)
                    id_bin_ysize = id_bin_maxy - id_bin_miny
                    id_bin_xsize = id_bin_maxx - id_bin_minx
                    ##compare cette etendue avec le raster decoupe
                    if ((id_bin_maxy == ysize_classif and id_bin_maxy != ysize) or (id_bin_maxx == xsize_classif and id_bin_maxx != xsize) or (id_bin_miny == 0 and transform_classif[3] != transform[3]) or (id_bin_minx == 0 and transform_classif[0] != transform[0])) and (id_bin_ysize != ysize and id_bin_xsize != xsize) :
                        print "La selection des entites n'est pas complete, augmentation de la zone de recherche"
                        NumIter += 2
                    else :
                        print "Phase 2, selection de la couronne"
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
            first_passe = True
            NumIterVoisin = 0
                    
            while search_emprise_voisins :
                
                print "Debut de determination de l'emprise maximale de la tuile"
                timer.start()
                
                #decoupe une zone de recherche des voisins equivalent à 1 tuile
                Xstart = Xstart - xsize_tile
                Ystart = Ystart + ysize_tile
                if Xstart < 0 :
                    Xstart = 0
                if Ystart < 0 :
                    Ystart = 0

                if not first_passe :
                    tif_raster_extract_voisin = osof.otb_ExtractROI(raster, "raster_extract_voisin_%s.tif"%(NumIterVoisin-1), Xstart, Ystart, xsize_tile*(3+NumIter+NumIterVoisin), ysize_tile*(3+NumIter+NumIterVoisin), ram)
                    memory_tif_raster_extract_voisin_1 = osof.otb_MiseEnRam([tif_raster_extract_voisin], "im1b1", 8)
                    memory_tif_raster_extract_voisin_2 = osof.otb_MiseEnRam([tif_raster_extract_voisin], "im1b2", 8)
                    memory_tif_raster_extract_voisin = osof.otb_MiseEnRamConcatenate([memory_tif_raster_extract_voisin_1,memory_tif_raster_extract_voisin_2])
                    
#                    if NumIterVoisin-1 != 0 :
#                        #generation masque entites deja traitee
#                        memory_mask_init = osof.otb_Superimpose("raster_extract_voisin_%s.tif"%(NumIterVoisin-1), "raster_extract_voisin_%s.tif"%(NumIterVoisin-2), ram, 8)
#                        mask = osof.otb_bandmath_ram([memory_mask_init], "im1b1==2?0:im1b1", ram, 8, True, True, "mask_voisins.tif")                        
#                    else :
#                        #generation masque entites deja traitee
#                        memory_mask_init = osof.otb_Superimpose("raster_extract_voisin_%s.tif"%(NumIterVoisin-1), "raster_extract_%s.tif"%(NumIter), ram, 8)
#                        mask = osof.otb_bandmath_ram([memory_mask_init], "im1b1==2?0:im1b1", ram, 8, True, True, "mask_voisins.tif")         
                        
                    #mise a l'echelle du clump_id_bin
                    memory_clump_id_bin_voisin = osof.otb_Superimpose(memory_tif_raster_extract_voisin, memory_clump_id_bin, ram, 8, True)
                    clump_id_bin_extend_voisin = osof.otb_bandmath_ram([memory_clump_id_bin_voisin], "im1b1==2?0:im1b1", ram, 8, True, True, "clump_id_bin_extend_voisin.tif")               
                    
                timer.stop()
                time_extent_max_tile += timer.interval
                print "Fin de determition de l'emprise maximale de la tuile %s"%(i), time_extent_max_tile,"\n"
                
                print "Debut de l'identification des voisins de la tuile %s"%(i)
                timer.start() 
                
                if first_passe :
                    #fait une dilution d'un pixel du clump_id_bin
                    memory_clump_id_dilate = osof.otb_dilate(memory_clump_id_bin,ram,8, True, False)
                    
                    #recupere uniquement la partie qui a changee, c'est à dire la frontiere
                    clump_id_boundaries = osof.otb_bandmath_ram([memory_clump_id_bin, memory_clump_id_dilate],"(im1b1==0 && im2b1==1)?1:0", ram, 8, True, True, "clump_id_boundaries.tif")
                    
                    #ouvre les rasters boundarries, classif de la zone et clump de la zone pour generer la liste des voisins ensuite
                    boundaries,xsize_boundaries,ysize_boundaries,projection_boundaries,transform_boundaries, raster_band_boundaries = osof.raster_open(clump_id_boundaries,1)
                    datas_classif_voisin,xsize_classif_voisin,ysize_classif_voisin,projection_classif_voisin,transform_classif_voisin, raster_classif_voisin = osof.raster_open("raster_extract_%s.tif"%(NumIter),1)
                    datas_clump_voisin,xsize_clump_voisin,ysize_clump_voisin,projection_clump_voisin,transform_clump_voisin, raster_clump_voisin = osof.raster_open("raster_extract_%s.tif"%(NumIter),2)
                
                    timer.stop()
                    time_select_id_neighbors += timer.interval
                    print "Fin de l'identification des voisins de la tuile %s"%(i), time_select_id_neighbors,"\n"
                
                    print "Début de la lecture des identifiants des voisins de la tuile %s"%(i)
                    timer.start()
                    
                    #parcours chaque pixel de la couronne externe pour connaitre l'id du voisin
                    liste_id_couronne = np.unique(np.where(((datas_classif_voisin > 1) & (datas_classif_voisin < 250) & (boundaries == 1)),datas_clump_voisin,0)).tolist()
                    liste_id_couronne = [x for x in liste_id_couronne if x != 0] 
                    nb_features_neighbors += len(liste_id_couronne)                           
                    print "Nombre de voisins de la cellule %s :"%(i), nb_features_neighbors
                    timer.stop()
                    print "Fin de la creation de la liste des voisins de la tuile %s"%(i), timer.interval,"\n"
                    
                #test la presence de la mer pour savoir si l'on ajoute les
                #entite de la tuile + ceux de la couronne à la liste
                if len(liste_id_couronne) != 0 :
                    if first_passe :
                        if np.any((boundaries == 1) & (datas_classif_voisin == 255)):
                            liste_id_couronne = liste_id_couronne + tile_id
                        elif len(liste_id_couronne) != 0 :
                            liste_id_couronne = liste_id_couronne                       
                    
                    print "Debut de l'identification de l'etendue des voisins de la tuile %s"%(i)
                    timer.start()
                    
                    #selon la liste des conditions, identifie l'emprise des voisins
                    if first_passe :
                        conditions_id_couronne = osof.genere_liste_conditions(liste_id_couronne,2)        
                        conditions_id_couronne = conditions_id_couronne + "?0:1"
                        couronne = osof.otb_bandmath_ram([memory_tif_raster_extract], conditions_id_couronne, ram, 32, True, True,"couronne.tif")
                        memory_couronne = osof.otb_MiseEnRam([couronne], "im1b1", 8)
                        
                    else :
                        #changement taille raster couronne precedent pour le fusion par la suite
                        memory_couronne_temp = osof.otb_Superimpose(memory_tif_raster_extract_voisin, memory_couronne, ram, 8, True)
                        memory_couronne_extend = osof.otb_bandmath_ram([memory_couronne_temp], "im1b1==2?3:im1b1", ram, 8, True, False)
                        
                        #selon la liste des conditions et d'un raster masque, identifie l'emprise des voisins dans la zone ou ce ne l'a pas encore ete
                        conditions_id_couronne = osof.genere_liste_conditions(liste_id_couronne,2)
                        conditions_id_couronne = "(im2b1==3 &&(" + conditions_id_couronne + "))?0:1"                  
                        memory_couronne_new_extent = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin, memory_couronne_extend], conditions_id_couronne, ram, 32, True, False)
                        
                        #fusion de la nouvelle couronne avec l'ancienne
                        couronne = osof.otb_bandmath_ram([memory_couronne_extend, memory_couronne_new_extent], "((im1b1==0)||(im2b1==0))?0:1",ram, 8, True, True, "couronne.tif")
                        memory_couronne = osof.otb_MiseEnRam([couronne], "im1b1", 8)
                        
                    #ouvre le fichier couronne pour recuperer l'etendue des pixels correspondants aux voisins
                    datas_couronne,xsize_couronne,ysize_couronne,projection_couronne,transform_couronne, raster_band_couronne = osof.raster_open(couronne,1)
                    
                    #genere l'index des entites    
                    index_couronne = np.argwhere(datas_couronne == 0)
                    
                    timer.stop()
                    time_extent_neighbors += timer.interval
                    print "Fin de l'identification de l'etendue des voisins de la tuile %s"%(i), time_extent_neighbors,"\n"
                    
                    print "Debut zone a extraire selon l'etendue des voisins de la tuile %s"%(i)
                    timer.start()
                
                elif len(liste_id_couronne) == 0 :
                    #s'il n'y a pas de voisins
                    print "Aucun voisins, utilisation du fichier clump_id_bin_extend_voisin"
                    if first_passe :
                        datas_couronne,xsize_couronne,ysize_couronne,projection_couronne,transform_couronne, raster_band_couronne = osof.raster_open(clump_id_bin,1)
                    else :
                        datas_couronne,xsize_couronne,ysize_couronne,projection_couronne,transform_couronne, raster_band_couronne = osof.raster_open(clump_id_bin_extend_voisin,1)
                    print "Debut zone a extraire selon l'etendue des voisins de la tuile %s"%(i)
                    timer.start()
                    
                    #genere l'index des entites    
                    index_couronne = np.argwhere(datas_couronne == 1)
                
                ##determine l'etendu de la zone à 1
                id_couronne_miny,id_couronne_maxy,id_couronne_minx,id_couronne_maxx = osof.extent(index_couronne, xsize_couronne, ysize_couronne)
                id_couronne_ysize = id_couronne_maxy - id_couronne_miny
                id_couronne_xsize = id_couronne_maxx - id_couronne_minx
                    
                timer.stop()
                print "Fin zone a extraire selon l'etendue des voisins de la tuile %s"%(i), timer.interval,"\n"
                
                ##compare cette etendue avec le raster decoupe
                if ((id_couronne_maxy == ysize_classif_voisin and id_couronne_maxy != ysize) or (id_couronne_maxx == xsize_classif_voisin and id_couronne_maxx != xsize) or (id_couronne_minx == 0 and transform_couronne[0] != transform[0]) or ( id_couronne_miny == 0 and transform_couronne[3] != transform[3])) and (id_couronne_ysize != ysize and id_couronne_xsize != xsize) :
                    print "La selection des voisins n'est pas complete, augmentation de la zone de recherche"
                    NumIterVoisin += 1
                    first_passe = False
                    
                else :
                    print "Fin de la selection des voisins"
                    search_emprise_voisins = False
                    
            print "Debut export de la zone %s"%(i)
            timer.start() 
            
            #change la condition des identifiants de la tuile pour distinguer les pixels de classif et de clump
            conditions_id_extract = conditions_tile + "?im1b1:im1b2"                              
                
            if os.path.exists("couronne.tif") :
                if not first_passe :
                    #calcul le fichier tif avec des valeurs à 0, de classe et d'identifiants
                    memory_intermediaire_tile = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin], conditions_id_extract, ram, 32, True, False)  
                    out = osof.otb_bandmath_ram([memory_intermediaire_tile, memory_couronne], "(im2b1 == 1 && im1b1 > 255)?0:im1b1", ram, 32, True, True, outfiles+"/tile_%s.tif"%(i))

                else :
                    #calcul le fichier tif avec des valeurs à 0, de classe et d'identifiants
                    memory_intermediaire_tile = osof.otb_bandmath_ram([memory_tif_raster_extract], conditions_id_extract, ram, 32, True, False)     
                    out = osof.otb_bandmath_ram([memory_intermediaire_tile, memory_couronne], "(im2b1 == 1 && im1b1 > 255)?0:im1b1", ram, 32, True, True, outfiles+"/tile_%s.tif"%(i))
                    
            else :
                if not first_passe :
                    out = osof.otb_bandmath_ram([memory_tif_raster_extract_voisin], conditions_id_extract, ram, 32, True, True, outfiles+"/tile_%s.tif"%(i))
                else :
                    out = osof.otb_bandmath_ram([memory_tif_raster_extract], conditions_id_extract, ram, 32, True, True, outfiles+"/tile_%s.tif"%(i))
                    
            timer.stop()
            print "Fin export de la zone %s"%(i), timer.interval,"\n"
            
            print "Debut de changement du nodata de la tuile %s"%(i)
            #change les valeurs 0 en nodata pour ne pas être prise en compte dans grass gis
            command = "gdal_translate -a_nodata 0 outfiles/tile_%s.tif outfiles/tile_%s_ndata.tif"%(i,i)
            os.system(command)
            os.remove("outfiles/tile_%s.tif"%(i))
            os.rename("outfiles/tile_%s_ndata.tif"%(i),"outfiles/tile_%s.tif"%(i))
            
            time_tif_tile = time.time() - debut_tif_tile
            print "Temps de traitement de la tuile %s en : "%(i), time_tif_tile,"\n"
            
            if cluster:
                with open(inpath+"/log_jobs_tif_%s.csv"%(ngrid), "a") as csvfile:
                    csvfile.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n"%(int(ngrid), int(nb_features_tile), round(time_condition_tile,0),\
                    round(time_extent_tile,0), round(time_extent_max_tile,0), round(time_select_id_neighbors,0), int(nb_features_neighbors),\
                    round(time_extent_neighbors,0), round(time_tif_tile,0)))
            else:
                with open(inpath+"/log_jobs_tif.csv", "a") as csvfile:
                    csvfile.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n"%(int(ngrid), int(nb_features_tile), round(time_condition_tile,0),\
                    round(time_extent_tile,0), round(time_extent_max_tile,0), round(time_select_id_neighbors,0), int(nb_features_neighbors),\
                    round(time_extent_neighbors,0), round(time_tif_tile,0)))

        else :                    
          continue
      
    if not tmp:
        liste_effacer = ["classif_reshape.tif","clump_id_bin.tif","clump_id_binary.tif","clump_id_boundaries.tif","clump_id_dilate.tif",\
        "clump_reshape.tif","clump_reshape2.tif","couronne_reshape.tif","couronne_reshape2.tif","datas_reshape2.tif","intermediaire_tile.tif"]
        for fichier in liste_effacer:
            try:
                os.remove(fichier)
            except:
                continue
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
    
    #initialise un fichier log de serialisation tif
    with open(args.path+"/log_jobs_tif_%s.csv"%(args.ngrid), "w") as csvfile :
        csvfile.write("tile;feature_tile;time_condition_tile;\
        time_extent_tile;time_extent_max_tile;time_select_neighbors;feature_neighbors\
        ;time_extent_neighbors;time_tif_tile\n")
        csvfile.close()
        
    serialisation_tif(args.path, args.classif, args.ram, args.grid, "outfiles", args.tmp, args.cluster, args.out, args.ngrid)
     
    if os.path.exists(args.path + "/" + str(args.ngrid) + "/outfiles" + "/tile_%s.tif"%(args.ngrid)): 
        shutil.copy(args.path + "/" + str(args.ngrid) + "/outfiles" + "/tile_%s.tif"%(args.ngrid), args.out + "/"+ str(args.ngrid) + "/outfiles" +"/tile_%s.tif"%(args.ngrid))
        
    if os.path.exists(args.path+"/log_jobs_tif_%s.csv"%(args.ngrid)):   
        shutil.copy(args.path+"/log_jobs_tif_%s.csv"%(args.ngrid), args.out + "/"+ str(args.ngrid) + "/outfiles" + "/log_jobs_tif_%s.csv"%(args.ngrid))
