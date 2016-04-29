
/* =========================================================================
   Program:   iota2

   Copyright (c) CESBIO. All rights reserved.

   See LICENSE for details.

   This software is distributed WITHOUT ANY WARRANTY; without even
   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
   PURPOSE.  See the above copyright notices for more information.

=========================================================================
*/

(function() {

var selectOpa = document.getElementById('opa');

var resultat_2009 = new ol.layer.Tile({
		title: 'Classification 2009',
		visible: true,
           	source: new ol.source.TileWMS({
            	url: 'http://cyan.ups-tlse.fr:8080/geoserver/SudOuest/wms?',
            	serverType:'geoserver',
            	params:{'LAYERS':'SudOuest:CES_OSO_ClassifV1_index', 'TILED':true}
           	})
		})

var resultat_2010 = new ol.layer.Tile({
		title: 'Classification 2010',
		visible: false,
           	source: new ol.source.TileWMS({
            	url: 'http://cyan.ups-tlse.fr:8080/geoserver/SudOuest/wms?',
            	serverType:'geoserver',
            	params:{'LAYERS':'SudOuest:CES_OSO_ClassifV2_index', 'TILED':true}
           	})
		})

var resultat_2011 = new ol.layer.Tile({
		title: 'Classification 2011',
		visible: false,
           	source: new ol.source.TileWMS({
            	url: 'http://cyan.ups-tlse.fr:8080/geoserver/SudOuest/wms?',
            	serverType:'geoserver',
            	params:{'LAYERS':'SudOuest:Mosaic_France2014_V1_ColorIndexedT', 'TILED':true}
           	})
		})

var Aerial = new ol.layer.Tile({
		title: 'Aerial',
		type: 'base',
		visible: true,
    		source: new ol.source.BingMaps({
      		key: 'Ap85vwFYkp6CUJP6RI_8jyCacpNw_E6u0wRl1uovaTr0lrxcUxcRQKVEEhTa5DPG',
      		imagerySet: 'Aerial',
    		})
		})

var AerialWithLabels = new ol.layer.Tile({
		title: 'AerialWithLabels',
		type: 'base',
		visible: false,
    		source: new ol.source.BingMaps({
      		key: 'Ap85vwFYkp6CUJP6RI_8jyCacpNw_E6u0wRl1uovaTr0lrxcUxcRQKVEEhTa5DPG',
      		imagerySet: 'AerialWithLabels',
    		})
		})

var Road = new ol.layer.Tile({
		title: 'Road',
		type: 'base',
		visible: false,
    		source: new ol.source.BingMaps({
      		key: 'Ap85vwFYkp6CUJP6RI_8jyCacpNw_E6u0wRl1uovaTr0lrxcUxcRQKVEEhTa5DPG',
      		imagerySet: 'Road',
    		})
		})

var layerSwitcher = new ol.control.LayerSwitcher({
	tipLabel: 'Legend' // Optional label for button
});

var mousePositionControl = new ol.control.MousePosition({
  coordinateFormat: ol.coordinate.createStringXY(4),
  projection: 'EPSG:4326',
  className: 'custom-mouse-position',
  target: document.getElementById('Coordinates'),
  undefinedHTML: '&nbsp;'
});

var scaleLineControl = new ol.control.ScaleLine();
scaleLineControl.setUnits('metric');

var map = new ol.Map({

	target: 'map',
	controls: ol.control.defaults({
    		attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
      		collapsible: false
    		})
  	}).extend([
    		scaleLineControl,mousePositionControl
  	]),
	view: new ol.View({
          center: ol.proj.fromLonLat([1.209533, 44.337733]),
          zoom: 4
        }),

        layers: [
            new ol.layer.Group({
                'title': 'Base maps',
                layers: [Aerial,AerialWithLabels,Road]}),

            new ol.layer.Group({
                title: 'Overlays',
                layers: [resultat_2009,resultat_2010,resultat_2011]}),
]});

	function OpaChange() {
var opcity = selectOpa.value;
resultat_2009.setOpacity(opcity);
resultat_2010.setOpacity(opcity);
resultat_2011.setOpacity(opcity);

}

	selectOpa.addEventListener('change', OpaChange);
	OpaChange();
   	map.addControl(layerSwitcher);
})();