# !/usr/bin/python
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

import logging
import os
import shutil

from Common import FileUtils as fut
from Common import OtbAppBank

LOGGER = logging.getLogger(__name__)


def prepareSelection(sample_sel_directory, tile_name, workingDirectory=None, LOGGER=LOGGER):
    """
    this function is dedicated to merge selection comming from different
    models by tiles. It is necessary in order to prepare sampleExtraction
    in the step call 'generate samples'

    Parameters
    ----------
    sample_sel_directory : string
        path to the IOTA² directory containing selections by models
    tile_name : string
        tile's name
    workingDirectory : string
        path to a working directory
    LOGGER : logging object
        root logger
    """

    wd = sample_sel_directory
    if workingDirectory:
        wd = workingDirectory

    vectors = fut.FileSearch_AND(sample_sel_directory, True, tile_name, "selection.sqlite")
    merge_selection_name = "{}_selection_merge".format(tile_name)
    output_selection_merge = os.path.join(wd, merge_selection_name + ".sqlite")

    if not os.path.exists(output_selection_merge):
        fut.mergeVectors(merge_selection_name, wd, vectors, ext="sqlite", out_Tbl_name="output")
        if workingDirectory:
            shutil.copy(output_selection_merge, os.path.join(sample_sel_directory, merge_selection_name + ".sqlite"))
            
    return os.path.join(sample_sel_directory, merge_selection_name + ".sqlite")


