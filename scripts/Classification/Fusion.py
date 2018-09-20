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
import os
import shutil
import logging

from config import Config
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF

LOGGER = logging.getLogger(__name__)


def dempster_shafer_fusion_parameters(iota2_dir):
    """
    use to feed dempster_shafer_fusion function

    from the iota2 output directory, return parameter needed to compute
    a fusion of classifcations by dempster-shafer method

    Parameters
    ----------
    iota2_dir : string
        iota2 output directory

    Return
    ------
    list
        list of dict containing keys {"sar_classif", "opt_classif",
                                      "sar_model", "opt_model"}
    """
    classif_seed_pos = 5
    classif_tile_pos = 1
    classif_model_pos = 3

    iota2_ds_confusions_dir = os.path.join(iota2_dir, "dataAppVal", "bymodels")
    iota2_classif_dir = os.path.join(iota2_dir, "classif")
    classifications = fu.FileSearch_AND(iota2_classif_dir, True, "Classif", ".tif")
    # group by models
    model_group = []
    for classif in classifications:
        classif_name = os.path.basename(classif)
        classif_seed = classif_name.split("_")[classif_seed_pos].replace(".tif", "")
        classif_model = classif_name.split("_")[classif_model_pos]
        classif_tile = classif_name.split("_")[classif_tile_pos]
        key_param = (classif_seed, classif_model, classif_tile)
        model_group.append((key_param, classif))
    raster_group = [param for key, param in fu.sortByFirstElem(model_group)]

    out_parameters = []
    for raster_model in raster_group:
        for raster in raster_model:
            raster_name = os.path.basename(raster)
            classif_seed = raster_name.split("_")[classif_seed_pos].replace(".tif", "")
            classif_model = raster_name.split("_")[classif_model_pos]
            if "SAR.tif"  in raster_name:
                sar_model = fu.fileSearchRegEx(os.path.join(iota2_ds_confusions_dir, "model_{}_seed_{}_SAR.csv".format(classif_model, classif_seed)))[0]
                sar_classif = raster
            else:
                opt_model = fu.fileSearchRegEx(os.path.join(iota2_ds_confusions_dir, "model_{}_seed_{}.csv".format(classif_model, classif_seed)))[0]
                opt_classif = raster
        out_parameters.append({"sar_classif": sar_classif,
                               "opt_classif": opt_classif,
                               "sar_model": sar_model,
                               "opt_model": opt_model})
    return out_parameters


def perform_fusion(fusion_dic, mob, classif_model_pos, classif_tile_pos, classif_seed_pos,
                   workingDirectory, LOGGER=LOGGER):
    """
    from classifications, perform the DS fusion of classifications

    Parameters
    ----------
    fusion_dic : dict
        dictionnary containing keys : "sar_classif", "opt_classif", "sar_model"
        "opt_model"
    mob : string
        Dempster-Shafer's mass of belive
    classif_model_pos : int
        position of the model's name in classification's name if
        splited by '_'
    classif_tile_pos : int
        position of the tile's name in classification's name if
        splited by '_'
    classif_seed_pos : int
        position of the seed number in classification's name if
        splited by '_'
    workingDirectory : string
        path to a working directory

    Return
    ------
    string
        output path the the fusion of classifications
    """
    from Common import OtbAppBank

    model = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_model_pos]
    seed = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_seed_pos]
    tile = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_tile_pos]
    classif_dir, _ = os.path.split(fusion_dic["sar_classif"])

    sar_opt_fus_name = "Classif_{}_model_{}_seed_{}_DS.tif".format(tile,
                                                                   model,
                                                                   seed)
    sar_opt_fus = os.path.join(classif_dir, sar_opt_fus_name)
    if workingDirectory:
        sar_opt_fus = os.path.join(workingDirectory, sar_opt_fus_name)
    im_list = [fusion_dic["sar_classif"], fusion_dic["opt_classif"]]
    csv_list = [fusion_dic["sar_model"], fusion_dic["opt_model"]]
   
    fusion_parameters = {"il": im_list,
                         "method": "dempstershafer",
                         "method.dempstershafer.mob": mob,
                         "method.dempstershafer.cmfl": csv_list,
                         "out": sar_opt_fus}

    ds_fus = OtbAppBank.CreateFusionOfClassificationsApplication(fusion_parameters)
    if not os.path.exists(os.path.join(classif_dir, sar_opt_fus_name)):
        LOGGER.info("computing : {}".format(sar_opt_fus))
        ds_fus.ExecuteAndWriteOutput()
        LOGGER.debug("{} DONE".format(sar_opt_fus))
        if workingDirectory:
            shutil.copy(sar_opt_fus,
                        os.path.join(classif_dir, sar_opt_fus_name))
            os.remove(sar_opt_fus)
    return os.path.join(classif_dir, sar_opt_fus_name)


