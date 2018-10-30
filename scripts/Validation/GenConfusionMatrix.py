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

import argparse
import sys
import os
import shutil
import logging

from config import Config
from Common import FileUtils as fu
from osgeo import gdal
from osgeo.gdalconst import *
from Common import ServiceConfigFile as SCF
from Common.Utils import run


LOGGER = logging.getLogger(__name__)


def create_dummy_rasters(missing_tiles, N, cfg):
    """
    use when mode is 'one_region' but there is no validations / learning
    samples into a specific tile
    """
    #gdal_merge.py -n 0 -createonly -o Classif_T38JPT_model_1_seed_0_fake.tif Classif_T38JPT_model_1_seed_0.tif
    classifications_dir = os.path.join(cfg.getParam('chain', 'outputPath'), "classif")
    final_dir = os.path.join(cfg.getParam('chain', 'outputPath'), "final", "TMP")

    for tile in missing_tiles:
        classif_tile = fu.FileSearch_AND(classifications_dir, True, "Classif_" + str(tile))[0]
        for seed in range(N):
            dummy_raster_name = tile + "_seed_" + str(seed) + "_CompRef.tif"
            dummy_raster = final_dir + "/" + dummy_raster_name
            dummy_raster_cmd = "gdal_merge.py -ot Byte -n 0 -createonly -o " + dummy_raster + " " + classif_tile
            run(dummy_raster_cmd)

def compareRef(shapeRef, shapeLearn, classif, diff, footprint, workingDirectory, cfg, pathWd):

    minX, maxX, minY, maxY = fu.getRasterExtent(classif)
    shapeRaster_val = workingDirectory+"/"+shapeRef.split("/")[-1].replace(".shp", ".tif")
    shapeRaster_learn = workingDirectory+"/"+shapeLearn.split("/")[-1].replace(".shp", ".tif")

    dataField = cfg.getParam('chain', 'dataField')
    spatialRes = int(cfg.getParam('chain', 'spatialResolution'))

    #Rasterise val
    cmd = "gdal_rasterize -a "+dataField+" -init 0 -tr "+str(spatialRes)+" "+str(spatialRes)+" "+shapeRef+" "+shapeRaster_val+" -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)
    run(cmd)
    #Rasterise learn
    cmd = "gdal_rasterize -a "+dataField+" -init 0 -tr "+str(spatialRes)+" "+str(spatialRes)+" "+shapeLearn+" "+shapeRaster_learn+" -te "+str(minX)+" "+str(minY)+" "+str(maxX)+" "+str(maxY)
    run(cmd)

    #diff val
    diff_val = workingDirectory+"/"+diff.split("/")[-1].replace(".tif", "_val.tif")
    cmd_val = 'otbcli_BandMath -il '+shapeRaster_val+' '+classif+' -out '+diff_val+' uint8 -exp "im1b1==0?0:im1b1==im2b1?2:1"'#reference identique -> 2  | reference != -> 1 | pas de reference -> 0
    run(cmd_val)
    os.remove(shapeRaster_val)

    #diff learn
    diff_learn = workingDirectory+"/"+diff.split("/")[-1].replace(".tif", "_learn.tif")
    cmd_learn = 'otbcli_BandMath -il '+shapeRaster_learn+' '+classif+' -out '+diff_learn+' uint8 -exp "im1b1==0?0:im1b1==im2b1?4:3"'#reference identique -> 4  | reference != -> 3 | pas de reference -> 0
    run(cmd_learn)
    os.remove(shapeRaster_learn)

    #sum diff val + learn
    diff_tmp = workingDirectory+"/"+diff.split("/")[-1]
    cmd_sum = 'otbcli_BandMath -il '+diff_val+' '+diff_learn+' -out '+diff_tmp+' uint8 -exp "im1b1+im2b1"'
    run(cmd_sum)
    os.remove(diff_val)
    os.remove(diff_learn)

    if pathWd and not os.path.exists(diff):
        shutil.copy(diff_tmp, diff)
        os.remove(diff_tmp)

    return diff

def genConfMatrix(pathClassif, pathValid, N, dataField, pathToCmdConfusion,
                  cfg, pathWd):
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    AllCmd = []
    pathTMP = pathClassif+"/TMP"

    pathTest = cfg.getParam('chain', 'outputPath')
    spatialRes = cfg.getParam('chain', 'spatialResolution')
    enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')

    workingDirectory = pathClassif+"/TMP"
    if pathWd:
        workingDirectory = pathWd

    AllTiles = []
    validationFiles = fu.FileSearch_AND(pathValid, True, "_val.sqlite")
    for valid in validationFiles:
        currentTile = valid.split("/")[-1].split("_")[0]
        try:
            ind = AllTiles.index(currentTile)
        except ValueError:
            AllTiles.append(currentTile)

    for seed in range(N):
        #recherche de tout les shapeFiles par seed, par tuiles pour les fusionner
        for tile in AllTiles:
            seed_val = seed
            if enableCrossValidation:
                seed_val = N
            valTile = fu.FileSearch_AND(pathValid, True, tile, "_seed_"+str(seed_val)+"_val.sqlite")[0]
            learnTile = fu.FileSearch_AND(pathValid, True, tile, "_seed_"+str(seed)+"_learn.sqlite")[0]
            pathDirectory = pathTMP
            cmd = 'otbcli_ComputeConfusionMatrix -in {}/Classif_Seed_{}.tif -out {}/{}_seed_{}.csv -ref.vector.field {} -ref vector -ref.vector.in {}'.format(
                pathClassif, seed, pathDirectory, tile, seed, dataField.lower(), valTile)
            AllCmd.append(cmd)
            classif = pathTMP+"/"+tile+"_seed_"+str(seed)+".tif"
            diff = pathTMP+"/"+tile+"_seed_"+str(seed)+"_CompRef.tif"
            footprint = pathTest+"/final/Classif_Seed_0.tif"
            compareRef(valTile,
                       learnTile,
                       classif, diff, footprint, workingDirectory, cfg, pathWd)

    fu.writeCmds(pathToCmdConfusion+"/confusion.txt", AllCmd)

    for seed in range(N):
        AllDiff = fu.FileSearch_AND(pathTMP, True, "_seed_"+str(seed)+"_CompRef.tif")
        diff_seed = pathTest+"/final/diff_seed_"+str(seed)+".tif"
        if pathWd:
            diff_seed = workingDirectory+"/diff_seed_"+str(seed)+".tif"
        fu.assembleTile_Merge(AllDiff, spatialRes, diff_seed, ot="Byte")
        if pathWd:
            shutil.copy(workingDirectory+"/diff_seed_"+str(seed)+".tif", pathTest+"/final/diff_seed_"+str(seed)+".tif")

    #Create dummy rasters if necessary
    tile_asked = cfg.getParam('chain', 'listTile').split()
    missing_tiles = [elem for elem in tile_asked if elem not in AllTiles]
    create_dummy_rasters(missing_tiles, N, cfg)

    return(AllCmd)


