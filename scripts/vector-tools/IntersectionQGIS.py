# -*- coding: utf-8 -*-
# Prepare the environment
#Priorite deuxieme fichier
import sys
from qgis.core import *
from PyQt4.QtGui import *
from osgeo import ogr

app = QApplication([])
QgsApplication.setPrefixPath("/usr", True)
QgsApplication.initQgis()

driver = ogr.GetDriverByName("ESRI Shapefile")
# Prepare processing framework 
sys.path.append('/usr/share/qgis/python/plugins/')
from processing.core.Processing import Processing
Processing.initialize()
from processing.tools import *

# Run the algorithm
inLayer = QgsVectorLayer(sys.argv[1], 'layer1', 'ogr')
overlay = QgsVectorLayer(sys.argv[2], 'layer2', 'ogr')
outLayer = sys.argv[3]
general.runalg('qgis:intersection', inLayer, overlay, outLayer)

# Exit applications
QgsApplication.exitQgis()
QApplication.exit()
