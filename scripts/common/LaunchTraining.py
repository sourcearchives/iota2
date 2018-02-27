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

import argparse,os
from config import Config
import fileUtils as fu
from osgeo import ogr
import numpy as np

def getStatsFromSamples(InSamples):

    """
        IN:
            InSamples [string] : path to a sqlite file containing N fields value_0 .... value_N-1 representing features values
        OUT:
            allMean [list of float] : all mean sort by band number
            allStdDev [list of float] : all stdDev sort by band number
    """
    driver = ogr.GetDriverByName("SQLite")
    if driver.Open(InSamples, 0):
        ds = driver.Open(InSamples, 0)
    else:
        raise Exception("Can not open : "+InSamples)

    layer = ds.GetLayer()
    featuresFields = fu.getVectorFeatures(InSamples)
    allStat=[]
    for currentBand in featuresFields:
        bandValues = []
        for feature in layer:
            val = feature.GetField(currentBand)
            if isinstance( val, int ) or isinstance( val, float ):
                bandValues.append(val)
        bandValues = np.asarray(bandValues)
        mean = np.mean(bandValues)
        stddev = np.std(bandValues)
        allStat.append((mean,stddev))
    allMean = [mean for mean,stddev in allStat]
    allStdDev = [stddev for mean,stddev in allStat]
    return allMean, allStdDev

def writeStatsFromSample(InSamples,outStats):

    allMean,allStdDev = getStatsFromSamples(InSamples)

    with open(outStats,"w") as statsFile:
        statsFile.write('<?xml version="1.0" ?>\n\
            <FeatureStatistics>\n\
            <Statistic name="mean">\n')
        for currentMean in allMean:
            statsFile.write('        <StatisticVector value="'+str(currentMean)+'" />\n')
        statsFile.write('    </Statistic>\n\
                            <Statistic name="stddev">\n')
        for currentStd in allStdDev:
            statsFile.write('        <StatisticVector value="'+str(currentStd)+'" />\n')
        statsFile.write('    </Statistic>\n\
                            </FeatureStatistics>')

def writeConfigName(r,tileList,configfile):
    configModel = open(configfile,"a")
    configModel.write("\n\t{\n\tmodelName:'"+r+"'\n\ttilesList:'"+tileList+"'\n\t}")
    configModel.close()

