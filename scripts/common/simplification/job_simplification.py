# -*- coding: utf-8 -*-
"""
Simplifie un raster en plusieurs etapes consecutives avec grass GIS : 
vectorisation, simplification, lissage, export au format shapefile.
"""

import shutil
import sys
import os
import time
import argparse
import OSO_functions as osof

#------------------------------------------------------------------------------
            
def init_grass(path, grasslib):

    """
    Initialisation of Grass GIS in lambert 93.
    
    in : 
        path : directory where create grassdata directory
        grasslib : install directory of Grass GIS
    """ 
    
    global gscript  
    
    #se place dans le repertoire courant pour créer le dossier grassdata     
    if not os.path.exists(path + "/grassdata"):
        os.mkdir(path + "/grassdata")
    path_grassdata = path +"/grassdata"
    print path_grassdata
    
    #initialise l'utilisation de grass dans un script python
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase
    
    #permet de relancer le script plusieurs fois en permettant d'ecraser les fichiers
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']='-1'
    
    #importe les fonctions grass
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    #initialise grass72 (important pour accelerer Simplification et lissage)
    gsetup.init(gisbase, gisdb)
    
    #supprime la location si elle existe deja
    if os.path.exists(gisdb + "/demolocation"):
        shutil.rmtree(gisdb + "/demolocation")
    
    #cree une nouvelle location nommee demolocation en lambert 93
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    #se place dans un mapset qui va contenir les donnees et le cree
    if not os.path.exists(gisdb + "/demolocation/datas") :
        gscript.run_command("g.mapset", flags="c", mapset = "datas", location="demolocation", dbase = gisdb)
        
