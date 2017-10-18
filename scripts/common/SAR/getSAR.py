#!/usr/bin/python
#-*- coding: utf-8 -*-


import S1Processor as s1p

configurationFile = "/home/uz/vincenta/tmp/testS1.cfg"

allFiltered,allDependence,allTile = s1p.S1Processor(configurationFile)

for CallFiltered,CallDependence,CallTile in zip(allFiltered,allDependence,allTile):
    for SARFiltered,a,b,c,d in CallFiltered : SARFiltered.ExecuteAndWriteOutput()


