# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
Script permettant d'effectuer la ou les regularisation, , reechantillonner, creer le masque mer, modifier
les valeurs de l'eau maritime, générer un identifiant unique pour chacun des groupes de pixels de 
meme classe générer la grille de serialisation. Il y a une possibilite d'effectuer la serialisation des 
raster a simplificer en mode non cluster et parallelise (dans le cas où l'argument cluster == False)
"""
import shutil
import sys
import os
import time
import argparse
from osgeo import gdal,ogr,osr
from multiprocessing import Pool
from functools import partial
import numpy as np
import OSO_functions as osof
import regularisation
import grille
import clump
import job_tif
import job_simplification
    
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
	parser = argparse.ArgumentParser(description = "Regulararize a raster" \
        "and simplify the corresponding vector ")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)
                                   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of classification", required = True)
        
        parser.add_argument("-mer", dest="sea", action="store", \
                            help="sea shapefile", required = True)
        
        parser.add_argument("-regul", dest="regul", action="store", \
                            help="Do regularisation and clump ? True or False", required = True)
        
        parser.add_argument("-clump", dest="clump", action="store", \
                            help="otb or scikit clump ? otb or scikit")
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)                           
                            
        parser.add_argument("-strippe", dest="strippe", action="store", \
                            help="Number of strippe for otb process", required = True)
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb applications", default="10000")
                            
        parser.add_argument("-umc1", dest="umc1", action="store", \
                            help="UMC for first regularization", required = True)
                                
        parser.add_argument("-umc2", dest="umc2", action="store", \
                            help="UMC for second regularization")
                        
        parser.add_argument("-rssize", dest="rssize", action="store", \
                            help="Pixel size for resampling")
                                
        parser.add_argument("-grid", dest="grid", action="store", \
                            help="Coefficient of grid", required = True)
                            
        parser.add_argument("-tmp", dest="tmp", action="store", \
                            help="keep temporary files ? True or False") 
                                                
        parser.add_argument("-log", dest="log", action="store", \
                            help="log name", required = True)

        parser.add_argument("-out", dest="out", action="store", help="output folder", required = True)                            

        parser.add_argument("-cluster", dest="cluster", action="store", \
                            help="If True, don't pool simplification phase and do only regularization", required = True)

        parser.add_argument("-float64", action="store_true", \
                            help="float64 otb execution", default = False)         

        #----------------------------------------------------------------------
        ################## only if -cluster == "False" ########################

        parser.add_argument("-nbprocess", dest="nbprocess", action="store", \
                            help="parallelization of tiles")
                            
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library")
                            
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="douglas value")   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="hermite value")   
                            
        parser.add_argument("-angle", dest="angle", action="store", \
                            help="angle 45 or not ? True, False.")   
            
        parser.add_argument("-resample", dest="resample", action="store", \
                            help="resample vector ? True, False")
        
                            
        args = parser.parse_args()
 
        timer = osof.Timer()
        debut_regularisation_total = time.time()
        debut_regularisation = time.time()
        
        #nombre de processeurs utilises par OTB
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
        
        #suppression des dossiers tuiles issus des precedents runs
        num_dossier = 0
        erase = True
        while erase == True :           
            try :
                shutil.rmtree(args.path+str(num_dossier))
                num_dossier += 1
            except:
                erase = False
        
        #cree un fichier log        
        with open(args.log, "w") as csvfile :    
            csvfile.close()
            
        #s'il faut faire la regularisation
        if str(args.regul) == "True":
            
            print "Regularisation UMC 1 \n"
            with open(args.log, "a") as csvfile :
                csvfile.write("Regularisation UMC 1 \n")
                csvfile.close()
                
            #effectue la premiere regularisation avec la valeur de l'umc 1
            classifRegularisee, time_regularisation1 = regularisation.regularisation(args.classif, args.umc1, args.core, args.path, args.out)
            
            print "TEMPS : %s secondes \n"%(round(time_regularisation1,2))
            with open(args.log, "a") as csvfile :
                csvfile.write("TEMPS : %s secondes \n"%(round(time_regularisation1,2)))
                csvfile.close()
            
            #s'il y a une valeur dans l'umc 2
            if args.umc2 != None :
                
                #dans le cadre du projet OSO, la seconde umc s'effectue sur un raster a 20m de resolution spatiale.                  
                if args.rssize != None :
                    
                    #reechantillonnage
                    timer.start()
                    print "Reechantillonnage \n"
                    with open(args.log, "a") as csvfile :
                        csvfile.write("Reechantillonnage \n")
                        csvfile.close()
                    
                    command = "gdalwarp -multi -wo NUM_THREADS=%s -r mode -tr %s %s %s %s/reechantillonnee.tif" %(args.core, args.rssize, args.rssize, classifRegularisee, args.path)
                    os.system(command)
                    classifRegularisee = "%s/reechantillonnee.tif"%(args.path)
                    
                    timer.stop()
                    print "TEMPS : %s secondes \n"%(round(timer.interval,2))
                    with open(args.log, "a") as csvfile :
                        csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
                        csvfile.close()
                        
                print "Regularisation UMC 2 \n"
                with open(args.log, "a") as csvfile :
                    csvfile.write("Regularisation UMC 2 \n")
                    csvfile.close()
                
                #effectue la seconde regularisation avec la classification regularisee umc 1 (reechantillonnee ou non)
                classifRegularisee, time_regularisation2 = regularisation.regularisation(classifRegularisee, args.umc2, args.core, args.path, args.out)
                
                print "TEMPS : %s secondes \n"%(round(time_regularisation2,2))
                with open(args.log, "a") as csvfile :
                    csvfile.write("TEMPS : %s secondes \n"%(round(time_regularisation2,2)))
                    csvfile.close()
                
            else :
                #pour indiquer qu'il n'y a pas eu de seconde regularisation dans le fichier de log
                time_regularisation2 = 0
            
            timer.start()
            print "Distinction eau maritime et eau continentale \n"
            with open(args.log, "a") as csvfile :
                csvfile.write("Distinction eau maritime et eau continentale \n")
                csvfile.close()
                    
            #cree un raster sans donnees ayant les caracteristiques de la classification (reechantillonnee ou non)
            tifMasqueMer = osof.otb_bandmath_ram([classifRegularisee], "im1b1*0", args.strippe, 8, False, True, args.path + "/" + "masque_mer.tif")
            
            #assigne la valeur 1 au continent d'apres un shapefile (data.gouv, france openstreetmap, simplifiee 5m, 2014)
            command = "gdal_rasterize -burn 1 %s %s"%(args.sea, tifMasqueMer)
            os.system(command)
                
            # utilise la classification et le mask mer pour modifier les valeurs de l'eau maritime
            classifRegularisee2 = osof.otb_bandmath_ram([classifRegularisee, tifMasqueMer], "(im1b1==51) && (im2b1==0)?255:im1b1", args.strippe, 8, False, True, args.path+"/classification_regularisee.tif")            

            timer.stop()
            
            print "TEMPS : %s secondes \n"%(round(timer.interval,2))
            with open(args.log, "a") as csvfile :
                csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
                csvfile.close()
                
            ## generation des identifiants uniques pour chacune des entites##
                
            timer.start()
            print "Generation du fichier clump \n"
            with open(args.log, "a") as csvfile :
                csvfile.write("Creation du fichier clump \n")
                csvfile.close()
                
            #generation via otb_segmentation
            if args.clump == "otb":                    
                # genere le raster ayant les identifiants uniques
                clump.otb_segmentation(classifRegularisee2, args.path+"/clump.tif", args.strippe)
                
                # ajoute une valeur de 300 a chacun des identifiants, pour distinguer les valeurs de la classe OSO lors de l'etape de simplification
                # Gestion du bug sur Bandmath de OTB => remplacement par numpy
                dsClump = gdal.Open(args.path+"/clump.tif")
                arrayClump = np.array(dsClump.GetRasterBand(1).ReadAsArray())
                arrayClump300 = arrayClump + 300
                rows = dsClump.RasterYSize
                cols = dsClump.RasterXSize
                projection = dsClump.GetProjectionRef()
                osof.raster_save(args.path+"/clump_300.tif", cols, rows, dsClump.GetGeoTransform(), arrayClump300, projection, gdal.GDT_UInt32)
                #osof.otb_bandmaths([args.path+"/clump.tif"], args.path+"/clump_300.tif", "im1b1+300", args.ram, 32)
                
                os.remove(args.path+"/clump.tif")
                os.rename(args.path+"/clump_300.tif", args.path+"/clump.tif")
                clump_file = args.path+"/clump.tif"
            
            #generation via scikit image
            elif args.clump == "scikit":
                clump_file, time_clump = clump.clumpScikit(args.path, classifRegularisee2)                
            
            timer.stop()
            print "TEMPS : %s secondes \n"%(round(timer.interval,2))
            with open(args.log, "a") as csvfile :
                csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
                csvfile.close()

            if not args.float64:
                #genere un raster bi-bande ayant en b1 la classification regularisee et en b2 les identifiants uniques
                clump.otb_concatenate_image(classifRegularisee2, clump_file, args.path+"/classif_clump_regularisee.tif")
                
            else:
                # gestion du problème de doublons (utilisation du codage DOUBLE)
                command = '/work/OT/theia/oso/OTB/otb_superbuild/iotaDouble/'\
                          'iota2ConcatenateImages %s %s %s'%((classifRegularisee2, \
                                                              clump_file, \
                                                              args.path + "/classif_clump_regularisee.tif"))
                os.system(command)
                
            print "Creation du raster bi-bande classification regularisee (b1) et clump (b2) \n"
            with open(args.log, "a") as csvfile :
                csvfile.write("Creation du raster bi-bande classification regularisee (b1) et clump (b2) \n")
                csvfile.close()
                
            shutil.copy(args.path + "/classif_clump_regularisee.tif", args.out +"/classif_clump_regularisee.tif")

            #suppression des fichiers intermediaires
            if str(args.tmp) == "False" :
                os.remove(args.path+"/reechantillonnee.tif")
                os.remove(args.path+"/masque_mer.tif")
                os.remove(args.path+"/clump.tif")
                os.remove(classifRegularisee)
                os.remove(classifRegularisee2)
            
            classifRegularisee = args.path+"/classif_clump_regularisee.tif"
            
            duree_regularisation = time.time() - debut_regularisation
            print "Fin de la regularisation et du clump en : %s secondes \n"%(round(duree_regularisation,2))
            with open(args.log, "a") as csvfile :
                csvfile.write("Fin de la regularisation et du clump en : %s secondes \n"%(round(duree_regularisation,2)))
                csvfile.close()
                
        #si la regularisation n'est pas a effectue, le raster en entree l'est deja
        else :               
            #ouvre le raster bi-bande en entree
            classifRegularisee = args.classif
        
        timer.start()
        print "Generation de la grille de serialisation \n"
        with open(args.log, "a") as csvfile :
            csvfile.write("Generation de la grille de serialisation \n")
            csvfile.close()
            
        #generation de la grille de serialisation
        nbtiles = grille.grid_generate(args.path + "/" + "grille.shp", classifRegularisee, args.grid)
        
        for ext in ["shp", "dbf", "prj", "shx"]:
            shutil.copy(args.path + "/" + "grille.%s"%(ext), args.out + "/" + "grille.%s"%(ext))
            os.remove(args.path + "/" + "grille.%s"%(ext))
        
        timer.stop()
        print "TEMPS : %s secondes \n"%(round(timer.interval,2))
        with open(args.log, "a") as csvfile :
            csvfile.write("TEMPS : %s secondes \n"%(round(timer.interval,2)))
            csvfile.close()
        
        time_regularisation_total = time.time() - debut_regularisation_total
        print "Temps de traitement total : %s secondes \nFin"%(round(time_regularisation_total,2))
        with open(args.log, "a") as csvfile :
            csvfile.write("Temps de traitement total : %s secondes \nFin"%(round(time_regularisation_total,2)))
            csvfile.close()
            
#        #si le script n'est pas utilise sur le cluster, alors la parallelisation de job_tif et job_simplification utilisation la librairie multiprocessing de python
#        #attention a bien renseigner les parametres supplementaires de oso_main
#        if str(args.cluster) == "False":
#            
#            #initialise un fichier log de serialisation tif
#            with open(args.path+"log_jobs_tif.csv", "w") as csvfile :
#                csvfile.write("tile;feature_tile;time_condition_tile;\
#                time_extent_tile;time_extent_max_tile;time_select_neighbors;feature_neighbors\
#                ;time_extent_neighbors;extent_xmin;\
#                extent_xmax;extent_ymin;extent_ymax;time_tif_tile\n")
#                csvfile.close()
#            
#            #generation des tifs par tuile
#            pool = Pool(processes=int(args.nbprocess))
#            iterable = (np.arange(nbtiles)).tolist()
#            function = partial(job_tif.serialisation_tif, args.path, classifRegularisee, args.ram, args.out + "/" + "grille.shp", "outfiles", args.tmp, False, args.out)
#            pool.map(function, iterable)
#            pool.close()
#            pool.join()
#            
#            #initialise un fichier log de simplification des tifs
#            with open(args.path+"log_jobs_simplification.csv", "w") as csvfile :
#                csvfile.write("tile;time_vectorisation;time_douglas;\
#                time_hermite;time_simplification\n")
#                csvfile.close()
#            
#            #simplification des tifs
#            pool = Pool(processes=int(args.nbprocess))
#            iterable = (np.arange(nbtiles)).tolist()
#            function = partial(job_simplification.simplification, args.path, args.path, args.douglas, args.hermite, args.angle, args.resample, args.tmp, args.grass, False, args.out)
#            pool.map(function, iterable)
#            pool.close()
#            pool.join()
        
        
        
            
         
