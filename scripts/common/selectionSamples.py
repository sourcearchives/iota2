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

import logging
import os
import shutil

import fileUtils as fut
import otbAppli as otb

logger = logging.getLogger(__name__)

def write_xml(samplesPerClass, samplesPerVector, output_merged_stats):
    """
    usage : write a xml file according to otb's xml file pattern

    INPUT
    samplesPerClass [dict]
    samplesPerVector [dict]
    output_merged_stats [string]
    
    OUTPUT
    output_merged_stats [string] merged xml file
    """
    import xml.dom.minidom as minidom
    from xml.etree.ElementTree import Element, SubElement, tostring, XML

    def prettify(elem):
        rough_string = tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    top = Element('GeneralStatistics')
    parent_a = SubElement(top, 'Statistic', name='samplesPerClass')
    parent_b = SubElement(top, 'Statistic', name='samplesPerVector')

    samplesPerClass_xml = "".join(['<StatisticMap value="{}" />'.format(count) for class_name, count in samplesPerClass.items()])
    samplesPerClass_part = XML('''<root>{}</root>'''.format(samplesPerClass_xml))

    samplesPerVector_xml = "".join(['<StatisticMap value="{}" />'.format(count) for poly_FID, count in samplesPerVector.items()])
    samplesPerVector_part = XML('''<root>{}</root>'''.format(samplesPerVector_xml))

    for index, c in enumerate(samplesPerClass_part):
        c.set('key', samplesPerClass.keys()[index])
    
    for index, c in enumerate(samplesPerVector_part):
        c.set('key', samplesPerVector.keys()[index])

    # Add to first parent
    parent_a.extend(samplesPerClass_part)

    # Copy nodes to second parent
    parent_b.extend(samplesPerVector_part)

    with open(output_merged_stats, "w") as xml_f:
        xml_f.write(prettify(top))

def merge_write_stats(stats, merged_stats):
    """
    stats [string] xml files to be merged
    merged_stats [string] output merged stats
    """
    import xml.etree.ElementTree as ET
    import collections
    samplesPerClass = []
    samplesPerVector = []

    for stat in stats:
        tree = ET.parse(stat)
        root_class = tree.getroot()[0]
        root_vector = tree.getroot()[1]

        for val_class in root_class.iter("StatisticMap"):
            samplesPerClass.append((val_class.attrib["key"], int(val_class.attrib["value"])))
        for val_vector in root_vector.iter("StatisticMap"):
            samplesPerVector.append((val_vector.attrib["key"], int(val_vector.attrib["value"])))

    samplesPerClass = dict(fut.sortByFirstElem(samplesPerClass))
    samplesPerVector = dict(fut.sortByFirstElem(samplesPerVector))
    
    samplesPerClass_sum = collections.OrderedDict()
    for class_name, count_list in samplesPerClass.items():
        samplesPerClass_sum[class_name] = sum(count_list)
    
    samplesPerVector_sum = collections.OrderedDict()
    for poly_fid, count_list in samplesPerVector.items():
        samplesPerVector_sum[poly_fid] = sum(count_list)

    #write stats
    if os.path.exists(merged_stats):
        os.remove(merged_stats)

    write_xml(samplesPerClass_sum, samplesPerVector_sum, merged_stats)


def gen_raster_ref(vec, cfg, workingDirectory):
    """
    usage : generate reference image to sampleSelection application
    TODO : cmp gdal_merge vs gdal_build_vrt
    """
    from Utils import run
    tileOrigin_field_name = "tile_o"
    features_directory = cfg.getParam('chain', 'featuresPath')
    tiles = fut.getFieldElement(vec, driverName="ESRI Shapefile",
                                field=tileOrigin_field_name,
                                mode="unique", elemType="str")

    rasters_tiles = [fut.FileSearch_AND(os.path.join(features_directory, tile_name), True, "MaskCommunSL.tif")[0] for tile_name in tiles]
    raster_ref_name = "ref_raster_{}.tif".format(os.path.splitext(os.path.basename(vec))[0])
    raster_ref = os.path.join(workingDirectory, raster_ref_name)

    raster_ref_cmd = "gdal_merge.py -ot Byte -n 0 -createonly -o {} {}".format(raster_ref,
                                                                               " ".join(rasters_tiles))
    run(raster_ref_cmd)
    return raster_ref, tiles


def get_sample_selection_param(cfg, model_name, stats, vec, workingDirectory):
    """
    usage : return sample selection otb's parameters
    """
    per_model = None
    #default parameters are define here
    sample_sel_def = {"sampler": "random",
                      "strategy": "percent",
                      "strategy.percent.p": "0.1",
                      "ram": "4000"}

    parameters = sample_sel_def
    try:
        parameters = dict(cfg.getParam('argTrain', 'sampleSelection'))
        if "per_model" in parameters:
            per_model = parameters["per_model"]
            parameters.pop("per_model", None)
    except:
        parameters = sample_sel_def

    if per_model:
        for strat in per_model:
            if str(model_name.split("f")[0]) == str(strat["target_model"]):
                parameters = dict(strat)
                parameters.pop("target_model", None)

    parameters["field"] = (cfg.getParam('chain', 'dataField')).lower()
    parameters["vec"] = vec
    parameters["instats"] = stats

    raster_ref, tiles_model = gen_raster_ref(vec, cfg, workingDirectory)

    parameters["in"] = raster_ref
    
    sample_sel_name = "{}_selection.sqlite".format(os.path.splitext(os.path.basename(vec))[0])
    sample_sel = os.path.join(workingDirectory, sample_sel_name)
    parameters["out"] = sample_sel

    return parameters, tiles_model


