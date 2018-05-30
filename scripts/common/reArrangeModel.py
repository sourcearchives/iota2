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

import os
import argparse
from collections import Counter
from collections import defaultdict
from config import Config
from osgeo import ogr
from osgeo.gdalconst import *
import numpy as np
import fileUtils as fu
from Utils import run
from Common import ServiceConfigFile as SCF

def getSeconde(item):
    return item[1]

def getFirst(item):
    return item[0]


def repartitionInShape(listShapeModel, dataField, resol):

    """

    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    buff = []#[(class, Area)...]
    AllClass = []
    for shape in listShapeModel:
        dataSource = driver.Open(shape, 0)
        layer = dataSource.GetLayer()
        #get all class in the current shape
        for feature in layer:
            try:
                ind = AllClass.index(feature.GetField(dataField))
            except ValueError:
                AllClass.append(int(feature.GetField(dataField)))

    AllClass.sort()
    for currentClass in AllClass:
        buff.append([currentClass, 0.0])

    for shape in listShapeModel:
        dataSource = driver.Open(shape, 0)
        layer = dataSource.GetLayer()
        for feature in layer:
            feat = feature.GetField(dataField)
            geom = feature.GetGeometryRef()
            Area = geom.GetArea()
            try:
                ind = AllClass.index(feat)
                buff[ind][1] += float(Area)/float(resol)
            except ValueError:
                print "Problem in repartitionClassByTile"

    buff = sorted(buff, key=getSeconde)
    return buff


def generateRepartition(pathTest, cfg, rep_model, rep_model_repCore, dataField):

    shapeApp = pathTest+"/dataAppVal"
    regionTiles = pathTest+"/shapeRegion"

    seuilClass = 0.1 #seuil ?
    NbTuiles = 1 #Nb de tuiles dans lequel il est possible de venir piocher des polygones
    resol = 30*30

    N = cfg.getParam('chain', 'runs')
    Tiles = cfg.getParam('chain', 'listTile')
    AllTiles = Tiles.split(" ")

    #Récupération des modèles
    AllModel = []
    listModel = fu.FileSearch_AND(regionTiles, True, ".shp")
    for shape in listModel:
        model = shape.split("/")[-1].split("_")[-2]
        try:
            ind = AllModel.index(model)
        except ValueError:
            AllModel.append(model)

    #pour chaque model et chaque seed, regarder la répartition des classes
    repM = []#[(model, seed, [[class0, area0], [class1, area1]...]), (...)]
    repT = []#[(tile, seed, [[class0, area0], [class1, area1]...]), (...)]

    N = 1# <----------------------------------------------------------
    for seed in range(N):
        for model in AllModel:
            listShapeModel = fu.FileSearch_AND(shapeApp, True, "region_"+model, "seed"+str(seed)+"_learn.shp")
            modelRep = repartitionInShape(listShapeModel, dataField, resol)
            repM.append((model, seed, modelRep))
        for tile in AllTiles:
            listShapeModel = fu.FileSearch_AND(shapeApp, True, tile+"_region_", "seed"+str(seed)+"_learn.shp")
            tileRep = repartitionInShape(listShapeModel, dataField, resol)
            repT.append((tile, seed, tileRep))
        #compute all statistics by class for a given model
        listClassRep = []
        for m, seed, classRep in repM:
            for cl, rep in classRep:
                listClassRep.append([cl, rep])

        #Calcul de concentration des classes
        d = defaultdict(list)
        for k, v in listClassRep:
            d[k].append(v)
        rep_tmp = list(d.items())
        rep = []
        for cl, repModel in rep_tmp:
            rep.append((cl, np.asarray(repModel).mean()))
        repartition = sorted(rep, key=getSeconde)#rep = [(class, présenceMoyenne), ()...]

        #présence à l'équilibre d'une classe dans un modèle = présence moyenne dans rep
        less = []
        for m, seed, classRep in repM:
            for cl, rep in classRep:
                for cl_m, rep_m in repartition:
                    if cl == cl_m:
                        if rep < seuilClass*rep_m:
                            less.append((m, cl, rep))

        repCore = []
        corrections = []
        for m, cl, sample in less:
            for N in range(NbTuiles):
                maxS = 0
                cpti = 0
                for tile, seed, classRep in repT:
                    cptj = 0
                    for cl_t, rep_t in classRep:
                        if cl_t == cl and rep_t > maxS:
                            maxS = rep_t
                            tileMax = tile
                            repT[cpti][2][cptj][1] = 0
                        cptj += 1
                    cpti += 1

                repCore.append([int(m), tileMax])
                corrections.append([int(m), tileMax])

        #lecture du fichier de repartition des tuiles par modèles
        modelTile = []
        fileModel = open(rep_model, "r")
        regNumber = 0
        while 1:
            data = fileModel.readline().rstrip('\n\r')
            if data == "":
                break
            line = data.split(":")[-1]
            tiles = line.replace(" ", "").split(",")
            for tile_m in tiles:
                repCore.append([regNumber+1, tile_m])
                modelTile.append([tile_m, regNumber+1])
            regNumber += 1
        fileModel.close()

        d = defaultdict(list)
        for k, v in repCore:
            d[k].append(v)
        repCore = list(d.items())
        repCore = sorted(repCore, key=getFirst)

        #Création des shp de val/App
        for model_cor, tiles_cor in repCore:
            for tile_cor in tiles_cor:
                if not os.path.exists(shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_learn.shp"):
                    learnShp = fu.FileSearch_AND(shapeApp, True, tile, "seed"+str(seed)+"_learn.shp")
                    cmd1 = "cp "+learnShp[0]+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_learn.shp"
                    cmd2 = "cp "+learnShp[0].replace(".shp", ".shx")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_learn.shx"
                    cmd3 = "cp "+learnShp[0].replace(".shp", ".dbf")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_learn.dbf"
                    cmd4 = "cp "+learnShp[0].replace(".shp", ".prj")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_learn.prj"
                    cmd5 = "cp "+learnShp[0].replace("_learn.shp", "_val.shx")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_val.shp"
                    cmd6 = "cp "+learnShp[0].replace("_learn.shp", "_val.shx")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_val.shx"
                    cmd7 = "cp "+learnShp[0].replace("_learn.shp", "_val.dbf")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_val.dbf"
                    cmd8 = "cp "+learnShp[0].replace("_learn.shp", "_val.prj")+" "+shapeApp+"/"+tile+"_region_"+str(model_cor)+"_seed"+str(seed)+"_val.prj"

                    run(cmd1)
                    run(cmd2)
                    run(cmd3)
                    run(cmd4)
                    run(cmd5)
                    run(cmd6)
                    run(cmd7)
                    run(cmd8)

        #écriture du nouveau fichier
        corFile = open(rep_model_repCore, "w")
        for i in range(len(repCore)):
            corFile.write("m"+str(i+1)+" : ")
            for j in range(len(repCore[i][1])):
                if j < len(repCore[i][1])-1:
                    corFile.write(repCore[i][1][j]+",")
                else:
                    corFile.write(repCore[i][1][j]+"\n")
        corFile.close()

        #copie des shp (qui servent de mask pour la classification) de région/par tuiles
        for model_cor, tiles_cor in corrections:
            for tile_mt, mt in modelTile:
                if tile_mt == tiles_cor:
                    maskShp = fu.FileSearch_AND(regionTiles, True, str(mt)+"_"+tile_mt, ".shp")
                    fileName = maskShp[0].split("/")[-1].split(".")[0]
                    fileName_out = fileName.replace("region_"+str(mt)+"_", "region_"+str(model_cor)+"_")
                    cmd1 = "cp "+regionTiles+"/"+fileName+".shp "+regionTiles+"/"+fileName_out+".shp "
                    cmd2 = "cp "+regionTiles+"/"+fileName+".shx "+regionTiles+"/"+fileName_out+".shx "
                    cmd3 = "cp "+regionTiles+"/"+fileName+".dbf "+regionTiles+"/"+fileName_out+".dbf "
                    cmd4 = "cp "+regionTiles+"/"+fileName+".prj "+regionTiles+"/"+fileName_out+".prj "
            run(cmd1)
            run(cmd2)
            run(cmd3)
            run(cmd4)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function try to rearrange the repartition tile by model, considering class repartition")
    parser.add_argument("-path.test", dest="pathTest", help="one_region/multi_regions (mandatory)", required=True)
    parser.add_argument("-conf", help="path to the configuration file which describe the learning method (mandatory)", dest="config", required=True)
    parser.add_argument("-repartition.in", dest="rep_model", help="field out (mandatory)", required=True)
    parser.add_argument("-repartition.out", dest="rep_model_repCore", help="field out (mandatory)", required=True)
    parser.add_argument("-data.field", dest="dataField", help="data field into data shape (mandatory)", required=True)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.config)

    generateRepartition(args.pathTest, cfg, args.rep_model, args.rep_model_repCore, args.dataField)

