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
Adaptative and majority voting regularization process based on landscape rules

"""

import sys, os, argparse, time, shutil
import numpy as np
from multiprocessing import Pool
from functools import partial
try:
    from Common import OtbAppBank
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

#------------------------------------------------------------------------------
            
def regularisation(raster, threshold, nbcores, path, out, ram):
              
    #First regularisation in connection 8, second in connection 4
    print "Image to treated : \n",raster
    debut_regularisation = time.time()    
    
    # A mask for each regularization rule    
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==11 || im1b1==12)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_1.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==31 || im1b1==32)?im1b1:0', 
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_2.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==41 || im1b1==42 || im1b1==43)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_3.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==34 || im1b1==36 || im1b1==211)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_4.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==45 || im1b1==46)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_5.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==221 || im1b1==222)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_6.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==44)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_7.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==51)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_8.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                        "exp": '(im1b1==53)?im1b1:0',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_9.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
    
    for i in range(9):        
        command = "gdalwarp -q -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_%s.tif %s/mask_nd_%s.tif"%(nbcores, \
                                                                                                         path, \
                                                                                                         str(i + 1), \
                                                                                                         path, \
                                                                                                         str(i + 1))
        os.system(command)
    
    for i in range(9):        
        os.remove(path + "/mask_%s.tif"%(i + 1))

    masktime = time.time()
    print " ".join([" : ".join(["Masks generation for adaptive rules", str(masktime - debut_regularisation)]), "seconds"])
    
    for i in range(2):
        
        if i == 0:
            connexion = 8
        else :
            connexion = 4
   
        #nombre de tuiles à traiter en meme temps
        pool = Pool(processes = 6)
        #nombre total de tuiles à traiter
        iterable = (np.arange(6)).tolist()
        #pour iterer sur la derniere tuile
        function = partial(gdal_sieve, threshold, connexion, path)
        pool.map(function, iterable)
        pool.close()
        pool.join()
    
        for j in range(6):
            command = "gdalwarp -q -multi -wo NUM_THREADS=%s -dstnodata 0 %s/mask_%s_%s.tif %s/mask_nd_%s_%s.tif"%(nbcores, \
                                                                                                                path, \
                                                                                                                str(j + 1), \
                                                                                                                str(connexion), \
                                                                                                                path, \
                                                                                                                str(j + 1), \
                                                                                                                str(connexion))
            os.system(command)
        
        for j in range(6):
            os.remove(path + "/mask_%s_%s.tif"%(str(j + 1),str(connexion)))
    
    for j in range(6):
        os.remove(path + "/mask_nd_%s_8.tif"%(str(j + 1)))
        
    adaptativetime = time.time()
    print " ".join([" : ".join(["Adaptative regularizations", str(adaptativetime - masktime)]), "seconds"])
    
    # fusion des rasters regularisee de maniere adaptative pour regularisation majoritaire
    rastersList = [os.path.join(path, "mask_nd_1_4.tif"), os.path.join(path, "mask_nd_2_4.tif"), os.path.join(path, "mask_nd_3_4.tif"), \
                   os.path.join(path, "mask_nd_4_4.tif"), os.path.join(path, "mask_nd_5_4.tif"), os.path.join(path, "mask_nd_6_4.tif"), \
                   os.path.join(path, "mask_nd_7.tif"), os.path.join(path, "mask_nd_8.tif"), os.path.join(path, "mask_nd_9.tif")]
    
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": rastersList,
                                                        "exp": 'im1b1+im2b1+\
                                                                im3b1+im4b1+\
                                                                im5b1+im6b1+\
                                                                im7b1+im8b1+\
                                                                im9b1',
                                                        "ram": ram,
                                                        "pixType": "uint8",
                                                        "out": os.path.join(path, 'mask_classification_regul_adaptative.tif')})
    bandMathAppli.ExecuteAndWriteOutput()
        
    for filemask in rastersList:
        os.remove(filemask)

    command = "gdalwarp -q -multi -wo NUM_THREADS="
    command += "%s -dstnodata 0 %s/mask_classification_regul_adaptative.tif %s/mask_nd_classification_regul_adaptative.tif"%(nbcores, \
                                                                                                                             path, \
                                                                                                                             path)
    os.system(command)

    #regularisation majoritaire
    
    #effectue une premiere passe du masque en connectivite 8, puis en 4
    command = "gdal_sieve.py -q -8 -st "
    command += "%s %s/mask_nd_classification_regul_adaptative.tif %s/mask_classification_regul_adaptative_0.tif" %(threshold, \
                                                                                                                   path, \
                                                                                                                   path)
    os.system(command)
    
    command = "gdalwarp -q -multi -wo NUM_THREADS="
    command += "%s -dstnodata 0 %s/mask_classification_regul_adaptative_0.tif %s/mask_nd_classification_regul_adaptative_0.tif"%(nbcores, \
                                                                                                                                 path, \
                                                                                                                                 path)
    os.system(command)
    
    command = "gdal_sieve.py -q -4 -st "
    command += "%s %s/mask_nd_classification_regul_adaptative_0.tif %s/classification_regul_adaptative_majoritaire.tif" %(threshold, \
                                                                                                                          path, \
                                                                                                                          path)
    os.system(command)
    
    #shutil.copy(path + "/mask_nd_classification_regul_adaptative_0.tif", out + "/classification_regul_adaptative_majoritaire_%s.tif"%(str(threshold)))
    
    out_classif_sieve = "%s/classification_regul_adaptative_majoritaire.tif"%(path)
        
    majoritytime = time.time()
    print " ".join([" : ".join(["Majority voting regularization", str(majoritytime - adaptativetime)]), "seconds"])
    
    for paths, dirs, files in os.walk(path):
        for fil in files :
            if "mask" in fil :
                os.remove(os.path.join(path, fil))
            
    fin_regularisation = time.time() - debut_regularisation
    
    return out_classif_sieve, fin_regularisation

def gdal_sieve(threshold, connexion, path, i):
       
    #effectue une premiere passe du masque en connectivite 8, puis en 4
    if connexion == 8:
        command = "gdal_sieve.py -q -%s -st %s %s/mask_nd_%s.tif %s/mask_%s_8.tif" %(connexion, threshold, path, str(i+1), path, str(i+1))
        os.system(command)
        
    else :       
        command = "gdal_sieve.py -q -%s -st %s %s/mask_nd_%s_8.tif %s/mask_%s_4.tif" %(connexion, threshold, path, str(i+1), path, str(i+1))
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
	parser = argparse.ArgumentParser(description = "Adaptative and majority voting regularization process based on landscape rules")

        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)
   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of classification", required = True)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-mmu", dest="mmu", action="store", \
                            help="Minimal mapping unit (in input classificaiton raster file unit)", required = True)
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb processes", required = True)
        
        parser.add_argument("-out", dest="out", action="store", \
                            help="Output path", required = True)                              
                                
    args = parser.parse_args()
    
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)

    regularisation(args.classif, args.mmu, args.core, args.path, args.out, args.ram)
    
