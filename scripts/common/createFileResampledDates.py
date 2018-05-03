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
import glob
from sys import argv
import LandsatDataN as LD
import numpy


tileList = ['Landsat8_D0003H0001', 'Landsat8_D0003H0002', 'Landsat8_D0003H0003', 'Landsat8_D0003H0004', 'Landsat8_D0003H0005', 'Landsat8_D0004H0001', 'Landsat8_D0004H0002', 'Landsat8_D0004H0003', 'Landsat8_D0004H0004', 'Landsat8_D0004H0005', 'Landsat8_D0005H0001', 'Landsat8_D0005H0002', 'Landsat8_D0005H0003', 'Landsat8_D0005H0004', 'Landsat8_D0005H0005', 'Landsat8_D0006H0001', 'Landsat8_D0006H0002', 'Landsat8_D0006H0003', 'Landsat8_D0006H0004', 'Landsat8_D0006H0005', 'Landsat8_D0007H0002', 'Landsat8_D0007H0003', 'Landsat8_D0007H0004', 'Landsat8_D0007H0005', 'Landsat8_D0008H0002', 'Landsat8_D0008H0003', 'Landsat8_D0008H0004']


if __name__ == "__main__":
    if (len(argv) != 4):
        raise Exception("[ ERROR ] you must supply: input_path out_path numer_days_to_resample")
    else:
        flist = []
        llist = []
        ipath = argv[1]
        opath = argv[2]
        days = argv[3]

        for tile in tileList:
            print tile
            flist.append(LD.getfirstdate(ipath, tile))
            llist.append(LD.getlastdate(ipath, tile))
        a = numpy.array(flist)
        b = numpy.max(a)
        d = numpy.array(llist)
        e = numpy.min(d)

        LD.RangeDates(str(b), str(e), int(days), opath)

