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
var_container = "\n\
var container = document.getElementById('popup');\n\
	var content = document.getElementById('popup-content');\n\
	var closer = document.getElementById('popup-closer');\n\
\n\
	var overlay = new ol.Overlay( ({\n\
	element: container,\n\
	autoPan: true,\n\
	autoPanAnimation: {\n\
	duration: 250\n\
	}\n\
	}));\n\
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
	overlays: [overlay],\n\
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

var_filterHeader = "\n\
fetch(url).then(function(response) {\n\
        return response.json();\n\
      }).then(function(json) {\n\
	  var coords = [];\n\
	  var Allfeatures = json.features\n\
	  for (var ii=0;ii<Allfeatures.length;ii++){\n\
	      coords.push(json.features[ii].geometry.coordinates);\n\
	  }\n\
	 var f = new ol.Feature(new ol.geom.MultiPolygon(coords[0]));\n\
	 var crop = new ol.filter.Crop({ feature: f, inner:false });\n\
"

var_filterLayer = "\
	 %s.addFilter(crop);\n\
"

var_control = "\n\
	closer.onclick = function() {\n\
        overlay.setPosition(undefined);\n\
        closer.blur();\n\
        return false;\n\
     	 };\n\
	\n\
	panel = new ol.control.Control(\n\
		{'displayClass': 'olControlEditingToolbar'}\n\
		);\n\
	\n\
	controls = {};\n\
"
var_mapEvent = "\n\
    map.on('singleclick', function(evt) {\n\
\n\
	activelayer = [];\n\
    	map.getLayers().forEach(function(layer, i) {\n\
        if (layer instanceof ol.layer.Group) {\n\
        if (layer.get('title') == 'Overlays'){\n\
            layer.getLayers().forEach(function(sublayer, j) {\n\
            activelayer.push([sublayer.get('title'),sublayer.get('visible')]);\n\
            });\n\
        }\n\
        }\n\
    	});\n\
\n\
	if (activelayer[activelayer.length - 1][1] == false){\n\
        if (activelayer[activelayer.length - 2][1] == false){\n\
        	var source = %s.getSource();\n\
        	var typesource = 'classif';\n\
        	} \n\
        	else\n\
        	{\n\
        	var source = %s.getSource();\n\
        	var typesource = 'valid';\n\
        	}\n\
    	}\n\
    	else\n\
    	{\n\
        	var source = %s.getSource();\n\
        	var typesource = 'conf';\n\
    	}\n\
\n\
	var coordinate = evt.coordinate;\n\
\n\
	var view = map.getView()\n\
	var viewResolution = view.getResolution();\n\
	var url = source.getGetFeatureInfoUrl(evt.coordinate, viewResolution, 'EPSG:3857',\n\
						 {'INFO_FORMAT': 'text/javascript',\n\
						  'propertyName':'PALETTE_INDEX'\n\
						 });\n\
	if (url) {\n\
	    var parser = new ol.format.GeoJSON();\n\
            $.ajax({\n\
		url: url,\n\
		dataType: 'jsonp',\n\
		jsonpCallback: 'parseResponse',\n\
	    }).then(function(response) {\n\
		var result = parser.readFeatures(response);\n\
		if (result.length) {\n\
		    var info = [];\n\
		    for (var i = 0, ii = result.length; i < ii; ++i) {\n\
			info.push(result[i].get('PALETTE_INDEX'));\n\
		    }\n\
			if (typesource == 'classif'){\n\
            content.innerHTML = '<p>Classe :&nbsp;&nbsp;<b>' + dict[info.join(', ')] + '</b></p>' ;\n\
            }\n\
            else\n\
            {\n\
            if (typesource == 'valid'){\n\
            content.innerHTML = '<p>Validité :&nbsp;&nbsp;<b>' + info.join(', ') + '&nbsp; dates</b></p>' ;\n\
            }\n\
            else\n\
            {\n\
"

var_mapEventTAIL="\n\
                content.innerHTML = '<p>Confiance :&nbsp;&nbsp;<b>' + info.join(', ') + '&nbsp; %</b></p>' ;\n\
            }\n\
            }\n\
			overlay.setPosition(coordinate);\n\
\n\
		} else {\n\
		}\n\
	    });\n\
	}\n\
	});\n\
"

html_headers = '\n\
<!DOCTYPE html>\n\
<html>\n\
  <head>\n\
    <meta charset="utf-8" />\n\
    <title>Visualisation des classifications</title>\n\
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no, width=device-width">\n\
    <link rel="stylesheet" href="http://openlayers.org/en/v3.11.2/css/ol.css" type="text/css">\n\
    <script src="http://code.jquery.com/jquery-1.11.0.min.js"></script>\n\
    <script src="ol3-popup.js"></script>\n\
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