def write_xml(samples_per_class, samples_per_vector, output_merged_stats):
    """
    write a xml file according to otb's xml file pattern

    Parameters
    ----------
    samples_per_class : collections.OrderedDict
        by class (as key), the pixel count
    samples_per_vector : collections.OrderedDict
    output_merged_stats : string
        output path

    Note
    ----

    output xml format as `PolygonClassStatistics <http://www.orfeo-toolbox.org/Applications/PolygonClassStatistics.html>`_'s output
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

    samples_per_class_xml = "".join(['<StatisticMap value="{}" />'.format(count) for _, count in samples_per_class.items()])
    samples_per_class_part = XML('''<root>{}</root>'''.format(samples_per_class_xml))

    samples_per_vector_xml = "".join(['<StatisticMap value="{}" />'.format(count) for _, count in samples_per_vector.items()])
    samples_per_vector_part = XML('''<root>{}</root>'''.format(samples_per_vector_xml))

    for index, c_statistic_map in enumerate(samples_per_class_part):
        c_statistic_map.set('key', samples_per_class.keys()[index])

    for index, c_statistic_map in enumerate(samples_per_vector_part):
        c_statistic_map.set('key', samples_per_vector.keys()[index])

    # Add to first parent
    parent_a.extend(samples_per_class_part)

    # Copy nodes to second parent
    parent_b.extend(samples_per_vector_part)

    with open(output_merged_stats, "w") as xml_f:
        xml_f.write(prettify(top))


def merge_write_stats(stats, merged_stats):
    """
    use to merge sample's statistics

    Parameters
    ----------
    stats : list
        list of xml files to be merged
    merged_stats : string
        output xml file
    """
    import xml.etree.ElementTree as ET
    import collections
    samples_per_class = []
    samples_per_vector = []

    for stat in stats:
        tree = ET.parse(stat)
        root_class = tree.getroot()[0]
        root_vector = tree.getroot()[1]

        for val_class in root_class.iter("StatisticMap"):
            samples_per_class.append((val_class.attrib["key"], int(val_class.attrib["value"])))
        for val_vector in root_vector.iter("StatisticMap"):
            samples_per_vector.append((val_vector.attrib["key"], int(val_vector.attrib["value"])))

    samples_per_class = dict(fut.sortByFirstElem(samples_per_class))
    samples_per_vector = dict(fut.sortByFirstElem(samples_per_vector))

    samples_per_class_sum = collections.OrderedDict()
    for class_name, count_list in samples_per_class.items():
        samples_per_class_sum[class_name] = sum(count_list)

    samples_per_vector_sum = collections.OrderedDict()
    for poly_fid, count_list in samples_per_vector.items():
        samples_per_vector_sum[poly_fid] = sum(count_list)

    # write stats
    if os.path.exists(merged_stats):
        os.remove(merged_stats)

    write_xml(samples_per_class_sum, samples_per_vector_sum, merged_stats)


def gen_raster_ref(vec, cfg, working_directory):
    """
    generate the reference image needed to sampleSelection application

    Parameters
    ----------

    vec : string
        path to the shapeFile containing all polygons dedicated to learn
        a model.
    cfg : ServiceConfigFile object
    working_directory : string
        Path to a working directory
    """
    from Common.Utils import run
    tile_field_name = "tile_o"
    iota2_dir = cfg.getParam('chain', 'outputPath')
    features_directory = os.path.join(iota2_dir, "features")
    tiles = fut.getFieldElement(vec, driverName="ESRI Shapefile",
                                field=tile_field_name,
                                mode="unique", elemType="str")

    masks_name = fut.getCommonMaskName(cfg) + ".tif"
    rasters_tiles = [fut.FileSearch_AND(os.path.join(features_directory, tile_name), True, masks_name)[0] for tile_name in tiles]
    raster_ref_name = "ref_raster_{}.tif".format(os.path.splitext(os.path.basename(vec))[0])
    raster_ref = os.path.join(working_directory, raster_ref_name)
    raster_ref_cmd = "gdal_merge.py -ot Byte -n 0 -createonly -o {} {}".format(raster_ref,
                                                                               " ".join(rasters_tiles))
    run(raster_ref_cmd)
    return raster_ref, tiles


def get_sample_selection_param(cfg, model_name, stats, vec, working_directory):
    """
    use to determine SampleSelection otb's parameters

    Parameters
    ----------
    cfg : ServiceConfigFile object
    model_name : string
    stats : string
        path to a xml file containing polygons statistics
    vec : string
        shapeFile to sample
    working_directory : string
        path to a working directory
    Note
    ----

    SampleSelection's parameters are define `here <http://www.orfeo-toolbox.org/Applications/SampleSelection.html>`_
    """
    per_model = None
    parameters = dict(cfg.getParam('argTrain', 'sampleSelection'))
    if "per_model" in parameters:
        per_model = parameters["per_model"]
        parameters.pop("per_model", None)

    if per_model:
        for strat in per_model:
            if str(model_name.split("f")[0]) == str(strat["target_model"]):
                parameters = dict(strat)
                parameters.pop("target_model", None)

    parameters["field"] = (cfg.getParam('chain', 'dataField')).lower()
    parameters["vec"] = vec
    parameters["instats"] = stats

    raster_ref, tiles_model = gen_raster_ref(vec, cfg, working_directory)

    parameters["in"] = raster_ref

    sample_sel_name = "{}_selection.sqlite".format(os.path.splitext(os.path.basename(vec))[0])
    sample_sel = os.path.join(working_directory, sample_sel_name)
    parameters["out"] = sample_sel

    return parameters, tiles_model


def split_sel(model_selection, tiles, working_directory, epsg):
    """
    split a SQLite file containing points by tiles

    Parameters
    ----------

    model_selection : string
        path to samplesSelection's output to a given model
    tiles : list
        list of tiles intersected by the model
    epsg : string
        epsg's projection. ie : epsg="EPSG:2154"
    working_directory : string
        path to a working directory
    """
    import sqlite3 as lite
    from Common.Utils import run

    tile_field_name = "tile_o"

    out_tiles = []
    for tile in tiles:
        mod_sel_name = os.path.splitext(os.path.basename(model_selection))[0]
        tile_mod_sel_name_tmp = "{}_{}_tmp".format(tile, mod_sel_name)
        tile_mod_sel_tmp = os.path.join(working_directory, tile_mod_sel_name_tmp + ".sqlite")
        if os.path.exists(tile_mod_sel_tmp):
            os.remove(tile_mod_sel_tmp)

        conn = lite.connect(tile_mod_sel_tmp)
        cursor = conn.cursor()
        cursor.execute("ATTACH '{}' AS db".format(model_selection))
        cursor.execute("CREATE TABLE {} as SELECT * FROM db.output WHERE {}='{}'".format(tile_mod_sel_name_tmp.lower(), tile_field_name, tile))
        conn.commit()

        tile_mod_sel_name = "{}_{}".format(tile, mod_sel_name)
        tile_mod_sel = os.path.join(working_directory, tile_mod_sel_name + ".sqlite")
        clause = "SELECT * FROM {}".format(tile_mod_sel_name_tmp)
        cmd = 'ogr2ogr -sql "{}" -dialect "SQLite" -f "SQLite" -s_srs {} -t_srs {} -nln {} {} {}'.format(clause, epsg, epsg,
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
    sep = "\n" + "\t".join(["" for _ in range(22)])
    return sep + sep.join(["{} : {}".format(key, val) for key, val in dico.items()])


def update_flags(vec_in, runs, flag_val="XXXX", table_name="output"):
    """
    set the special value 'XXXX' to the seeds different form the current one

    Parameters
    ----------

    vec_in : string
        path to a sqlite file containing "seed_*" field(s)
    runs : int
        number of random samples
    flag_val : string
        features's value for seeds different from the current one
    """
    import sqlite3 as lite

    current_seed = int(os.path.splitext(os.path.basename(vec_in))[0].split("_")[-2])

    if runs > 1:
        update_seed = ",".join(["seed_{} = '{}'".format(run, flag_val) for run in range(runs) if run != current_seed])
        conn = lite.connect(vec_in)
        cursor = conn.cursor()
        sql_clause = "UPDATE {} SET {}".format(table_name, update_seed)
        cursor.execute(sql_clause)
        conn.commit()


def samples_selection(model, cfg, working_directory, logger=LOGGER):
    """
    compute sample selection.

    Parameters
    ----------

    model : string
        path to a shapeFile containing all polygons to build a model
    cfg : ServiceConfigFile object
    working_directory : string
        Path to a working directory
    logger : logging object
        root logger
    """
    from Common import ServiceConfigFile as SCF

    # because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    iota2_directory = cfg.getParam('chain', 'outputPath')
    runs = cfg.getParam('chain', 'runs')
    epsg = cfg.getParam('GlobChain', 'proj')
    samples_sel_dir = os.path.join(iota2_directory, "samplesSelection")

    merged_stats = model.replace(".shp", ".xml")
    if os.path.exists(merged_stats):
        os.remove(merged_stats)

    wdir = samples_sel_dir
    if working_directory:
        wdir = working_directory

    model_name = os.path.splitext(os.path.basename(model))[0].split("_")[2]
    seed = os.path.splitext(os.path.basename(model))[0].split("_")[4]

    logger.info("Launch sample selection for the model '{}' run {}".format(model_name, seed))

    # merge stats
    stats = fut.FileSearch_AND(samples_sel_dir, True, "region_" + str(model_name), ".xml", "seed_" + str(seed))
    merge_write_stats(stats, merged_stats)

    # samples Selection
    sel_parameters, tiles_model = get_sample_selection_param(cfg, model_name, merged_stats, model, wdir)

    logger.debug("SampleSelection parameters : {}".format(print_dict(sel_parameters)))

    sample_sel_app = OtbAppBank.CreateSampleSelectionApplication(sel_parameters)
    sample_sel_app.ExecuteAndWriteOutput()
    logger.info("sample selection terminated")

    # update samples flag -> keep current values in seed field and set 'XXXX' values to the others
    update_flags(sel_parameters["out"], runs)

    # split by tiles
    sel_tiles = split_sel(sel_parameters["out"], tiles_model, wdir, epsg)

    if working_directory:
        for sel_tile in sel_tiles:
            shutil.copy(sel_tile, samples_sel_dir)
    # remove tmp data
    os.remove(sel_parameters["in"])