def simplification(path, raster, douglas, hermite, angle, resample, tmp, grasslib, cluster, out, ngrid):
    """
        Simplification of raster dataset with Grass GIS.
        
        in :
            path : path where raster is located
            raster : raster name
            douglas : threshold of douglas simplification
            hermite : threshold of hermite smooth
            angle : Do a vectorisation with angles at 45 degrees ? True, False
            resample : Rasterize the shapefile simplified ? True, False
            tmp : Keep temporary files ? True, False
            grasslib : Path of folder with grass GIS install
            cluster : Do this step in command line ? True, False
            ngrid : tile number
            
        out : 
            shapefile with standart name ("tile_ngrid.shp")
    """
    timer = osof.Timer()
    debut_simplification = time.time()
    
    print "Initialisation de l'environnement GRASS\n"
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Initialisation de l'environnement GRASS\n")
        csvfile.close()
        
    if not cluster:
        path = path + "/" + str(ngrid) + "/outfiles"
        raster = raster + "/" + str(ngrid) + "/outfiles/tile_" + str(ngrid) + ".tif"
        init_grass(path, grasslib)
        os.chdir(path)
    else :
        init_grass(path, grasslib)
        os.chdir(path)
        
    if not os.path.exists(raster):
        print "Le fichier %s n'existe pas.Fin"%(os.path.basename(raster))
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("Le fichier %s n'existe pas.Fin"%(os.path.basename(raster)))
        csvfile.close()
        sys.exit()
    
    print "Import du raster\n"
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Import du raster\n")
        csvfile.close()
        
    #importe le raster regularise
    gscript.run_command("r.in.gdal", input=raster, output= "classification")
    
    #focalise la region sur le raster
    gscript.run_command("g.region", raster = "classification")
    
    #vectorisation
    print "Vectorisation de la tuile %s \n"%(ngrid)
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Vectorisation de la tuile %s \n"%(ngrid))
        csvfile.close()
    
    if str(angle)=="True":
        timer.start()
        #effectue une vectorisation en rognant les angles a 45 degres
        gscript.run_command("r.to.vect", flags="s", input="classification@datas", output="classification_vecteur", type="area")
        
    elif str(angle)=="False" :
        timer.start()
        #effectue une vectorisation sans l'angle a 45 degres
        gscript.run_command("r.to.vect", input="classification@datas", output="classification_vecteur", type="area")
        
    else :
        timer.start()
        #effectue une vectorisation et enregistre directement le resultat, sans simplification (produit respectant strictement le raster)
        gscript.run_command("r.to.vect", input="classification@datas", output="tile_%s"%(ngrid), type="area")
        
        timer.stop()
        time_vectorisation = timer.interval
        print "TEMPS : %s \n"%(round(time_vectorisation,2))
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "w") as csvfile :
            csvfile.write("TEMPS : %s secondes \n"%(round(time_vectorisation,2)))
            csvfile.close()
        
        timer.start()
        #suppression des entites nodata,mer/ocean et voisins
        print "Suppression des entites nodata, mer et voisins \n"
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("Suppression des entites nodata, mer et voisins \n")
            csvfile.close()
            
        gscript.run_command("v.edit", map="tile_%s"%(ngrid), tool = "delete", where="value > 250 or value < 1")
        
        timer.stop()
        time_delete = timer.interval
        print "TEMPS : %s \n"%(round(time_delete,2))
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("TEMPS : %s secondes \n"%(round(time_delete,2)))
            csvfile.close()
            
        timer.start()
        #exporte le vecteur selon le numero de la tuile traitee
        print "Export du fichier shapefile\n"
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("Export du fichier shapefile\n")
            csvfile.close()
            
        gscript.run_command("v.out.ogr", input="tile_%s@datas"%(ngrid), output=path+"/tile_%s"%(ngrid), format = "ESRI_Shapefile")
        
        timer.stop()
        time_export = timer.interval
        print "TEMPS : %s \n"%(round(time_export,2))
        with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("TEMPS : %s secondes \n"%(round(time_export,2)))
            csvfile.close()
        
        return "Fin de generation du produit fidele au raster"
        
    timer.stop()
    time_vectorisation = timer.interval
    print "TEMPS : %s secondes \n"%(time_vectorisation)
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
            csvfile.write("TEMPS : %s secondes \n"%(round(time_vectorisation,2)))
            csvfile.close()
    
    timer.start()        
    #simplification douglas
    print "Simplification Douglas de la tuile %s \n"%(ngrid)
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Simplification Douglas de la tuile %s \n"%(ngrid))
        csvfile.close()
        
    gscript.run_command("v.generalize", input="classification_vecteur@datas", method="douglas", threshold="%s"%(douglas), output="classification_vecteur_douglas")
    
    timer.stop()
    time_douglas = timer.interval
    print "TEMPS : %s secondes \n"%(round(time_douglas,2))
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes \n"%(round(time_douglas,2)))
        csvfile.close()
    
    timer.start()
    #simplification hermite
    print "Simplification Hermite de la tuile %s \n"%(ngrid)
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Simplification Hermite de la tuile %s \n"%(ngrid))
        csvfile.close()
        
    gscript.run_command("v.generalize", input="classification_vecteur_douglas@datas", method="hermite", threshold="%s"%(hermite), output="tile_%s"%(ngrid))
    
    timer.stop()
    time_hermite = timer.interval
    print "TEMPS : %s secondes \n"%(round(time_hermite,2))
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes \n"%(round(time_hermite,2)))
        csvfile.close()
    
    timer.start()
    #suppression des entites nodata et mer/ocean
    print "Suppression des entites nodata, mer et voisins \n"
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Suppression des entites nodata, mer et voisins \n")
        csvfile.close()
    
    gscript.run_command("v.edit", map="tile_%s"%(ngrid), tool = "delete", where="value > 250 or value < 1")
    
    timer.stop()
    time_delete = timer.interval
    print "TEMPS : %s \n"%(round(time_delete,2))
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes \n"%(round(time_delete,2)))
        csvfile.close()
    
    timer.start()
    #export de la classif simplifiee dans un dossier ayant pour nom le numero de tuile
    print "Export du fichier shapefile \n"
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Export du fichier shapefile\n")
        csvfile.close()
        
    gscript.run_command("v.out.ogr", input="tile_%s@datas"%(ngrid), output=path+"/tile_%s.shp"%(ngrid), format = "ESRI_Shapefile")
    
    timer.stop()
    time_export = timer.interval
    print "TEMPS : %s \n"%(round(time_export,2))
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("TEMPS : %s secondes \n"%(round(time_export,2)))
        csvfile.close()
        
    #rasterisation 20m du vecteur
    if str(resample) == "True" :
        command = "gdal_rasterize -a value -tr 20 20 %s %s" %(path+"/tile_"+str(ngrid)+".shp",path+"/tile_"+str(ngrid)+".tif")
        os.system(command)

    time_simplification = time.time() - debut_simplification
            
    print "Temps de traitement total : %s \n"%(round(time_simplification,2))
    with open(args.path+"/log_jobs_simplification_%s.csv"%(ngrid), "a") as csvfile :
        csvfile.write("Temps de traitement total : %s secondes \n"%(round(time_simplification,2)))
        csvfile.close()
        
    if not tmp :
        shutil.rmtree(path+"/grassdata")   
    
    if str(cluster) == "False":
        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(path + "/tile_%s.%s"%(ngrid, ext)):
                shutil.copy(path + "/tile_%s.%s"%(ngrid, ext), out + "/"+ str(ngrid) + "/outfiles/tile_%s.%s"%(ngrid, ext))
                
    return "Fin de la simplification"
    
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
                            help="Input path of tile directory", required = True)
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)
                            
        parser.add_argument("-in", dest="raster", action="store", \
                            help="tile raster from job_tif", required = True)
                            
        parser.add_argument("-ngrid", dest="ngrid", action="store", \
                            help="ngrid value", required = True)     
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder", required = True)  
                            
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="douglas value", required = True)   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="hermite value", required = True)   
                            
        parser.add_argument("-angle", dest="angle", action="store", \
                            help="angle 45 or not ? True, False, rien", required = True)   
            
        parser.add_argument("-resample", dest="resample", action="store", \
                            help="resample vector ? True, False", required = True)   
                            
        parser.add_argument("-tmp", action="store_true", \
                            help="keep temporary files ?", default = False) 
                            
        parser.add_argument("-cluster", action="store_true", \
                            help="If True, don't pool simplification phase", default = False) 
                                
    args = parser.parse_args()
    
    #initialise un fichier log de serialisation tif
    with open(args.path+"/log_jobs_simplification_%s.csv"%(args.ngrid), "w") as csvfile :
        csvfile.close()
    
    simplification(args.path, args.raster, args.douglas, args.hermite, args.angle, args.resample, args.tmp, args.grass, args.cluster, args.out, args.ngrid)
    
    for ext in ["shp","shx","dbf","prj"] :
        if os.path.exists(args.path + "/tile_%s.%s"%(args.ngrid, ext)):
            shutil.copy(args.path + "/tile_%s.%s"%(args.ngrid, ext), args.out + "/"+ str(args.ngrid) + "/outfiles" +"/tile_%s.%s"%(args.ngrid, ext))
    
    if os.path.exists(args.path+"/log_jobs_simplification_%s.csv"%(args.ngrid)):
        shutil.copy(args.path+"/log_jobs_simplification_%s.csv"%(args.ngrid), args.out + "/"+ str(args.ngrid) + "/outfiles" +"/log_jobs_simplification_%s.csv"%(args.ngrid))