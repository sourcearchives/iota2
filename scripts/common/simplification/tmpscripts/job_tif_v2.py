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
from skimage.measure import regionprops


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

def listTileEntities(raster, outpath, ngrid, feature):

    # ouvre le clump et la classification de la zone ayant ete decoupee
    datas_classif, xsize_classif, ysize_classif, projection_classif, transform_classif, raster_band_classif = osof.raster_open(raster, 1)
    datas_clump, xsize_clump, ysize_clump, projection_clump, transform_clump, raster_band_clump = osof.raster_open(raster, 2)
    print "\nXsize de la zone de recherche", xsize_classif,"Ysize de la zone de recherche",ysize_classif
                    
    with open(outpath+"/"+ngrid+"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Xsize de la zone de recherche %s Ysize de la zone de recherche %s \n"%(xsize_classif,ysize_classif))
        csvfile.close()
                        
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
    
def listTileNeighbors(clumpIdBoundaries, tifRasterExtract, listTileId):
    """
    Genere la liste des identifiants des voisins.
    """
    #ouvre les rasters necessaires
    boundaries, xsize_boundaries, ysize_boundaries, \
        projection_boundaries, transform_boundaries, raster_band_boundaries = osof.raster_open(clumpIdBoundaries,1)
    datas_classif_voisin, xsize_classif_voisin, ysize_classif_voisin, \
        projection_classif_voisin, transform_classif_voisin, \
        raster_classif_voisin = osof.raster_open(tifRasterExtract,1)
    datas_clump_voisin, xsize_clump_voisin, ysize_clump_voisin, \
        projection_clump_voisin, transform_clump_voisin, \
        raster_clump_voisin = osof.raster_open(tifRasterExtract,2)
    
    #parcours chaque pixel de la frontiere pour connaitre l'id du voisin
    listeIdCouronne = np.unique(np.where(((datas_classif_voisin > 1) & \
                                            (datas_classif_voisin < 250) & \
                                            (boundaries == 1)),datas_clump_voisin,0)).tolist()
    
    #enleve les identifiants de nodata
    listeIdCouronneMaj = [x for x in listeIdCouronne if x != 0] 
    
    #maj la liste avec les identifiants des entites s'il y a la presence de la mer ou de nodata en voisin
    if len(listeIdCouronneMaj) != 0 :
        Voisins = True
        if np.any((boundaries == 1) & ((datas_classif_voisin == 255) | (datas_classif_voisin == 0))):
            listeIdCouronneMaj = listeIdCouronneMaj + listTileId
            eauMaritimeVoisins = True
            print "Presence d'eau maritime / nodata dans les voisins"
        else :
            print "Aucune presence d'eau maritime / nodata dans les voisins"
            eauMaritimeVoisins = False
    else :
        eauMaritimeVoisins = True
        Voisins = False
            
    return listeIdCouronneMaj, eauMaritimeVoisins, Voisins