def split_sel(model_selection, tiles, workingDirectory, EPSG):
    """
    """
    import sqlite3 as lite
    from Utils import run

    tileOrigin_field_name = "tile_o"

    out_tiles = []
    for tile in tiles:
        mod_sel_name = os.path.splitext(os.path.basename(model_selection))[0]
        tile_mod_sel_name_tmp = "{}_{}_tmp".format(tile, mod_sel_name)
        tile_mod_sel_tmp = os.path.join(workingDirectory, tile_mod_sel_name_tmp + ".sqlite")
        if os.path.exists(tile_mod_sel_tmp):
            os.remove(tile_mod_sel_tmp)

        conn = lite.connect(tile_mod_sel_tmp)
        cursor = conn.cursor()
        cursor.execute("ATTACH '{}' AS db".format(model_selection))
        cursor.execute("CREATE TABLE {} as SELECT * FROM db.output WHERE {}='{}'".format(tile_mod_sel_name_tmp.lower(), tileOrigin_field_name, tile))
        conn.commit()
        
        tile_mod_sel_name = "{}_{}".format(tile, mod_sel_name)
        tile_mod_sel = os.path.join(workingDirectory, tile_mod_sel_name + ".sqlite")
        clause = "SELECT * FROM {}".format(tile_mod_sel_name_tmp)
        cmd = 'ogr2ogr -sql "{}" -dialect "SQLite" -f "SQLite" -s_srs {} -t_srs {} -nln {} {} {}'.format(clause, EPSG, EPSG,
                                                                                                         tile_mod_sel_name.lower(),
                                                                                                         tile_mod_sel, tile_mod_sel_tmp)
        run(cmd)

        os.remove(tile_mod_sel_tmp)
        out_tiles.append(tile_mod_sel)
        conn = cursor = None

    return out_tiles


def print_dict(dico):
    """
    usage : use to print some dictionnary
    """
    sep = "\n"+"\t".join(["" for i in range(22)])
    return sep+sep.join(["{} : {}".format(key, val) for key, val in dico.items()])


def update_flags(vec_in, runs, flag_val="XXXX"):
    """
    """
    import sqlite3 as lite

    current_seed = int(os.path.splitext(os.path.basename(vec_in))[0].split("_")[-2])

    if runs > 1:
        update_seed = ",".join(["seed_{} = '{}'".format(run, flag_val) for run in range(runs) if run!=current_seed])

        conn = lite.connect(vec_in)
        cursor = conn.cursor()
        sql_clause = "UPDATE output SET {}".format(update_seed)
        cursor.execute(sql_clause)
        conn.commit()


def samples_selection(model, cfg, workingDirectory, logger=logger):
    """
    usage : compute sample selection according to configuration file parameters
    
    INPUT
    model [string] path to the shapeFile containing learning polygons of a specific model
    cfg [serviceConfig file object]
    workingDirectory [string] : path to a working directory
    """
    import serviceConfigFile as SCF

    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    iota2_directory = cfg.getParam('chain', 'outputPath')
    runs = cfg.getParam('chain', 'runs')
    EPSG = cfg.getParam('GlobChain', 'proj')
    samples_sel_dir = os.path.join(iota2_directory, "samplesSelection")

    merged_stats = model.replace(".shp", ".xml")
    if os.path.exists(merged_stats):
        os.remove(merged_stats)

    wd = samples_sel_dir
    if workingDirectory:
        wd = workingDirectory

    model_name = os.path.splitext(os.path.basename(model))[0].split("_")[2]
    seed = os.path.splitext(os.path.basename(model))[0].split("_")[4]

    logger.info("Launch sample selection for the model '{}' run {}".format(model_name, seed))

    #merge stats
    stats = fut.FileSearch_AND(samples_sel_dir, True, "region_" + str(model_name), ".xml", "seed_" + str(seed))

    merge_write_stats(stats, merged_stats)

    #samples Selection
    sel_parameters, tiles_model = get_sample_selection_param(cfg, model_name, merged_stats, model, wd)

    logger.debug("SampleSelection parameters : {}".format(print_dict(sel_parameters)))

    sampleSel = otb.CreateSampleSelectionApplication(sel_parameters)
    sampleSel.ExecuteAndWriteOutput()
    logger.info("sample selection terminated")
    
    #update samples flag -> keep current values in seed field and set XXXX values to the others
    update_flags(sel_parameters["out"], runs)

    #split by tiles
    sel_tiles = split_sel(sel_parameters["out"], tiles_model, wd, EPSG)

    if workingDirectory:
        for sel_tile in sel_tiles:
            shutil.copy(sel_tile, samples_sel_dir)

    #remove tmp data
    os.remove(sel_parameters["in"])

