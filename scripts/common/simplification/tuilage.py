# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 17:04:08 2017

@author: donatien
"""
import os
import sys
import multiprocessing
import shutil
import numpy as np
import argparse
from multiprocessing import Pool
from functools import partial

import regularisation
import serialisation_otb
import clump
import grass_simplification

def parallelisation(inpath, grasslib, ram, log, douglas, hermite, resample, angle, ngrid) :
    
    #creation du repertoire de la tuile
    os.mkdir(inpath+"/"+str(ngrid))
    
    #creation du repertoire grass dans le dossier de la tuile    
    grass_simplification.init_grass(inpath+"/"+str(ngrid), grasslib)
    
    #cree repertoire où enregistrer les donnees
    os.mkdir(inpath+"/"+str(ngrid)+"/outfiles")
    
    #se place dans le dossier de la tuile
    os.chdir(inpath+"/"+str(ngrid))
    
    #Serialisation de la simplification 
    serialisation_otb.serialisation_grille(inpath, inpath+"/classification.tif", ram, ngrid, log, "outfiles", douglas, hermite, resample, angle)
    
def tuilage(raster):
    datas,xsize,ysize,projection,transform,raster_band = serialisation_otb.raster_open(classif_regularisee)
    #generation de la grille de serialisation
    serialisation_otb.grid_generate("grille.shp",transform[0],(transform[0] + transform[1] * xsize), (transform[3] + transform[5] * ysize),transform[3],ysize*int(args.xytile),xsize*int(args.xytile))
    grid_open = serialisation_otb.shape_open("grille.shp",0)
    grid_layer = grid_open.GetLayer()
    nbtiles = grid_layer.GetFeatureCount()

    #serialisation et parallelisation des tuiles
    #si on traite toutes les tuiles        
    if args.ngrid == None :
        #nombre de tuiles à traiter en meme temps
        pool = Pool(processes=int(args.nbprocess))
        #nombre total de tuiles à traiter
        iterable = (np.arange(nbtiles)).tolist()
        #pour iterer sur la derniere tuile
        #iterable.append(nbtiles)
        function = partial(main, args.path, args.grass, args.ram, args.log, args.douglas, args.hermite, args.resample, args.angle)
        pool.map(function, iterable)
        pool.close()
        pool.join()