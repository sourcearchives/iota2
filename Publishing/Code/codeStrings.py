#!/usr/bin/python
#-*- coding: utf-8 -*-


JS_headers ="\n\
/* =========================================================================\n\
   Program:   iota2\n\
\n\
   Copyright (c) CESBIO. All rights reserved.\n\
\n\
   See LICENSE for details.\n\
\n\
   This software is distributed WITHOUT ANY WARRANTY; without even\n\
   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR\n\
   PURPOSE.  See the above copyright notices for more information.\n\
\n\
=========================================================================\n\
*/\n\
\n\
(function() {\n\
\n\
var selectOpa = document.getElementById('opa');\n\
"

var_Classif="\n\
var %s = new ol.layer.Tile({\n\
		title: '%s',\n\
		visible: %s,\n\
           	source: new ol.source.TileWMS({\n\
            	url: '%s',\n\
            	serverType:'geoserver',\n\
            	params:{'LAYERS':'%s', 'TILED':true}\n\
           	})\n\
		})\n\
"
var_layerSwitcher = "\n\
var layerSwitcher = new ol.control.LayerSwitcher({\n\
	tipLabel: 'Legend' // Optional label for button\n\
});\n\
"
var_mousePositionControl = "\n\
var mousePositionControl = new ol.control.MousePosition({\n\
  coordinateFormat: ol.coordinate.createStringXY(4),\n\
  projection: 'EPSG:4326',\n\
  className: 'custom-mouse-position',\n\
  target: document.getElementById('Coordinates'),\n\
  undefinedHTML: '&nbsp;'\n\
});\n\
"

var_scaleLineControl = "\n\
var scaleLineControl = new ol.control.ScaleLine();\n\
scaleLineControl.setUnits('metric');\n\
"

var_Bings = "\n\
var %s = new ol.layer.Tile({\n\
		title: '%s',\n\
		type: 'base',\n\
		visible: %s,\n\
    		source: new ol.source.BingMaps({\n\
      		key: '%s',\n\
      		imagerySet: '%s',\n\
    		})\n\
		})\n\
"

var_mapHeaders = "\n\
var map = new ol.Map({\n\
"
var_mapOptions = "\n\
	target: 'map',\n\
	controls: ol.control.defaults({\n\
    		attributionOptions: /** @type {olx.control.AttributionOptions} */ ({\n\
      		collapsible: false\n\
    		})\n\
  	}).extend([\n\
    		scaleLineControl,mousePositionControl\n\
  	]),\n\
	view: new ol.View({\n\
          center: ol.proj.fromLonLat([1.209533, 44.337733]),\n\
          zoom: 4\n\
        }),\n\
"

var_mapLayers_head = "\n\
        layers: [\n\
            new ol.layer.Group({\n\
                'title': 'Base maps',\n\
                layers: ["

var_mapLayers_overlays = "\n\
            new ol.layer.Group({\n\
                title: 'Overlays',\n\
                layers: ["

html_headers = '\n\
<!DOCTYPE html>\n\
<html>\n\
  <head>\n\
    <meta charset="utf-8" />\n\
    <title>Visualisation des classifications</title>\n\
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no, width=device-width">\n\
    <link rel="stylesheet" href="http://openlayers.org/en/v3.11.2/css/ol.css" type="text/css">\n\
    <link rel="stylesheet" href="%s">\n\
    <link rel="stylesheet" href="layer.css" />\n\
    <script src="http://openlayers.org/en/v3.11.2/build/ol.js"></script>\n\
    <script src="%s"></script>\n\
  </head>\n\
  <body>\n\
\n\
    <div id="map"></div>\n\
	<div id="left-panel"  style="color: #FFF">\n\
	<div align = "right"><b>></b></div>\n\
	<form name=form1 style="float: left;">\n\
		<table border=0 BORDERCOLOR=RED width=''250'' cellspacing=''0'' cellpadding=''0'' align=center>\n\
			<tr><td > </td><td ><b>display results</b></td></tr>\n\
'
html_head_res = '\n\
		</table>\n\
	</form>\n\
    </div>\n\
    \n\
    <div class = RES id="InfoPanel" style = "border: 1px solid white" > \n\
	<div style="float: left;border: 1px solid white;width:5%">opacity</div> <input id = "opa" type="range" min="0" max="1" step="0.01"/><div id="Coordinates" style="border: 1px solid white;float: right;width:50%"></div>\n\
    </div>\n\
\n\
    <div class = RES id="RES" style = "border: 0px solid black" >\n\
'

