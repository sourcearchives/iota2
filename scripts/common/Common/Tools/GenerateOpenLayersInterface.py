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

import sys

#---------------------------------------------------------------------------------------------------------------------------------
def getStringBetween(string, ch1, ch2):
    out = ""
    for i in range(len(string)):
        if ch1 == string[i]:
            for j in range(i+1, len(string)):
                if string[j] == ch2:
                    break
                else:
                    out = out+string[j]
            break
    return out
#---------------------------------------------------------------------------------------------------------------------------------
def generate(listClassif, colorFile, pathOut, urlserveur):

    panelHeight = str(5+5*len(listClassif))

    #Recherche du nom le plus long pour une classif
    Size = len("List of Classifications")
    for i in range(len(listClassif)):
        if len(listClassif[i][0]) > Size:
            Size = int(len(listClassif[i][0]))
    Size = 0.95*Size
    #loop over classifications and their results
    for classifName, results in listClassif:
        #Read classification's results
        classifRes = []#[(ClassNumber,FScore),...]
        resFile = open(results, "r")
        while 1:
            data = resFile.readline().rstrip('\n\r')
            if data.count('Standard deviation is:') != 0:
                std = float(data.split(":")[-1])
                break
            elif data.count("Class") != 0:
                classe = data.split(" ")[1].replace(",", "")
                FScore = float(data.split(" ")[4])
                classifRes.append((classe, FScore))
            elif data.count("Mean OA of the 1 tests is:") != 0:
                OA = data.split(":")[-1].replace(" ", "")

        resFile.close()

        htmlFile = open(pathOut+"/"+classifName+".html", "w")

        htmlFile.write('<!DOCTYPE html>\n<html>\n<head>\n<title>Prototype de produit</title>\n<script src="https://code.jquery.com/jquery-1.11.2.min.js"></script>\n<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>\n<link rel="stylesheet" href="http://openlayers.org/en/v3.10.1/css/ol.css" type="text/css">\n<meta  http-equiv="Content-Type" content="text/html;charset=utf-8" />\n<script src="http://openlayers.org/en/v3.10.1/build/ol.js"></script>\n<link rel="stylesheet" href="popup.css">\n')
        htmlFile.write('<style type="text/css">\n\
#left-panel {\n\
width: %s%%;\n\
height: %s%%;\n\
border: 3px solid rgba(160,160,160,0.6);\n\
background-color: rgba(51,89,131,0.6);\n\
position: fixed;\n\
top: 50%%;\n\
left: -29%%;\n\
border-radius: 0 1em 1em 0;\n\
padding: 1%%;\n\
-webkit-transition: all 0.5s ease-in-out;\n\
-moz-transition: all 0.25s ease-in-out;\n\
-o-transition: all 0.25s ease-in-out;\n\
}\n\
#left-panel:hover {\n\
 left: 0px;\n\
}\n\
\n\
#left-panel.show {\n\
left: -100px;\n\
}\n\
\n\
#left-panel a.controller {\n\
position: absolute;\n\
right: 5px;\n\
top: 5px;\n\
text-decoration: none;\n\
-webkit-transition: all 0.25s ease-in-out;\n\
color: black;\n\
font-weight: bold;\n\
-moz-transition: all 0.25s ease-in-out;\n\
-o-transition: all 0.25s ease-in-out;\n\
}\n\
\n\
#left-panel.show a.controller {\n\
-webkit-transform: rotate(180deg);\n\
-moz-transform: rotate(180deg);\n\
-o-transform: rotate(180deg);\n\
}\n\
</style>\n\
\n\
<style>\n\
	.map {\n\
      	       height: 85%%;\n\
      	       width: 60%%;\n\
               margin: 0px;\n\
             }\n\
	.score {\n\
  		 width: 100%%;\n\
		 float: left\n\
		 height: 80%%;\n\
		 border: 1px solid white;\n\
		 margin: 5px;\n\
	         }\n\
	.org-right  {\n\
		      margin-left: 2px;\n\
		      margin-right: 2px;\n\
		      text-align: left;\n\
		      font-size: 15px;\n\
		    }\n\
  	.org-left   {\n\
		      margin-left: 2px;\n\
		      margin-right: 2px;\n\
		      text-align: left;\n\
                      font-size: 15px;\n\
                    }\n\
	.separator{\n\
                    height: 2px;\n\
    	          }\n\
	.classification{\n\
		         font-size: 8px;\n\
		         text-decoration: none;\n\
	               }\n\
</style>\n\
</head>\n\
<body>\n\
\n\
<div class="container">\n\
	<div class = "row">\n\
		<div class = "span" style="position: absolute; left: 0; top: 0; right:0; bottom: 0;">\n\
			<h1>Prototypes de produits</h1>\n\
			<div id="map" class="map" style="float: left"></div>\n\
			<div id = "right panel" style="float: left;height: 70%%;width: 40%%;margin: 0px;">\n\
				<div id = "ClickInfo" style="float: left;height: 15%%;width: 100%%;border: 0px solid white;margin: 5px">\n\
					<div id="ClassClicked" style="float: left;height: 100%%;width: 50%%;border: 0px solid white;margin: 0px">Class Clicked :</div>\n\
					<div id="information" style="float: right;height: 100%%;width: 50%%;border: 0px solid white;margin: 0px">Information</div>\n\
				</div>\n\
				<div id = "sc" class = "score">\n\
				<table border="2" BORDERCOLOR="black" style="width:100%%;" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">\n\
					<colgroup>\n\
						<col  class="org-left" />\n\
						<col  class="org-right" />\n\
					</colgroup>\n\
					<thead>\n\
						<tr>\n\
						<th scope="col" class="org-left">Classe</th>\n\
						<th scope="col" class="org-right">FScore</th>\n\
						</tr>\n\
					</thead>\n\
					<tbody >\n'%(Size, panelHeight))

        #Read the color's file and write into the html file
        color = open(colorFile, "r")
        lineData = []#[(ClassNumber,ClassName,r,g,b,Fscore),[...],...]
        while 1:
            data = color.readline().rstrip('\n\r')
            if data.count('</qgis>') != 0:
                break
            elif data.count("colorRampEntry") != 0:

                #Get the red value
                ind = data.index("red")
                redVal = int(getStringBetween(data[ind+len("red"):ind+len("red")+7], '"', '"'))
                #Get the green value
                ind = data.index("green")
                greenVal = int(getStringBetween(data[ind+len("green"):ind+len("green")+7], '"', '"'))
                #Get the blue value
                ind = data.index("blue")
                blueVal = int(getStringBetween(data[ind+len("blue"):ind+len("blue")+7], '"', '"'))
                #Get the Class Name
                ind = data.index("label")
                ClassName = getStringBetween(data[ind+len("label"):ind+len(data)], '"', '"')
                #Get the Class Number
                ind = data.index("value")
                ClassNum = getStringBetween(data[ind+len("value"):ind+len(data)], '"', '"').split(".")[0]

                #get the FScore
                for ClassNumber, FScore in classifRes:
                    if ClassNumber == ClassNum:
                        lineData.append((ClassNum, ClassName, redVal, greenVal, blueVal, FScore))
                if ClassName == "autres":
                    lineData.append((ClassNum, ClassName, redVal, greenVal, blueVal))

        color.close()
        for i in range(len(lineData)):
            if lineData[i][1] != "autres":
                htmlFile.write('\n\
					<tr>\n\
					<td class="org-left"><FONT style="BACKGROUND-COLOR: rgb(%d,%d,%d)"> %s: %s</FONT></td>\n\
					<td class="org-right">%f</td>\n\
					</tr>'%(lineData[i][2], lineData[i][3], lineData[i][4], lineData[i][0], lineData[i][1], lineData[i][5]))
            else:
                """
				#pour respecter ce qui est dans le fichier de couleurs
				htmlFile.write('\n\
					<tr>\n\
					<td class="org-left"><FONT style="BACKGROUND-COLOR: rgb(%d,%d,%d)"> %d: %s</FONT></td>\n\
					<td class="org-right">&#xa0;</td>\n\
					</tr>'%(lineData[i][2],lineData[i][3],lineData[i][4],lineData[i][0],lineData[i][1]))
                """
                htmlFile.write('\n\
					<tr>\n\
					<td class="org-left"><FONT style="BACKGROUND-COLOR: rgb(255,255,255)"> 255/0: No data</FONT></td>\n\
					<td class="org-right">&#xa0;</td>\n\
					</tr>')
        htmlFile.write('</tbody>\n\
					<tbody>\n\
					<tr>\n\
					<td class="org-left">OA</td>\n\
					<td class="org-right">%s</td>\n\
					</tr>\n\
					</tbody>\n\
				</table>\n\
				</div>\n\
			</div>\n\
			<div id = "Optionspanel" style = "float: left;height: 5%%;width: 60%%;border: 0px solid black;margin: 0px;">\n\
				<div id = "selectBoite" style = "width: 20%%;float: left;border: 0px solid black;margin: 1%%">\n\
					<select id="layer-select" style="float: left">\n\
       						<option value="Aerial">Aerial</option>\n\
       						<option value="AerialWithLabels" selected>Aerial with labels</option>\n\
       						<option value="Road">Roads</option>\n\
					</select>\n\
				</div>\n\
				<div id = "Classification" style = "height: 100%%;width: 40%%;float: left;border: 0px solid black" >\n\
					<table>\n\
						<tr>\n\
						<td>opacity :</td>\n\
       						<td><span id="opacity"></span></td>\n\
       						<td><input id = "opa" type="range" min="0" max="1" step="0.01"/></td>\n\
     						</tr>\n\
					</table>\n\
				</div>\n\
				<div id = "Coordinates" style = "height: 100%%;width: 33%%;float: right;border: 0px solid black;margin: 1%%">\n\
				</div>\n\
			</div>\n\
\n\
\n\
		</div>\n\
	</div>\n\
\n\
\n\
</div>\n\
<div id="left-panel"  style="color: #FFF">\n\
	<div align = "right"><b>></b></div>\n\
	<p><b>List of classifications :</b></p>'%(OA))
        for classifName2, results in listClassif:
            pathHref = pathOut+"/"+classifName2+".html"
            if classifName2 == classifName:
                htmlFile.write('\n\
	<p><a href="%s" style="color: #FFF">%s</a> <b><</b> </p>'%(pathHref, classifName2))
            else:
                htmlFile.write('\n\
	<p><a href="%s" style="color: #FFF">%s</a></p>'%(pathHref, classifName2))
        htmlFile.write('\n\
</div>\n\
<script type="text/javascript">\n\
  function showLeftPanel() {\n\
    var elem = document.getElementById("left-panel");\n\
    elem.classList.toggle("show");\n\
  }\n\
</script>\n\
<script>\n\
\n\
\n\
var styles = [\n\
  "'"Road"'",\n\
  "'"Aerial"'",\n\
  "'"AerialWithLabels"'"\n\
];\n\
\n\
var mousePositionControl = new ol.control.MousePosition({\n\
  coordinateFormat: ol.coordinate.createStringXY(4),\n\
  projection: "EPSG:4326",\n\
  className: "custom-mouse-position",\n\
  target: document.getElementById("Coordinates"),\n\
  undefinedHTML: "&nbsp;"\n\
});\n\
\n\
var scaleLineControl = new ol.control.ScaleLine();\n\
scaleLineControl.setUnits("metric");\n\
\n\
var layers = [];\n\
var i, ii;\n\
for (i = 0, ii = styles.length; i < ii; ++i) {\n\
  layers.push(new ol.layer.Tile({\n\
    visible: false,\n\
    preload: Infinity,\n\
    source: new ol.source.BingMaps({\n\
      key: "Ak-dzM4wZjSqTlzveKz5u0d4IQ4bRzVI309GxmkgSVr1ewS6iPSrOvOKhA-CJlm3",\n\
      imagerySet: styles[i]\n\
\n\
    })\n\
  }));\n\
}\n\
var view = new ol.View({\n\
	center: ol.proj.fromLonLat([1.209533, 44.337733]),\n\
	zoom: 5\n\
		});\n\
var map = new ol.Map({\n\
	layers: layers,\n\
	loadTilesWhileInteracting: true,\n\
	target: "'"map"'",\n\
	view: view,\n\
	controls: ol.control.defaults({\n\
    attributionOptions: /** @type {olx.control.AttributionOptions} */ ({\n\
      collapsible: false\n\
    })\n\
  }).extend([\n\
    scaleLineControl,mousePositionControl\n\
  ]),\n\
});\n\
\n\
\n\
\n\
var classif = new ol.layer.Tile({\n\
            source: new ol.source.TileWMS({\n\
            	preload: Infinity,\n\
            	url: "%s",\n\
            	serverType:"geoserver",\n\
            	params:{"LAYERS":"%s", "'"TILED"'":true}\n\
            })\n\
\n\
});\n\
\n\
var select = document.getElementById("layer-select");\n\
var selectOpa = document.getElementById("opa");\n\
var PixInfo = document.getElementById("'"information"'");\n\
\n\
var viewProjection = view.getProjection();\n\
var viewResolution = view.getResolution();\n\
\n\
function onChange() {\n\
  var style = select.value;\n\
  for (var i = 0, ii = layers.length; i < ii; ++i) {\n\
    layers[i].setVisible(styles[i] === style);\n\
  }\n\
}\n\
\n\
function OpaChange() {\n\
	var opcity = selectOpa.value;\n\
	classif.setOpacity(opcity)\n\
}\n\
\n\
map.on("'"click"'", function(evt) {\n\
  var viewResolution = /** @type {number} */ (view.getResolution());\n\
  var coordinate = evt.coordinate;\n\
  var url = classif.getSource().getGetFeatureInfoUrl(\n\
      coordinate, viewResolution, viewProjection,\n\
      {"INFO_FORMAT": "text/html",\n\
       "propertyName": "PALETTE_INDEX"});\n\
  if (url) {\n\
   var iframe = '"'<iframe seamless src="'"'"' + url + '"'"'" width = "'"350"'" height = "'"150"'" style="'"border:none"'" ></iframe>'"';\n\
    PixInfo.innerHTML = iframe\n\
\n\
\n\
  }\n\
});\n\
\n\
select.addEventListener("'"change"'", onChange);\n\
selectOpa.addEventListener("'"change"'", OpaChange);\n\
\n\
onChange();\n\
OpaChange();\n\
map.addLayer(classif)\n\
\n\
</script>\n\
</body>\n\
</html>'%(urlserveur, classifName))
        htmlFile.close()


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print "Usage: "+sys.argv[0]+" server_url style_file output_path classif_1 metrics_1 [classif_12 metrics_2 ... classif_n metrics_n]"
        print "Example: python "+sys.argv[0]+" \"http://cyan.ups-tlse.fr:8080/geoserver/SudOuest/wms?\" FR_ALLCLASSES.qml /tmp/html \"SudOuest:OSOV1\" MetricsV1.txt \"SudOuest:OSOV2\" MetricsV2.txt "
    else:
        urlserveur = sys.argv[1]
        colorFile = sys.argv[2]
        pathOut = sys.argv[3]
        listClassif = [(sys.argv[i], sys.argv[i+1]) for i in range(4, len(sys.argv), 2)]
        generate(listClassif, colorFile, pathOut, urlserveur)