html_headers_oneClassification = '\n\
<!DOCTYPE html>\n\
<html>\n\
  <head>\n\
    <meta charset="utf-8" />\n\
    <title>Visualisation des classifications</title>\n\
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no, width=device-width">\n\
    <link rel="stylesheet" href="http://openlayers.org/en/v3.11.2/css/ol.css" type="text/css">\n\
    <script src="http://code.jquery.com/jquery-1.11.0.min.js"></script>\n\
    <link rel="stylesheet" href="%s">\n\
    <link rel="stylesheet" href="layer.css" />\n\
    <script src="http://openlayers.org/en/v3.11.2/build/ol.js"></script>\n\
    <script src="ol3-popup.js"></script>\n\
    <script src="%s"></script>\n\
  </head>\n\
  <body>\n\
\n\
    <div id="map"></div>'

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

html_head_res_oneClassification = '\n\
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
htmlHEADER="\n\
<!DOCTYPE html>\n\
<html>\n\
  <head>\n\
    <meta charset=\"utf-8\" />\n\
    <title>Visualisation des classifications</title>\n\
    <meta name=\"viewport\" content=\"initial-scale=1.0, user-scalable=no, width=device-width\">\n\
	<link rel=\"stylesheet\" href=\"https://openlayers.org/en/v4.1.0/css/ol.css\" type=\"text/css\">\n\
    <script src=\"http://code.jquery.com/jquery-1.11.0.min.js\"></script>\n\
    <link rel=\"stylesheet\" href=\"osgis-ol3-leaflet-master/ol3/lib/ol3-layerswitcher/src/ol3-layerswitcher.css\">\n\
    <link rel=\"stylesheet\" href=\"layer.css\" />\n\
    <script src=\"https://openlayers.org/en/v4.1.0/build/ol.js\"></script>\n\
    <script src=\"ol3-popup.js\"></script>\n\
    <script src=\"osgis-ol3-leaflet-master/ol3/lib/ol3-layerswitcher/src/ol3-layerswitcher.js\"></script>\n\
    	<script src=\"https://mapbox.github.io/geojson-vt/geojson-vt-dev.js\"></script>\n\
    \n\
	<script type=\"text/javascript\" src=\"filter.js\"></script>\n\
	<script type=\"text/javascript\" src=\"maskfilter.js\"></script>\n\
	<script type=\"text/javascript\" src=\"cropfilter.js\"></script>\n\
\n\
	<script type=\"text/javascript\" src=\"jqExportMap.js\"></script>\n\
	<script type=\"text/javascript\" src=\"https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.2/jspdf.min.js\"></script>\n\
	<script src=\"https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/1.3.3/FileSaver.min.js\"></script>\n\
\n\
  </head>\n\
  <body>\n\
\n\
    <div id=\"map\" style=\"border: 1px solid white;float: center;width:100%\">\n\
    </div>\n\
	<div id=\"popup\" class=\"ol-popup\">\n\
      <a href=\"#\" id=\"popup-closer\" class=\"ol-popup-closer\"></a>\n\
      <div id=\"popup-content\"></div>\n\
    </div>\n\
    <div class = RES id=\"InfoPanel\" style = \"border: 1px solid white\" > \n\
	<div style=\"float: left;border: 1px solid white;width:5%\">Opacité</div> \n\
		<input id = \"opa\" type=\"range\" min=\"0\" max=\"1\" step=\"0.01\">\n\
	<div id=\"Coordinates\" style=\"border: 1px solid white;float: right;width:50%\"></div>\n\
    </div>\n\
"
htmdRES = "\n\
	<div id=resultat_2016 style=\"border: 1px solid white;float: left;width:100%\"></div>\n\
	<div style=\"float: center;border: 1px solid white;width:100%\"> Les produits OSO sont diffusés sous licence ODC-BY 1.0 : <a href=\"https://opendatacommons.org/licenses/by/\">Open Data Commons License </a> </div>\n\
<script src=\"layer.js\"></script>\n\
"
htmlTAIL = "\n\
	<div style=\"float: center;border: 1px solid white;width:100%\"> Les produits OSO sont diffusés sous licence ODC-BY 1.0 : <a href=\"https://opendatacommons.org/licenses/by/\">Open Data Commons License </a> </div>\n\
<script src=\"layer.js\"></script>\n\
"
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
.ol-popup-content {\n\
    position: absolute;\n\
    background-color: white;\n\
    -webkit-filter: drop-shadow(0 1px 4px rgba(0,0,0,0.2));\n\
    filter: drop-shadow(0 1px 4px rgba(0,0,0,0.2));\n\
    padding: 15px;\n\
    border-radius: 10px;\n\
    border: 1px solid #cccccc;\n\
    bottom: 12px;\n\
    left: -50px;\n\
    min-width: 200px;\n\
}\n\
.legend { list-style: none; }\n\
.legend li { float: left; margin-right: 10px; }\n\
.legend span { border: 1px solid #ccc; float: left; width: 12px; height: 12px; margin: 2px; }\n\
\n\
.legend .Sunflower { background-color: rgba(120,0,0,1); }\n\
.legend .Sugarbeet { background-color: rgba(0,170,0,1); }\n\
.legend .Rice { background-color: rgba(170,110,135,1); }\n\
.legend .Maize { background-color: rgba(255,133,10,1); }\n\
"










