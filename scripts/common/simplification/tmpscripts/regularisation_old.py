# -*- coding: utf-8 -*-
"""
Processus de regularisation employant gdal_sieve.py 

"""

#import vector_functions as vf
import os
import sys
import numpy as np
import argparse
import otbApplication as otb
from multiprocessing import Pool
from functools import partial
import OSO_functions as osof
import time
import shutil

#------------------------------------------------------------------------------
            
def regularisation(raster, threshold, nbcores, path, out):
              
    #effectue deux passes pour la classification. La première est une
    #regularisation en connexion 8, la seconde est en connexion 4 pour
    #eliminer l'effet "goutte d'eau".
    
    print "Voici l'image traitee\n",raster
    debut_regularisation = time.time()
    
    #dictionnary of OSO classes
    #dico_classe = {11:1, 12:2, 31:3, 32:4, 34:5, 36:6, 41:7, 42:8, 43:9,\
    #44:10, 45:11, 46:12, 51:13, 53:14, 211:15, 221:16, 222:17}
    
    #pour chaque classe, génère un masque selon les règles qui ont été déterminée
    #puis applique ce masque dans gdal_sieve. 
    print "Début de la génération des masques"
    
    print "Creation des fichiers masque"
    #masques des regles adaptatives       
    osof.otb_bandmath_1(raster, path+"/mask_1.tif", "(im1b1==11 || im1b1==12)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_2.tif", "(im1b1==31 || im1b1==32)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_3.tif", "(im1b1==41 || im1b1==42 || im1b1==43)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_4.tif", "(im1b1==34 || im1b1==36 || im1b1==211)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_5.tif", "(im1b1==45 || im1b1==46)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_6.tif", "(im1b1==221 || im1b1==222)?im1b1:0",2,8)
    
    #masques restant pour faire la fusion des images apres
    osof.otb_bandmath_1(raster, path+"/mask_7.tif", "(im1b1==44)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_8.tif", "(im1b1==51)?im1b1:0",2,8)
    osof.otb_bandmath_1(raster, path+"/mask_9.tif", "(im1b1==53)?im1b1:0",2,8)  
    
    for i in range(9):        
        command = "gdalwarp -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_%s.tif %s/mask_nd_%s.tif"%(nbcores, path, str(i+1), path, str(i+1))
        os.system(command)
    
    for i in range(9):        
        os.remove(path+"/mask_%s.tif"%(i+1))
        
    for i in range(2):
        
        if i == 0:
            connexion = 8
        else :
            connexion = 4
            
        #nombre de tuiles à traiter en meme temps
        pool = Pool(processes=6)
        #nombre total de tuiles à traiter
        iterable = (np.arange(6)).tolist()
        #pour iterer sur la derniere tuile
        function = partial(gdal_sieve, threshold, connexion, path)
        pool.map(function, iterable)
        pool.close()
        pool.join()
    
        for j in range(6):
            command = "gdalwarp -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_%s_%s.tif %s/mask_nd_%s_%s.tif"%(nbcores, path, str(j+1), str(connexion), path, str(j+1), str(connexion))
            os.system(command)
        
        for j in range(6):
            os.remove(path+"/mask_%s_%s.tif"%(str(j+1),str(connexion)))
    
    for j in range(6):
        os.remove(path+"/mask_nd_%s_8.tif"%(str(j+1)))
        
    #fusion des rasters regularisee de maniere adaptative pour regularisation majoritaire
    osof.otb_bandmaths([path+"/mask_nd_1_4.tif",path+"/mask_nd_2_4.tif",path+"/mask_nd_3_4.tif",path+"/mask_nd_4_4.tif",\
    path+"/mask_nd_5_4.tif",path+"/mask_nd_6_4.tif",path+"/mask_nd_7.tif",path+"/mask_nd_8.tif",path+"/mask_nd_9.tif"],\
    path+"/mask_classification_regul_adaptative.tif", "im1b1+im2b1+im3b1+im4b1+im5b1+im6b1+im7b1+im8b1+im9b1",2, 8)
    
    for j in [path+"/mask_nd_1_4.tif",path+"/mask_nd_2_4.tif",path+"/mask_nd_3_4.tif",path+"/mask_nd_4_4.tif",\
    path+"/mask_nd_5_4.tif",path+"/mask_nd_6_4.tif",path+"/mask_nd_7.tif",path+"/mask_nd_8.tif",path+"/mask_nd_9.tif"]:
        os.remove(j)
        
    command = "gdalwarp -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_classification_regul_adaptative.tif %s/mask_nd_classification_regul_adaptative.tif"%(nbcores, path, path)
    os.system(command)
        
    #regularisation majoritaire
    print "Execution de gdal_sieve majoritaire"
    
    #effectue une premiere passe du masque en connectivite 8, puis en 4
    command = "gdal_sieve.py -8 -st %s %s/mask_nd_classification_regul_adaptative.tif %s/mask_classification_regul_adaptative_0.tif" %(threshold, path, path)
    os.system(command)
    
    command = "gdalwarp -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_classification_regul_adaptative_0.tif %s/mask_nd_classification_regul_adaptative_0.tif"%(nbcores, path, path)
    os.system(command)
    
    command = "gdal_sieve.py -4 -st %s %s/mask_nd_classification_regul_adaptative_0.tif %s/classification_regul_adaptative_majoritaire.tif" %(threshold, path, path)
    os.system(command)
    
    print "Export du raster"
    shutil.copy(path + "/mask_nd_classification_regul_adaptative_0.tif", out +"/classification_regul_adaptative_majoritaire_%s.tif"%(str(threshold)))
    
    out_classif_sieve = "%s/classification_regul_adaptative_majoritaire.tif"%(path)
        
    #supprime tous les fichiers intermediaires
    print "Suppression des fichiers intermediaire"
    #liste_effacer = glob.glob("mask*.tif")
    
    #for image_effacer in liste_effacer :
        #os.remove(image_effacer)
    
    for paths, dirs, fichiers in os.walk(path):
        for fichier in fichiers :
            if "mask" in fichier :
                os.remove(path +"/" +fichier)
            
    fin_regularisation = time.time() - debut_regularisation
    print "Temps total pour la regularisation :", fin_regularisation
    
    return out_classif_sieve, fin_regularisation

def gdal_sieve(threshold, connexion, path, i):
    
    print "Execution de gdal_sieve avec mask"
       
    #effectue une premiere passe du masque en connectivite 8, puis en 4
    if connexion == 8:
        command = "gdal_sieve.py -%s -st %s %s/mask_nd_%s.tif %s/mask_%s_8.tif" %(connexion,threshold, path, str(i+1), path, str(i+1))
        os.system(command)
        
    else :       
        command = "gdal_sieve.py -%s -st %s %s/mask_nd_%s_8.tif %s/mask_%s_4.tif" %(connexion, threshold, path, str(i+1), path, str(i+1))
        os.system(command)
        
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

        parser.add_argument("-p", dest="path", action="store", \
                            help="Input path where classification is located", required = True)
   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of classification", required = True)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-umc", dest="umc", action="store", \
                    help="Number of strippe for otb process", required = True)
                            
        parser.add_argument("-strippe", dest="ram", action="store", \
                            help="Number of strippe for otb process", required = True)
                            
        parser.add_argument("-tmp", dest="tmp", action="store", \
                            help="keep temporary files ? True or False") 
                                
    args = parser.parse_args()
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
    os.chdir(args.path)
    regularisation(args.classif, args.umc, args.core)
