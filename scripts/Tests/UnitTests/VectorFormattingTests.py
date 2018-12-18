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

# python -m unittest SamplesSelectionsTests

import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2_SCRIPTS = IOTA2DIR + "/scripts"
sys.path.append(IOTA2_SCRIPTS)

from Common import FileUtils as fut


class iota_testVectorFormatting(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testVectorFormatting"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.in_vector = os.path.join(IOTA2DIR, "data", "references",
                                      "formatting_vectors", "Input",
                                      "formattingVectors", "T31TCJ.shp")
        self.ref_img = os.path.join(IOTA2DIR, "data", "references",
                                    "selectionSamples", "Input",
                                    "features", "T31TCJ", "tmp",
                                    "MaskCommunSL.tif")
        self.ref_region = os.path.join(IOTA2DIR, "data", "references",
                                    "genResults", "Input", "classif",
                                    "MASK","Myregion_region_1_T31TCJ.shp")

        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print "{} ended".format(self.group_test_name)
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

    # before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        # self.test_working_directory is the diretory dedicated to each tests
        # it changes for each tests

        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        test_ok = not error and not failure
        self.all_tests_ok.append(test_ok)
        if test_ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_VectorFormatting(self):
        """
        test vectorFormatting function
        random function is used in Sampling.VectorFormatting.VectorFormatting
        we can only check if there is expected number of features with
        expected fields and some features values
        """
        from Sampling.VectorFormatting import VectorFormatting
        from Common import ServiceConfigFile as SCF
        from Common import IOTA2Directory
        from Common.Utils import run
        from VectorTools.ChangeNameField import changeName

        # define inputs
        test_output = os.path.join(self.test_working_directory,
                                   "IOTA2_dir_VectorFormatting")
        # prepare ground truth
        ground_truth = os.path.join(self.test_working_directory,
                                    "groundTruth_test.shp")
        cmd = "ogr2ogr -s_srs EPSG:2154 -t_srs EPSG:2154 -dialect 'SQLite' -sql 'select GEOMETRY,code from t31tcj' {} {}".format(ground_truth,
                                                                                                                                 self.in_vector)
        run(cmd)

        # cfg instance
        runs = 2
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam('chain', 'outputPath', test_output)
        cfg.setParam('chain', 'groundTruth', ground_truth)
        cfg.setParam('chain', 'dataField', "code")
        cfg.setParam('chain', 'cloud_threshold', 0)
        cfg.setParam('chain', 'merge_final_classifications', False)
        cfg.setParam('chain', 'runs', runs)
        cfg.setParam('GlobChain', 'proj', "EPSG:2154")
        cfg.setParam('chain', 'regionPath', self.ref_region)

        IOTA2Directory.GenerateDirectories(cfg)

        # prepare expected function inputs
        t31tcj_feat_dir = os.path.join(self.test_working_directory,
                                       "IOTA2_dir_VectorFormatting",
                                       "features",
                                       "T31TCJ")
        os.mkdir(t31tcj_feat_dir)
        # prepare ref img
        t31tcj_ref_img = os.path.join(t31tcj_feat_dir, "MaskCommunSL.tif")
        shutil.copy(self.ref_img, t31tcj_ref_img)
        # prepare envelope
        envelope_name = "T31TCJ.shp"
        envelope_path = os.path.join(self.test_working_directory,
                                     "IOTA2_dir_VectorFormatting",
                                     "envelope", envelope_name)
        fut.cpShapeFile(self.ref_region.replace(".shp",""),
                        envelope_path.replace(".shp",""),
                        [".prj",".shp",".dbf",".shx"])
        changeName(envelope_path, "region", "FID")
        # prepare cloud mask
        cloud_name = "CloudThreshold_0.shp"
        cloud_path = os.path.join(self.test_working_directory,
                                  "IOTA2_dir_VectorFormatting",
                                  "features", "T31TCJ", cloud_name)
        fut.cpShapeFile(self.ref_region.replace(".shp",""),
                        cloud_path.replace(".shp",""),
                        [".prj",".shp",".dbf",".shx"])
        changeName(cloud_path, "region", "cloud")

        # launch function
        VectorFormatting(cfg, "T31TCJ", workingDirectory=None)

        # assert
        nb_features_origin = len(fut.getFieldElement(ground_truth,
                                                    driverName="ESRI Shapefile",
                                                    field="code", mode="all",
                                                    elemType="str"))
        test_vector = fut.FileSearch_AND(os.path.join(test_output, "formattingVectors"),
                                         True, "T31TCJ.shp")[0]
        nb_features_test = len(fut.getFieldElement(test_vector,
                                                   driverName="ESRI Shapefile",
                                                   field="code", mode="all",
                                                   elemType="str"))
        # check nb features
        self.assertTrue(nb_features_origin == nb_features_test,
                        msg="wrong number of features")

        # check fields
        origin_fields = fut.getAllFieldsInShape(ground_truth)
        test_fields = fut.getAllFieldsInShape(test_vector)

        new_fields = ['region', 'originfid', 'seed_0', 'seed_1', 'tile_o']
        expected_fields = origin_fields + new_fields
        self.assertTrue(len(expected_fields)==len(test_fields))
        self.assertTrue(all(field in test_fields for field in expected_fields))


    def test_extract_maj_vote_samples(self):
        """
        test the extraction of samples by class according to a ratio
        """
        from Sampling.VectorFormatting import extract_maj_vote_samples
        from collections import Counter

        # define inputs
        in_vector_name = os.path.basename(self.in_vector)
        extracted_vector_name = "extracted_samples.sqlite"
        in_vector = os.path.join(self.test_working_directory,
                                 in_vector_name)
        extracted_vector = os.path.join(self.test_working_directory,
                                        extracted_vector_name)
        fut.cpShapeFile(self.in_vector.replace(".shp",""),
                        in_vector.replace(".shp",""), [".prj",".shp",".dbf",".shx"])

        # launch function
        dataField = "code"
        regionField = "region"
        extraction_ratio = 0.5
        extract_maj_vote_samples(in_vector, extracted_vector, extraction_ratio, dataField,
                                 regionField)
        # assert
        features_origin = fut.getFieldElement(self.in_vector,
                                              driverName="ESRI Shapefile",
                                              field=dataField, mode="all",
                                              elemType="str")
        by_class_origin = Counter(features_origin)

        features_in_vector = fut.getFieldElement(in_vector,
                                                 driverName="ESRI Shapefile",
                                                 field=dataField, mode="all",
                                                 elemType="str")
        by_class_in_vector = Counter(features_in_vector)

        features_extract_vector = fut.getFieldElement(extracted_vector,
                                                      driverName="SQLite",
                                                      field=dataField, mode="all",
                                                      elemType="str")
        by_class_extract_vector = Counter(features_extract_vector)

        buff = []
        for class_name, class_count in by_class_origin.items():
            buff.append(by_class_in_vector[class_name] == extraction_ratio * class_count)

        self.assertTrue(all(buff), msg="extraction of samples failed")

    def test_BuiltWhereSQL_exp(self):
        """
        test the sql clause generation. There is a random part in 
        the function BuiltWhereSQL_exp, the returned string value can
        not be compare to a reference. That is the reason why we check 
        the number of 'OR' which must be the rest of nb_id / 1000.0
        """
        from Sampling.VectorFormatting import BuiltWhereSQL_exp

        nb_id = 2000
        sample_id_to_extract_low = [str(id_) for id_ in range(nb_id)]
        sql_clause = BuiltWhereSQL_exp(sample_id_to_extract_low, "in")
        nb_or_test = sql_clause.count("OR")
        self.assertEqual(1, nb_or_test, msg="SQLite expression failed")

    def test_splitbySets(self):
        """
        test the split of a given vector
        """
        from Sampling.VectorFormatting import splitbySets

        # launch function
        s0_val, s0_learn, s1_val, s1_learn = splitbySets(self.in_vector, 2,
                                                         self.test_working_directory,
                                                         2154, 2154, "T31TCJ",
                                                         crossValid=False,
                                                         splitGroundTruth=True)
        # assert
        seed_0 = fut.getFieldElement(self.in_vector,
                                     driverName="ESRI Shapefile",
                                     field="seed_0", mode="all",
                                     elemType="str")
        seed_1 = fut.getFieldElement(self.in_vector,
                                     driverName="ESRI Shapefile",
                                     field="seed_1", mode="all",
                                     elemType="str")

        seed_0_learn_ref = seed_0.count("learn")
        seed_0_val_ref = seed_0.count("validation")
        seed_1_learn_ref = seed_1.count("learn")
        seed_1_val_ref = seed_1.count("validation")

        seed_0_learn_test = len(fut.getFieldElement(s0_learn,
                                                    driverName="SQLite",
                                                    field="region", mode="all",
                                                    elemType="str"))
        seed_0_val_test = len(fut.getFieldElement(s0_val,
                                                  driverName="SQLite",
                                                  field="region", mode="all",
                                                  elemType="str"))
        seed_1_learn_test = len(fut.getFieldElement(s1_learn,
                                                    driverName="SQLite",
                                                    field="region", mode="all",
                                                    elemType="str"))
        seed_1_val_test = len(fut.getFieldElement(s1_val,
                                                  driverName="SQLite",
                                                  field="region", mode="all",
                                                  elemType="str"))
        
        self.assertTrue(seed_0_learn_test == seed_0_learn_ref,
                        msg="wrong number of learning samples in seed 0")
        self.assertTrue(seed_1_learn_test == seed_1_learn_ref,
                        msg="wrong number of learning samples in seed 1")
        self.assertTrue(seed_0_val_test == seed_0_val_ref,
                        msg="wrong number of validation samples in seed 0")
        self.assertTrue(seed_1_val_test == seed_1_val_ref,
                        msg="wrong number of validation samples in seed 1")

    def test_keepFields(self):
        """
        test the extraction of fields
        """
        from Sampling.VectorFormatting import keepFields

        # define inputs
        fields_to_keep = ["region", "code"]
        test_vector_name = "test_vector.sqlite"
        test_vector = os.path.join(self.test_working_directory, test_vector_name)

        # launch function
        keepFields(self.in_vector, test_vector, fields=fields_to_keep)

        # assert
        test_vector_fields = fut.getAllFieldsInShape(test_vector, driver='SQLite')
        self.assertTrue(all(current_field in fields_to_keep for current_field in test_vector_fields),
                        msg="remove fields failed")

    def test_create_tile_region_masks(self):
        """
        test the generation of the raster mask which define the region
        in the tile
        """
        from Sampling.VectorFormatting import create_tile_region_masks
        from Common.Utils import run
        from Iota2Tests import rasterToArray
        import numpy as np

        # define inputs
        test_vector_name = "T31TCJ.sqlite"
        test_vector = os.path.join(self.test_working_directory, test_vector_name)
        cmd = "ogr2ogr -nln t31tcj -f SQLite {} {}".format(test_vector, self.ref_region)
        run(cmd)

        # launch function
        create_tile_region_masks(test_vector, "region", "T31TCJ", self.test_working_directory,
                                 "MyRegion", self.ref_img)
        # assert
        raster_region = fut.FileSearch_AND(self.test_working_directory, True, "MyRegion", ".tif")[0]
        raster_region_arr = rasterToArray(raster_region)

        ref_array = np.ones((50, 50))

        self.assertTrue(np.allclose(ref_array, raster_region_arr),
                        msg="problem with the normalization by ref")

    def test_split_vector_by_region(self):
        """
        test : split a vector by the region he belongs to
        """
        from Sampling.VectorFormatting import split_vector_by_region
        from Common.Utils import run
        from Iota2Tests import random_update

        # define inputs
        nb_features_origin = len(fut.getFieldElement(self.in_vector,
                                                     driverName="ESRI shapefile",
                                                     field="region", mode="all",
                                                     elemType="str"))
        nb_features_new_region = 5
        test_vector_name = "T31TCJ_Samples.sqlite"
        test_vector = os.path.join(self.test_working_directory, test_vector_name)
        cmd = "ogr2ogr -nln output -f SQLite {} {}".format(test_vector, self.in_vector)
        run(cmd)

        random_update(test_vector, "output",
                      "seed_0", "learn", nb_features_origin)
        random_update(test_vector, "output",
                      "region", "2", nb_features_new_region)

        output_dir = self.test_working_directory
        region_field = "region"

        # launch function
        split_vector_by_region(test_vector, output_dir,
                               region_field, runs=1,
                               driver="SQLite")
        # assert
        vector_reg_1 = fut.FileSearch_AND(self.test_working_directory, True, "region_1")[0]
        vector_reg_2 = fut.FileSearch_AND(self.test_working_directory, True, "region_2")[0]

        feat_vect_reg_1 = len(fut.getFieldElement(vector_reg_1,
                                                  driverName="SQLite",
                                                  field="region", mode="all",
                                                  elemType="str"))
        feat_vect_reg_2 = len(fut.getFieldElement(vector_reg_2,
                                                  driverName="SQLite",
                                                  field="region", mode="all",
                                                  elemType="str"))

        self.assertTrue(nb_features_new_region == feat_vect_reg_2)
        self.assertTrue(nb_features_origin == feat_vect_reg_1 + feat_vect_reg_2)
