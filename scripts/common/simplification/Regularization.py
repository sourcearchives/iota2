#!/usr/bin/python
#-*- coding: utf-8 -*-

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
Make OSO map regularization (10 m regularization, 10 m to 20 m resampling, 20 m regularization, inland and sea water differentiation)
"""

import sys, os, argparse
import shutil
import time
import numpy as np
import AdaptRegul

try:
    import otbAppli
except ImportError:
    raise ImportError('Iota2 not well configured / installed')
    
#------------------------------------------------------------------------------

def rastToVectRecode(path, classif, vector, outputName, ram = "10000", dtype = "uint8"):
    
    # empty raster
    bandMathAppli = otbAppli.CreateBandMathApplication(classif, 'im1b1*0', ram, dtype, os.path.join(path, 'temp.tif'))
    bandMathAppli.ExecuteAndWriteOutput()
            
    # rasterize with value 1 to no water (data.gouv, france openstreetmap, 5m, 2014)
    command = "gdal_rasterize -q -burn 1 %s %s"%(vector, os.path.join(path, 'temp.tif'))
    os.system(command)
                
    # Differenciate inland water and sea water
    bandMathAppli = otbAppli.CreateBandMathApplication([classif, os.path.join(path, 'temp.tif')], \
                                                       "(im1b1==51) && (im2b1==0)?255:im1b1", \
                                                       ram, dtype, outputName)
    bandMathAppli.ExecuteAndWriteOutput()
    
    return outputName

def OSORegularization(classif, umc1, core, path, output, ram = "10000", noSeaVector = None, rssize = None, umc2 = None):
    
    # OTB Number of threads
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(core)

    # first regularization
    out = os.path.dirname(os.path.abspath(output))
    regulClassif, time_regularisation1 = AdaptRegul.regularisation(classif, umc1, core, path, out, ram)

    print " ".join([" : ".join(["First regularization", str(time_regularisation1)]), "seconds"])
    
    # second regularization
    if umc2 != None :
        if rssize != None :
            command = "gdalwarp -q -multi -wo NUM_THREADS=%s -r mode -tr %s %s %s %s/reechantillonnee.tif" %(core, \
                                                                                                          rssize, \
                                                                                                          rssize, \
                                                                                                          regulClassif, \
                                                                                                          path)
            os.system(command)
            regulClassif = os.path.join(path, "reechantillonnee.tif")
            print " ".join([" : ".join(["Resample", str(time.time() - time_regularisation1)]), "seconds"])
            

        regulClassif, time_regularisation2 = AdaptRegul.regularisation(regulClassif, umc2, core, path, out, ram)
        print " ".join([" : ".join(["Second regularization", str(time_regularisation2)]), "seconds"])
        
    if noSeaVector is not None:
        outfilename = os.path.basename(output)
        outfile = rastToVectRecode(path, regulClassif, noSeaVector, os.path.join(path, outfilename), ram, "uint8")

    shutil.copyfile(os.path.join(path, outfilename), output)
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regularization and resampling a classification raster")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)
                                   
        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of classification", required = True)
        
        parser.add_argument("-inland", dest="inland", action="store", \
                            help="inland water limit shapefile", required = False)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of CPU / Threads to use for OTB applications (ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS)", \
                            required = True)                                   
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="RAM for otb applications", default = "10000", required = False)
                            
        parser.add_argument("-umc1", dest="umc1", action="store", \
                            help="MMU for first regularization", required = True)
                                
        parser.add_argument("-umc2", dest="umc2", action="store", \
                            help="MMU for second regularization", required = False)
                        
        parser.add_argument("-rssize", dest="rssize", action="store", \
                            help="Pixel size for resampling", required = False)

        parser.add_argument("-outfile", dest="out", action="store", \
                            help="output file name", required = True)                                    
                            
        args = parser.parse_args()
        
        OSORegularization(args.classif, args.umc1, args.core, args.path, args.out, args.ram, args.inland, args.rssize, args.umc2)

        # python regularization.py -wd /home/thierionv/cluster/simplification/post-processing-oso/script_oso/wd -in /home/thierionv/cluster/simplification/post-processing-oso/script_oso/OSO_10m.tif -inland /home/thierionv/work_cluster/classifications/Simplification/masque_mer.shp -nbcore 4 -umc1 10 -umc2 3 - rssize 20 -outfile /home/thierionv/cluster/simplification/post-processing-oso/script_oso/out/classif_regul_20m.tif
        
        '''
                
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
        
        
        
            
        '''         