def Extent(tile_id, Params, xsize, ysize, voisin=False):
    
    subParams = {x:Params[x] for x in tile_id}
    valsExtents = list(subParams.values())

    minCol = min([y for x, y, z, w in valsExtents])
    minRow = min([x for x, y, z, w in valsExtents])
    maxCol = max([w for x, y, z, w in valsExtents])       
    maxRow = max([z for x, y, z, w in valsExtents])
    
    if not voisin :
        print "+1 pixel"
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
    # Gestion des répertoires
    manageEnvi(inpath, outpath, ngrid)
        
    timer = osof.Timer()
    debutTraitement = time.time()   
    
    print "########## INITIALISATION ENVIRONNEMENT ##########\n"
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("########## INITIALISATION JOB ##########\n")
        csvfile.close()
    
    # ouverture de la classification regularise pour recuperer ses informations geographiques
    print "Ouverture classification et generation du regionsprops (skimage)\n"
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Ouverture classification et generation du regionsprops (skimage)\n")
        csvfile.close()
        
    timer.start()    
    
    rasterfile = gdal.Open(raster, 0)
    clumpBand = rasterfile.GetRasterBand(2)
    xsize = rasterfile.RasterXSize
    ysize = rasterfile.RasterYSize
    clumpArray = clumpBand.ReadAsArray()
    clumpProps = regionprops(clumpArray)
    rasterfile = None
    
    timer.stop()
    
    print "TEMPS : %s secondes\n"%(round(timer.interval,2))
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
        csvfile.close()
        
    #generation dictionnaire label:bbox
    print "Genere dictionnaire label:bbox\n"
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Genere dictionnaire label:bbox\n")
        csvfile.close()
    
    timer.start()
    
    Params = {}
    i=0
    while clumpProps:
        try:
            Params[clumpProps[i].label] = clumpProps[i].bbox
            i+=1
        except:
            IndexError
            print "Fin generation dictionnaire label:bbox"
            break
    
    timer.stop()
    
    print "TEMPS : %s secondes\n"%(round(timer.interval,2))
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
        csvfile.close()
        
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
            
            ############# Phase 1 #############
            print "########## Phase 1 ##########\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("########## Phase 1 ##########\n")
                csvfile.close()
        
            #genere liste entites
            print "Genere la liste des identifiants de la tuile\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Genere la liste des identifiants de la tuile\n")
                csvfile.close()
                
            listTileId = listTileEntities(raster, outpath, ngrid, feature)
            
            # si la liste de la tuile ne contient pas d'identifiants
            if len(listTileId) == 0 :          
                print "Aucune entite dans la tuile.Fin"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Aucune entite dans la tuile.Fin")
                    csvfile.close()  
                    sys.exit()
                    
            print "Nombre d'entites : %s\n"%(len(listTileId))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Nombre d'entites : %s\n"%(len(listTileId)))
                csvfile.close()
            
              
            #calcule la bounding box de la zone à decouper +1 et -1 pixel (pour effectuer otb dilate)
            #exemple de sortie : [0L, 0L, 163L, 236L] soit [minRow, minCol, maxRow, maxCol]
            print "Calcule la bounding box des entites (+1 pixel)\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Calcule la bounding box des entites (+1 pixel)\n")
                csvfile.close()
                
            timer.start()
            
            listExtent = Extent(listTileId, Params, xsize, ysize)
            print listExtent
            timer.stop()
            
            print "TEMPS : %s secondes\n"%(round(timer.interval,2))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                csvfile.close()
                
            tifRasterExtract = inpath + "/" + str(ngrid) + "/raster_extract.tif"
            
            print "Decoupage de la classification selon l'emprise des entites de la tuile\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Decoupage de la classification selon l'emprise des etnites de la tuile\n")
                csvfile.close()
                
            #decoupe la zone
            command = "gdal_translate -srcwin {} {} {} {} -ot UInt32 {} {}".format(listExtent[1], listExtent[0], listExtent[3]-listExtent[1], listExtent[2]-listExtent[0], raster, tifRasterExtract) 
            os.system(command)
            
            shutil.copy(tifRasterExtract, outpath + "/" + str(ngrid) + "/raster_extract.tif")
            
            print "Calcul de l'emprise des entites\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Calcul de l'emprise des entites\n")
                csvfile.close()
            
            timer.start()

            #genere l'expression otb pour calculer l'emprise des entites de la tuile
            condition = osof.genere_liste_conditions(listTileId,2)
            conditionIdTile = condition + "?1:0"
            
            #genere un raster binaire pour identifier l'emprise des entites de la tuile
            memoryClumpIdBin = osof.otb_bandmath_ram([tifRasterExtract], conditionIdTile, ram, 8, False, False)
            
            tifClumpIdBin = osof.otb_bandmath_ram([memoryClumpIdBin], "im1b1", ram, 8, True, True, inpath + "/" + str(ngrid) + "/ClumpIdBin.tif")
            shutil.copy(tifClumpIdBin, outpath + "/" + str(ngrid) + "/ClumpIdBin.tif")
            
            timer.stop()
            
            print "TEMPS : %s secondes\n"%(round(timer.interval,2))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                csvfile.close()
            
            ############# Phase 2 #############
            
            print "############# Phase 2 #############\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("############# Phase 2 #############\n")
                csvfile.close()
                
            print "Genere la liste des identifiants des voisins\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Genere la liste des identifiants des voisins\n")
                csvfile.close()
            
            timer.start()
            
            #effectue un dilate d'un pixel
            memoryClumpIdDilate = osof.otb_dilate(memoryClumpIdBin, ram, 8, True, False)
            
            #recupere uniquement la partie qui a changee, c'est a dire la frontiere
            clumpIdBoundaries = osof.otb_bandmath_ram([memoryClumpIdBin, \
                                                         memoryClumpIdDilate],\
                                                        "(im1b1==0 && im2b1==1)?1:0", \
                                                        ram, 8, True, True, \
                                                        inpath + "/" + str(ngrid) + "/clump_id_boundaries.tif")
            
            shutil.copy(clumpIdBoundaries, outpath + "/" + str(ngrid) + "/clumpIdBoundaries.tif")
            
            #genere liste des voisins et un booleen pour savoir s'il y a de l'eau maritime dans les voisins et s'il y a des voisins
            listTileIdCouronne, eauMartitimeVoisins, Voisins = listTileNeighbors(clumpIdBoundaries, tifRasterExtract, listTileId)
            
            print "Nombre de voisins : %s\n"%(len(listTileIdCouronne))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Nombre de voisins : %s\n"%(len(listTileIdCouronne)))
                csvfile.close()
                
            timer.stop()         
                    
            print "TEMPS : %s secondes\n"%(round(timer.interval,2))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                csvfile.close()
            
            # s'il y a des voisins
            if Voisins :
                    
                #calcule la bounding box de la zone a decouper                
                print "Calcule la bounding box des voisins\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Calcule la bounding box des voisins\n")
                    csvfile.close()
                
                timer.start()
                
                #exemple de sortie : [0L, 0L, 163L, 236L] soit [minRow, minCol, maxRow, maxCol]    
                listExtentNeighbors = Extent(listTileIdCouronne, Params, xsize, ysize, True)
                
                timer.stop()
                
                print "TEMPS : %s secondes\n"%(round(timer.interval,2))
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                    csvfile.close()
                    
                tifRasterExtractNeighbors = inpath + "/" + str(ngrid) + "/raster_extract_voisins.tif"
    
                #decoupe la zone
                command = "gdal_translate -srcwin {} {} {} {} -ot UInt32 {} {}".format(listExtentNeighbors[1], listExtentNeighbors[0], listExtentNeighbors[3]-listExtentNeighbors[1], listExtentNeighbors[2]-listExtentNeighbors[0], raster, tifRasterExtractNeighbors) 
                os.system(command)
                
                shutil.copy(tifRasterExtractNeighbors, outpath + "/" + str(ngrid) + "/raster_extract_voisins.tif")
                
                print "Calcul de l'emprise des voisins\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Calcul de l'emprise des voisins\n")
                    csvfile.close()
                
                timer.start()
                
                #genere l'expression otb pour calculer l'emprise des entites de la tuile
                condition = osof.genere_liste_conditions(listTileIdCouronne,2)
                conditionIdTileNeighbors = condition + "?1:0"
                                                     
                memoryClumpIdBinNeighbors = osof.otb_bandmath_ram([tifRasterExtractNeighbors], conditionIdTileNeighbors, ram, 8, False, False)
                
                tifClumpIdBinNeighbors = osof.otb_bandmath_ram([memoryClumpIdBinNeighbors], "im1b1", ram, 8, True, True, inpath + "/" + str(ngrid) + "/ClumpIdBinNeighbors.tif")
                shutil.copy(tifClumpIdBinNeighbors, outpath + "/" + str(ngrid) + "/ClumpIdBinNeighbors.tif")
            
                timer.stop()
                
                print "TEMPS : %s secondes\n"%(round(timer.interval,2))
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                    csvfile.close()
     
                ############# Phase 3 #############
                
                print "############# Phase 3 avec voisins #############\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("############# Phase 3 avec voisins #############\n")
                    csvfile.close()
                    
                #met en ram le raster bi-bande classification-clump en ram
                memoryTifRasterExtractNeighborsB1 = osof.otb_MiseEnRam([tifRasterExtractNeighbors], "im1b1", 8)
                memoryTifRasterExtractNeighborsB2 = osof.otb_MiseEnRam([tifRasterExtractNeighbors], "im1b2", 32)
                memoryRasterExtractNeighbors = osof.otb_MiseEnRamConcatenate([memoryTifRasterExtractNeighborsB1,\
                                                                                memoryTifRasterExtractNeighborsB2],32)
                
                #Redimensionne le fichier clumpIdBin pour le faire correspondre a l'emprise du raster des voisins
                memoryClumpIdBinResample = osof.otb_SuperimposeJobTifv2(memoryRasterExtractNeighbors, memoryClumpIdBin, ram, 8, True)
                
                tifClumpIdBinResample = osof.otb_bandmath_ram([memoryClumpIdBinResample], "im1b1", ram, 8, True, True, inpath + "/" + str(ngrid) + "/ClumpIdBinResample.tif")
                shutil.copy(tifClumpIdBinResample, outpath + "/" + str(ngrid) + "/ClumpIdBinResample.tif")
                                                  
                print "Generation du raster de sortie\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Generation du raster de sortie\n")
                    csvfile.close()   
                                
                timer.start()
                
                print "Raster avec identifiant des voisins\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Raster avec identifiant des voisins\n")
                    csvfile.close() 
                
                if not eauMartitimeVoisins :
                    #s'il n'y a pas d'eau maritime dans les voisins, alors nous pouvons utiliser uniquement le raster binaire des voisins
                
                    #Genere un fichier tif de la dimension des voisins et avec leurs identifiants
                    memoryOutRasterNeighbors = osof.otb_bandmath_ram([memoryRasterExtractNeighbors, memoryClumpIdBinNeighbors], \
                                                                      "im2b1==1?im1b2:0", ram, 32, True, False)
                else:
                    #s'il y a de l'eau maritime, il est necessaire d'utiliser le raster binaire des entites de la tuile en plus pour
                    #distinguer les entites de cette premiere selection de celles presentent dans le raster binaire des voisins
                    
                    #Genere un fichier tif de la dimension des voisins et avec leurs identifiants
                    memoryOutRasterNeighbors = osof.otb_bandmath_ram([memoryRasterExtractNeighbors, \
                                                                        memoryClumpIdBinNeighbors, \
                                                                        memoryClumpIdBinResample], \
                                                                      "(im2b1==1 && im3b1==0)?im1b2:0", ram, 32, True, False)
                                                                      
                timer.stop()
                
                print "TEMPS : %s secondes\n"%(round(timer.interval,2))
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                    csvfile.close()
                                                     
                #nom du raster temporaire en sortie
                outfileTemp = inpath + "/" + str(ngrid) + "/outfiles/tile_%s_without_nodata.tif"%(i)
                
                print "Raster avec classe des entites\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Raster avec classe des entites\n")
                    csvfile.close() 
                
                timer.start()

                #Genere un fichier tif de la dimension des voisins et les classes oso pour les entites de la tuile
                outRasterTemp = osof.otb_bandmath_ram([memoryRasterExtractNeighbors, memoryClumpIdBinResample, memoryOutRasterNeighbors], \
                                                                  "(im2b1==1 && im3b1==0)?im1b1:im3b1", ram, 32, True, True, outfileTemp)                                         
                
                timer.stop()
                
                print "TEMPS : %s secondes\n"%(round(timer.interval,2))
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                    csvfile.close()
            
            #s'il n'y a pas de voisins, le fichier a simplifier correspond uniquement aux entites de la tuile
            if not Voisins :
                
                print "############# Phase 3 sans voisins #############\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("############# Phase 3 sans voisins #############\n")
                    csvfile.close()
                    
                #met en ram le raster bi-bande classification-clump de l'etendue des entites
                memoryTifRasterExtractB1 = osof.otb_MiseEnRam([tifRasterExtract], "im1b1", 8)
                
                print "Generation du raster de sortie\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Generation du raster de sortie\n")
                    csvfile.close()   
                                
                timer.start()
                
                print "Raster avec classe des entites\n"
                with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                    csvfile.write("Raster avec classe des entites\n")
                    csvfile.close() 
                
                #nom du raster temporaire en sortie
                outfileTemp = inpath + "/" + str(ngrid) + "/outfiles/tile_%s_without_nodata.tif"%(i)
                
                #Genere un fichier tif avec la classe des entites de la tuile et des valeurs 0 pour le reste
                outRasterTemp = osof.otb_bandmath_ram([memoryTifRasterExtractB1, memoryClumpIdBin], \
                                                        "im2b1==1?im1b1:0", ram, 32, True, True, outfileTemp)
                
                timer.stop()
                
            #nom du raster en sortie
            outfile = inpath + "/" + str(ngrid) + "/outfiles/tile_%s.tif"%(i)
            
            print "Gestion des 0 en nodata\n"
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("Gestion des 0 en nodata\n")
                csvfile.close() 
            
            timer.start() 
            
            #change les valeurs 0 en nodata pour ne pas les vectoriser lors de l'etape de simplification
            command = "gdal_translate -a_nodata 0 %s %s"%(outRasterTemp, outfile) 
            os.system(command)
            
            timer.stop()
            
            print "TEMPS : %s secondes\n"%(round(timer.interval,2))
            with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
                csvfile.write("TEMPS : %s secondes\n"%(round(timer.interval,2)))
                csvfile.close()
    
    finTraitement = time.time() - debutTraitement
    
    print "\nTemps de traitement : %s"%(round(finTraitement,2))
    with open(outpath +"/" + ngrid +"/log_prints_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("\nTemps de traitement : %s"%(round(finTraitement,2)))
        csvfile.close() 
                
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
