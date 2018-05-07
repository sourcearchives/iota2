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
import otbApplication as otb

def edgeStat(image, outStat_directory, useFilter, ram):

    def getStatMeanAndStd(stat):
        """
        OTB statistics parser
        """
        import re
        with open(stat, "r") as xml:
            for inLine in xml:
                if '<Statistic name="mean">' in inLine.rstrip('\n\r'):
                    for nextLine in xml:
                        mean = nextLine.rstrip('\n\r')
                        break
                if '<Statistic name="stddev">' in inLine.rstrip('\n\r'):
                    for nextLine in xml:
                        std = nextLine.rstrip('\n\r')
                        break
        try:
            mean = float(re.findall("\d+\,\d+", mean)[0].replace(",", "."))
            std = float(re.findall("\d+\,\d+", std)[0].replace(",", "."))
        except:
            mean = float(re.findall("\d+\.\d+", mean)[0])
            std = float(re.findall("\d+\.\d+", std)[0])
        return mean, std

    statName = os.path.splitext(os.path.split(image)[-1])[0]
    outStat = outStat_directory+"/"+statName+".xml"
    edgeDetec = otb.Registry.CreateApplication("EdgeExtraction")
    edgeDetec.SetParameterString("in", image)
    edgeDetec.SetParameterString("ram", str(ram))
    edgeDetec.SetParameterString("filter", useFilter)
    edgeDetec.Execute()

    stat = otb.Registry.CreateApplication("ComputeImagesStatistics")
    stat.AddImageToParameterInputImageList("il", edgeDetec.GetParameterOutputImage("out"))
    stat.SetParameterString("ram", str(ram))
    stat.SetParameterString("out", outStat)

    print "computing "+outStat

    stat.ExecuteAndWriteOutput()

    mean, std = getStatMeanAndStd(outStat)
    print "mean : "+str(mean)
    print "std  : "+str(std)
    return mean, std

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function compute statistics after an edge extraction.")

    parser.add_argument("-in", help="image to extract statistics", dest="image", required=True)
    parser.add_argument("-wd", help="working directory", dest="outStat_directory", required=True)
    parser.add_argument("-filter", help="filter to use", dest="useFilter", default="sobel", required=False)
    parser.add_argument("-ram", help="pipeline size", dest="ram", default="128", required=False)
    args = parser.parse_args()

    edgeStat(args.image, args.outStat_directory, args.useFilter, args.ram)

