def confusion_sar_optical_parameter(iota2_dir, LOGGER=LOGGER):
    """
    return a list of tuple containing the classification and the associated
    shapeFile to compute a confusion matrix
    """
    ref_vectors_dir = os.path.join(iota2_dir, "dataAppVal", "bymodels")
    classifications_dir = os.path.join(iota2_dir, "classif")

    vector_seed_pos = 4
    vector_tile_pos = 0
    vector_model_pos = 2
    classif_seed_pos = 5
    classif_tile_pos = 1
    classif_model_pos = 3

    vectors = fu.FileSearch_AND(ref_vectors_dir, True, ".shp")
    classifications = fu.FileSearch_AND(classifications_dir, True, "Classif", "model", "seed", ".tif")

    group = []
    for vector in vectors:
        vec_name = os.path.basename(vector)
        seed = vec_name.split("_")[vector_seed_pos]
        tile = vec_name.split("_")[vector_tile_pos]
        model = vec_name.split("_")[vector_model_pos]
        key = (seed, tile, model)
        fields = fu.getAllFieldsInShape(vector)
        if len(fu.getFieldElement(vector, driverName="ESRI Shapefile", field=fields[0], mode="all", elemType="str")):
            group.append((key, vector))
    for classif in classifications:
        classif_name = os.path.basename(classif)
        seed = classif_name.split("_")[classif_seed_pos].split(".tif")[0]
        tile = classif_name.split("_")[classif_tile_pos]
        model = classif_name.split("_")[classif_model_pos]
        key = (seed, tile, model)
        group.append((key, classif))
    # group by keys
    groups_param = [param for key, param in fu.sortByFirstElem(group)]

    # check if all parameter to find are found.
    for group in groups_param:
        if len(group) != 3:
            err_message = "ERROR : all parameter to use Dempster-Shafer fusion, not found"
            LOGGER.error(err_message)
            raise Exception(err_message)

    # output
    output_parameters = []
    for param in groups_param:
        for sub_param in param:
            if ".shp" in sub_param:
                ref_vector = sub_param
            elif "SAR.tif" in sub_param:
                classif_sar = sub_param
            elif ".tif" in sub_param and not "SAR.tif" in sub_param:
                classif_opt = sub_param
        output_parameters.append((ref_vector, classif_opt))
        output_parameters.append((ref_vector, classif_sar))

    return output_parameters


def confusion_sar_optical(ref_vector, dataField, ram=128, LOGGER=LOGGER):
    """
    function use to compute a confusion matrix dedicated to the D-S classification
    fusion.

    Parameter
    ---------
    ref_vector : tuple
        tuple containing (reference vector, classification raster)
    dataField : string
        labels fields in reference vector
    ram : int
        ram dedicated to produce the confusion matrix (OTB's pipeline size)
    LOGGER : logging
        root logger
    """
    from Common import OtbAppBank
    
    ref_vector, classification = ref_vector
    csv_out = ref_vector.replace(".shp", ".csv")
    if "SAR.tif" in classification:
        csv_out = csv_out.replace(".csv", "_SAR.csv")
    if os.path.exists(csv_out):
        os.remove(csv_out)

    confusion_parameters = {"in": classification,
                            "out": csv_out,
                            "ref": "vector",
                            "ref.vector.in": ref_vector,
                            "ref.vector.field": dataField.lower(),
                            "ram": str(0.8 * ram)}

    confusion_matrix = OtbAppBank.CreateComputeConfusionMatrixApplication(confusion_parameters)

    LOGGER.info("Launch : {}".format(csv_out))
    confusion_matrix.ExecuteAndWriteOutput()
    LOGGER.debug("{} done".format(csv_out))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="this function create a confusion matrix")
    parser.add_argument("-path.classif", help="path to the folder which contains classification images (mandatory)", dest="pathClassif", required=True)
    parser.add_argument("-path.valid", help="path to the folder which contains validation samples (with priority) (mandatory)", dest="pathValid", required=True)
    parser.add_argument("-N", dest="N", help="number of random sample(mandatory)", required=True, type=int)
    parser.add_argument("-data.field", dest="dataField", help="data's field into data shape (mandatory)", required=True)
    parser.add_argument("-confusion.out.cmd", dest="pathToCmdConfusion", help="path where all confusion cmd will be stored in a text file(mandatory)", required=True)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file which describe the classification (mandatory)", dest="pathConf", required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    genConfMatrix(args.pathClassif, args.pathValid, args.N, args.dataField,
                  args.pathToCmdConfusion, cfg, args.pathWd)