def compute_fusion_choice(iota2_dir, fusion_dic, fusion_class,
                          classif_model_pos, classif_tile_pos, classif_seed_pos,
                          ds_choice_both,
                          ds_choice_sar,
                          ds_choice_opt,
                          ds_no_choice,
                          workingDirectory, LOGGER=LOGGER):
    """
    using the resulting fusion of classification and originals classifications,
    generate a raster which determine which input was chosen

    Parameters
    ----------

    iota2_dir : string
        iota2's output path
    fusion_dic : dict
        dictionnary containing keys : "sar_classif", "opt_classif", "sar_model"
        "opt_model"
    fusion_class : string
        path to the fusion of classifications
    classif_model_pos : int
        position of the model's name in classification's name if
        splited by '_'
    classif_tile_pos : int
        position of the tile's name in classification's name if
        splited by '_'
    classif_seed_pos : int
        position of the seed number in classification's name if
        splited by '_'
    ds_choice_both : int
        output value if fusion of classifications get the same label than
        SAR classification and optical classification
    ds_choice_sar : int
        output value if fusion of classifications get the same label than
        SAR classification
    ds_choice_opt : int
        output value if fusion of classifications get the same label than
        optical classification
    ds_no_choice : int
        default case
    workingDirectory : string
        path to a working directory
    LOGGER : logging
        root logger
    Return
    ------
    string
        output path
    """
    from Common import OtbAppBank

    model = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_model_pos]
    seed = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_seed_pos]
    tile = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_tile_pos]
    im_list = [fusion_dic["sar_classif"], fusion_dic["opt_classif"], fusion_class]
    choice_exp = "im1b1==im3b1 and im2b1==im3b1?{ds_choice_both}:im1b1==im3b1?{ds_choice_sar}:im2b1==im3b1?{ds_choice_opt}:{ds_no_choice}".format(ds_choice_both=ds_choice_both,
                                                                                                                                                  ds_choice_sar=ds_choice_sar,
                                                                                                                                                  ds_choice_opt=ds_choice_opt,
                                                                                                                                                  ds_no_choice=ds_no_choice)
    ds_choice_name = "DSchoice_{}_model_{}_seed_{}.tif".format(tile,
                                                               model,
                                                               seed)
    ds_choice_dir = os.path.join(iota2_dir, "final", "TMP")
    if not os.path.exists(ds_choice_dir):
        try:
            os.mkdir(ds_choice_dir)
        except:
            pass
    ds_choice = os.path.join(ds_choice_dir, ds_choice_name)
    if workingDirectory:
        ds_choice = os.path.join(workingDirectory, ds_choice_name)
    ds_choice_params = {"il": im_list,
                        "out": ds_choice,
                        "exp": choice_exp,
                        "pixType": "uint8"}
    choice = OtbAppBank.CreateBandMathApplication(ds_choice_params)
    if not os.path.exists(os.path.join(ds_choice_dir,ds_choice_name)):
        LOGGER.info("computing : {}".format(ds_choice))
        choice.ExecuteAndWriteOutput()
        LOGGER.debug("{} : DONE".format(ds_choice))
        if workingDirectory:
            shutil.copy(ds_choice,
                        os.path.join(ds_choice_dir,ds_choice_name))
            os.remove(ds_choice)
    return os.path.join(ds_choice_dir,ds_choice_name)


