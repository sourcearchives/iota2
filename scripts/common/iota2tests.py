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
import unittest
import os
import Sensors
import Utils

testDir = "/tmp/"
iota2Dir = os.environ.get('IOTA2DIR')

def traitementIntelligent(x):
    return x+2

class iotaTestname(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testLandsat8Name(self):
        name = Sensors.Landsat8("",Utils.Opath(testDir+"/tsts"),\
                                iota2Dir+"/data/Config_1tile.cfg",0).name
        self.assertEqual(name, 'Landsat8')

    def testLaunchChain(self):
        import launchChain as lc
        lc.launchChain(iota2Dir+"/data/ConfigDummyParallel.cfg", False)
        """ TODO: valider les fichiers générés, les copier dans data, puis
        vérifier que ceux qui sont générés à l'exécution du test, sont
        identiques (test de non régression) """

    def testTraitementIntelligent(self):
        input = 3
        expected = 5
        result = traitementIntelligent(input)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