html_end = '\n\
</div>\n\
    </div>\n\
    \n\
    <script>\n\
     function showLeftPanel() \n\
	{\n\
    	var elem = document.getElementById("left-panel");\n\
    	elem.classList.toggle("show");\n\
  	}\n\
    function affiche(element)\n\
	{\n\
    		var targetElement = document.getElementById(element) ;\n\
    		if (targetElement.style.display == "none")\n\
    		{\n\
        		targetElement.style.display = "" ;\n\
    		}\n\
        	else\n\
        	{\n\
        	targetElement.style.display = "none" ;\n\
    		}\n\
	}\n\
	function chkcontrol(j,element) {\n\
	var total=0;\n\
	var targetElement = document.getElementById(element) ;\n\
    			if (targetElement.style.display == "none")\n\
    			{\n\
        			targetElement.style.display = "" ;\n\
    			}\n\
        		else\n\
        		{\n\
        		targetElement.style.display = "none" ;\n\
    			}\n\
	for(var i=0; i < document.form1.ckb.length; i++){\n\
		if(document.form1.ckb[i].checked){\n\
			total =total +1;\n\
			\n\
			}\n\
		\n\
		if(total > 2){\n\
			if (targetElement.style.display != "none")\n\
    			{\n\
        			targetElement.style.display =  "none" ;\n\
    			}\n\
			alert("Please Select only two classifications results") \n\
			document.form1.ckb[j-1].checked = false ;	\n\
			return false;\n\
			}\n\
		}\n\
		\n\
		\n\
	}\n\
    </script>\n\
    <script src="layer.js"></script>\n\
'

CSS_File = "\n\
html, body {\n\
  height: 100%;\n\
  padding: 0;\n\
  margin: 0;\n\
  font-family: sans-serif;\n\
  font-size: small;\n\
}\n\
\n\
#map {\n\
  width: 100%;\n\
  height: 50%;\n\
}\n\
#RES {\n\
  width: 100%;\n\
  height: 50%;\n\
}\n\
\n\
#left-panel {\n\
  width: 15%;\n\
  height: 15%;\n\
  border: 3px solid rgba(160,160,160,0.6);\n\
  background-color: rgba(51,89,131,0.6);\n\
  position: absolute;\n\
  top: 20%;\n\
  left: -15%;\n\
  border-radius: 0 1em 1em 0;\n\
  padding: 1%;\n\
  -webkit-transition: all 0.5s ease-in-out;\n\
	  -moz-transition: all 0.25s ease-in-out;\n\
	-o-transition: all 0.25s ease-in-out;\n\
}\n\
\n\
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
.score {\n\
  		 width: 100%;\n\
		 float: left\n\
		 height: 80%;\n\
		 border: 1px solid white;\n\
		 margin: 5px;\n\
	         }\n\
\n\
.legend { list-style: none; }\n\
.legend li { float: left; margin-right: 10px; }\n\
.legend span { border: 1px solid #ccc; float: left; width: 12px; height: 12px; margin: 2px; }\n\
\n\
.legend .Sunflower { background-color: rgba(120,0,0,1); }\n\
.legend .Sugarbeet { background-color: rgba(0,170,0,1); }\n\
.legend .Rice { background-color: rgba(170,110,135,1); }\n\
.legend .Maize { background-color: rgba(255,133,10,1); }\n\
"