def compute_confidence_fusion(fusion_dic, ds_choice,
                              classif_model_pos, classif_tile_pos, classif_seed_pos,
                              ds_choice_both,
                              ds_choice_sar,
                              ds_choice_opt,
                              ds_no_choice,
                              workingDirectory, LOGGER=LOGGER):
    """
    from the fusion of classification's raster choice compute the fusion of confidence map

    Parameters
    ----------

    fusion_dic : dict
        dictionnary containing keys : "sar_classif", "opt_classif", "sar_model"
        "opt_model"
    ds_choice : string
        path to the fusion of classifications choice map
    classif_model_pos : int
        position of the model's name in classification's name if
        splited by '_'
    classif_tile_pos : int
        position of the tile's name in classification's name if
        splited by '_'
    classif_seed_pos : int
        position of the seed number in classification's name if
        splited by '_'
    ds_choice_both : int
        output value if fusion of classifications get the same label than
        SAR classification and optical classification
    ds_choice_sar : int
        output value if fusion of classifications get the same label than
        SAR classification
    ds_choice_opt : int
        output value if fusion of classifications get the same label than
        optical classification
    ds_no_choice : int
        default case
    workingDirectory : string
        path to a working directory
    LOGGER : logging
        root logger

    Return
    ------
    string
        output path
    """
    from Common import OtbAppBank

    classif_dir, _ = os.path.split(fusion_dic["sar_classif"])
    model = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_model_pos]
    seed = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_seed_pos]
    tile = os.path.basename(fusion_dic["sar_classif"]).split("_")[classif_tile_pos]
    sar_confidence = fu.fileSearchRegEx(os.path.join(classif_dir, "{}_model_{}_confidence_seed_{}_SAR.tif".format(tile, model, seed)))[0]
    opt_confidence = fu.fileSearchRegEx(os.path.join(classif_dir, "{}_model_{}_confidence_seed_{}.tif".format(tile, model, seed)))[0]

    im_list = [ds_choice, sar_confidence, opt_confidence]
    confidence_exp = "im1b1=={ds_choice_both}?max(im2b1, im3b1):im1b1=={ds_choice_sar}?im2b1:im1b1=={ds_choice_opt}?im3b1:{ds_no_choice}".format(ds_choice_both=ds_choice_both,
                                                                                                                                                 ds_choice_sar=ds_choice_sar,
                                                                                                                                                 ds_choice_opt=ds_choice_opt,
                                                                                                                                                 ds_no_choice=ds_no_choice)
    ds_confidence_name = "{}_model_{}_confidence_seed_{}_DS.tif".format(tile, model, seed)
    ds_confidence_dir = classif_dir
    ds_confidence = os.path.join(ds_confidence_dir, ds_confidence_name)
    if workingDirectory:
        ds_confidence = os.path.join(workingDirectory, ds_confidence_name)
    confidence_param = {"il": im_list,
                        "out": ds_confidence,
                        "exp": confidence_exp}
    confidence = OtbAppBank.CreateBandMathApplication(confidence_param)

    if not os.path.exists(os.path.join(ds_confidence_dir, ds_confidence_name)):
        LOGGER.info("computing : {}".format(ds_confidence))
        confidence.ExecuteAndWriteOutput()
        LOGGER.debug("{} : DONE".format(ds_choice))
        if workingDirectory:
            # copy confidence
            shutil.copy(ds_confidence,
                        os.path.join(ds_confidence_dir, ds_confidence_name))
            # remove
            os.remove(ds_confidence)
    return os.path.join(ds_confidence_dir, ds_confidence_name)