def buildTrainCmd_points(r,paths,classif,options,dataField,out,seed,stat,pathlog,shape_ref):

    """
    shape_ref [param] [string] path to a shape use to determine how many fields
                               are already present before adding features
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd "
    if paths.count("learn")!=0:
        cmd = cmd +" "+paths 

    cmd = cmd+" -classifier "+classif+" "+options+" -cfield "+dataField.lower()+" -io.out "+out+"/model_"+str(r)+"_seed_"+str(seed)+".txt"
    
    nb_origin_fields = len(fu.getAllFieldsInShape(shape_ref))+1
    features_labels = " ".join(fu.getAllFieldsInShape(paths,"SQLite")[nb_origin_fields:])
    cmd = cmd+" -feat "+features_labels

    if ("svm" in classif):
        cmd = cmd+" -io.stats "+stat+"/Model_"+str(r)+".xml"

    if pathlog != None:
        cmd = cmd+" > "+pathlog+"/LOG_model_"+str(r)+"_seed_"+str(seed)+".out"
    return cmd

def buildTrainCmd_poly(r,paths,pathToTiles,Stack_ind,classif,options,dataField,out,seed,stat,pathlog):

    cmd = "otbcli_TrainImagesClassifier -io.il "
    for path in paths:
        if path.count("learn")!=0:
            tile = path.split("/")[-1].split("_")[0]
            pathToFeat = pathToTiles+"/"+tile+"/Final/"+Stack_ind
            cmd = cmd+pathToFeat+" "

    cmd = cmd+"-io.vd"
    for path in paths:
        if path.count("learn")!=0:
            cmd = cmd +" "+path

    cmd = cmd+" -classifier "+classif+" "+options+" -sample.vfn "+dataField
    cmd = cmd+" -io.out "+out+"/model_"+str(r)+"_seed_"+str(seed)+".txt"

    if ("svm" in classif):
        cmd = cmd + " -io.imstat "+stat+"/Model_"+str(r)+".xml"

    if pathlog != None:
        cmd = cmd +" > "+pathlog+"/LOG_model_"+str(r)+"_seed_"+str(seed)+".out"
    return cmd


def models_in_tiles(vectors):
    """
    usage : use to kwow in which tile models are present
    """
    
    #const
    #model's position, if training shape is split by "_"
    posModel = -3
    
    output = "AllModel:\n["
    for vector in vectors:
        model = os.path.split(vector)[-1].split("_")[posModel]
        tiles = fu.getFieldElement(vector, driverName="SQLite", field="tile_o",
                                   mode="unique", elemType="str")
        
        tmp = "modelName: '{}'\n\ttilesList: '{}'".format(model, "_".join(tiles))
        output += "\n\t{\n\t" + tmp + "\n\t}\n\t"
    output+="\n]"
    return output


def config_model(outputPath):
    """
    usage deternmine which model will class which tile
    """
    #const
    region_field = "region"
    region_split_field = "DN"
    output = None
    posTile = 0
    formatting_vec_dir = os.path.join(outputPath, "formattingVectors")
    samples = fu.FileSearch_AND(formatting_vec_dir,True, "seed_0", ".shp")
    
    #init
    all_regions = []
    for sample in samples:
        tile_name = os.path.splitext(os.path.basename(sample))[0].split("_")[posTile]
        regions = fu.getFieldElement(sample, driverName="ESRI Shapefile", field=region_field, mode="unique",
                                     elemType="str")
        for region in regions:
            all_regions.append((region, tile_name))

    #{'model_name':[TileName, TileName...],'...':...,...}
    model_tiles = dict(fu.sortByFirstElem(all_regions))
    
    #add tiles if they are missing by checking in /shapeRegion/ directory
    shape_region_dir = os.path.join(outputPath, "shapeRegion")
    shape_region_path = fu.FileSearch_AND(shape_region_dir,True, ".shp")
    
    #check if there is actually polygons
    shape_regions = [elem for elem in shape_region_path if len(fu.getFieldElement(elem,
                                                                                  driverName="ESRI Shapefile",
                                                                                  field=region_split_field,
                                                                                  mode="all",
                                                                                  elemType="str"))>=1]
    for shape_region in shape_regions:
        tile = os.path.splitext(os.path.basename(shape_region))[0].split("_")[-1]
        region = os.path.splitext(os.path.basename(shape_region))[0].split("_")[-2]
        for model_name, tiles_model in model_tiles.items():
            if model_name.split("f")[0] == region and not tile in tiles_model:
                tiles_model.append(tile)
    
    #Construct output file string
    output = "AllModel:\n["
    for model_name, tiles_model in model_tiles.items():
        output_tmp = "\n\tmodelName:'{}'\n\ttilesList:'{}'".format(model_name, "_".join(tiles_model))
        output = output + "\n\t{" + output_tmp + "\n\t}"
    output += "\n]"

    return output


def launchTraining(pathShapes, cfg, pathToTiles, dataField, stat, N, 
                   pathToCmdTrain, out, pathWd, pathlog):

    """
    OUT : les commandes pour l'app
    """
    cmd_out = []

    pathConf = cfg.pathConf
    classif = cfg.getParam('argTrain', 'classifier')
    options = cfg.getParam('argTrain', 'options')
    outputPath = cfg.getParam('chain', 'outputPath')
    samplesMode = cfg.getParam('argTrain', 'shapeMode')
    dataField = cfg.getParam('chain', 'dataField')
    
    shape_ref = fu.FileSearch_AND(os.path.join(outputPath,"formattingVectors"), True, ".shp")[0]
    posModel = -3 #model's position, if training shape is split by "_"

    pathToModelConfig = outputPath+"/config_model/configModel.cfg"

    if not os.path.exists(pathToModelConfig):
        tiles_model = config_model(outputPath)
        with open(pathToModelConfig, "w") as pathToModelConfig_file:
            pathToModelConfig_file.write(tiles_model)

    for seed in range(N):
        pathAppVal = fu.FileSearch_AND(pathShapes,True,"seed"+str(seed),".shp","learn")
        sort = [(path.split("/")[-1].split("_")[posModel],path) for path in pathAppVal]
        sort = fu.sortByFirstElem(sort)
        #get tiles by model
        names = []
        for r,paths in sort:
            tmp = ""
            for i in range(len(paths)):
                if i <len(paths)-1:
                    tmp = tmp+paths[i].split("/")[-1].split("_")[0]+"_"
                else :
                    tmp = tmp+paths[i].split("/")[-1].split("_")[0]
            names.append(tmp)
        cpt = 0
        for r,paths in sort:
            writeConfigName(r,names[cpt],pathToModelConfig)
            cpt+=1
        if samplesMode == "points":
            pathAppVal = fu.FileSearch_AND(outputPath+"/learningSamples",True,"seed"+str(seed),".sqlite","learn")
            sort = [(path.split("/")[-1].split("_")[posModel],path) for path in pathAppVal]

        for r,paths in sort:
            print r
            if samplesMode != "points":
                cmd = buildTrainCmd_poly(r,paths,pathToTiles,Stack_ind,classif,options,dataField,out,seed,stat,pathlog)
            else:
                if classif == "svm":
                    outStats = outputPath+"/stats/Model_"+r+".xml"
                    if os.path.exists(outStats):
                        os.remove(outStats)
                    writeStatsFromSample(paths,outStats)
                cmd = buildTrainCmd_points(r,paths,classif,options,dataField,out,seed,stat,pathlog,shape_ref)
            cmd_out.append(cmd)

    fu.writeCmds(pathToCmdTrain+"/train.txt",cmd_out)

    return cmd_out

if __name__ == "__main__":
    
    import serviceConfigFile as SCF

    parser = argparse.ArgumentParser(description = "This function allow you to create a training command for a classifieur according to a configuration file")
    parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
    parser.add_argument("-conf",help ="path to the configuration file which describe the learning method (mandatory)",dest = "pathConf",required=True)
    parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
    parser.add_argument("-data.field",dest = "dataField",help ="data field into data shape (mandatory)",required=True)
    parser.add_argument("-N",dest = "N",type = int,help ="number of random sample(mandatory)",required=True)
    parser.add_argument("--stat",dest = "stat",help ="statistics for classification",required=False)
    parser.add_argument("-train.out.cmd",dest = "pathToCmdTrain",help ="path where all training cmd will be stored in a text file(mandatory)",required=True)
    parser.add_argument("-out",dest = "out",help ="path where all models will be stored(mandatory)",required=True)
    parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
    parser.add_argument("--path.log",dest = "pathlog",help ="path to the log file",default=None,required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)
    
    launchTraining(args.pathShapes, cfg, args.pathToTiles, args.dataField, 
                   args.stat, args.N, args.pathToCmdTrain, args.out,
                   args.pathWd, args.pathlog)