def dempster_shafer_fusion(iota2_dir, fusion_dic, mob="precision",
                           workingDirectory=None):
    """
    perform a fusion of classifications thanks acording to Dempster-Shafer's method

    Parameters
    ----------
    iota2_dir : string
        iota2's output path
    fusion_dic : dict
        dictionnary containing keys : "sar_classif", "opt_classif", "sar_model"
        "opt_model"
    mob : string
        Dempster-Shafer's mass of belive
    workingDirectory : string
        path to a working directory

    Return
    ------
    list
        list containing : the Dempster-Shafer fusion labels path,
                              Dempster-Shafer fusion confidence path,
                              Dempster-Shafer fusion choice path
    """
    # const
    classif_seed_pos = 5
    classif_tile_pos = 1
    classif_model_pos = 3

    ds_choice_both = 1
    ds_choice_sar = 2
    ds_choice_opt = 3
    ds_no_choice = 0

    # fusion
    sar_opt_fus = perform_fusion(fusion_dic, mob,
                                 classif_model_pos, classif_tile_pos, classif_seed_pos,
                                 workingDirectory)

    # dempster-shafer raster choice
    ds_choice = compute_fusion_choice(iota2_dir, fusion_dic, sar_opt_fus,
                                      classif_model_pos, classif_tile_pos, classif_seed_pos,
                                      ds_choice_both,
                                      ds_choice_sar,
                                      ds_choice_opt,
                                      ds_no_choice,
                                      workingDirectory)

    # confidence
    confidence_fus = compute_confidence_fusion(fusion_dic, ds_choice,
                                               classif_model_pos, classif_tile_pos, classif_seed_pos,
                                               ds_choice_both,
                                               ds_choice_sar,
                                               ds_choice_opt,
                                               ds_no_choice,
                                               workingDirectory)
    return sar_opt_fus, confidence_fus, ds_choice


def fusion(pathClassif, cfg, pathWd):

    pathWd = None
    classifMode = cfg.getParam('argClassification', 'classifMode')
    N = cfg.getParam('chain', 'runs')
    allTiles = cfg.getParam('chain', 'listTile').split(" ")
    fusionOptions = cfg.getParam('argClassification', 'fusionOptions')
    pixType = fu.getOutputPixType(cfg.getParam('chain', 'nomenclaturePath'))
    region_vec = cfg.getParam('chain', 'regionPath')

    if region_vec:
        AllClassif = fu.fileSearchRegEx(pathClassif+"/Classif_*_model_*f*_seed_*.tif")
        allTiles = []
        models = []
        for classif in AllClassif:
            mod = classif.split("/")[-1].split("_")[3].split("f")[0]
            tile = classif.split("/")[-1].split("_")[1]
            if mod not in models:
                models.append(mod)
            if tile not in allTiles:
                allTiles.append(tile)
    AllCmd = []
    for seed in range(N):
        for tile in allTiles:
            directoryOut = pathClassif
            if pathWd != None:
                directoryOut = "$TMPDIR"

            if region_vec is None:
                classifPath = fu.FileSearch_AND(pathClassif, True, "Classif_"+tile, "seed_"+str(seed)+".tif")
                allPathFusion = " ".join(classifPath)
                cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out "+directoryOut+"/"+tile+"_FUSION_seed_"+str(seed)+".tif"
                AllCmd.append(cmd)
            else:
                for mod in models:
                    classifPath = fu.fileSearchRegEx(pathClassif+"/Classif_"+tile+"_model_"+mod+"f*_seed_"+str(seed)+".tif")
                    if len(classifPath) != 0:
                        allPathFusion = " ".join(classifPath)
                        cmd = "otbcli_FusionOfClassifications -il "+allPathFusion+" "+fusionOptions+" -out "+directoryOut+"/"+tile+"_FUSION_model_"+mod+"_seed_"+str(seed)+".tif "+pixType
                        AllCmd.append(cmd)

    tmp = pathClassif.split("/")
    if pathClassif[-1] == "/":
        del tmp[-1]
    tmp[-1] = "cmd/fusion"
    pathToCmdFusion = "/".join(tmp)
    fu.writeCmds(pathToCmdFusion+"/fusion.txt", AllCmd)

    return AllCmd

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allow you launch oso chain according to a configuration file")
    parser.add_argument("-path.classif", help="path to the folder which ONLY contains classification images (mandatory)", dest="pathClassif", required=True)
    parser.add_argument("-conf", help="path to the configuration file which describe the classification (mandatory)", dest="pathConf", required=False)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)
    fusion(args.pathClassif, cfg, args.pathWd)















