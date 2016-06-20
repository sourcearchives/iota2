







function mpld3_load_lib(url, callback){
  var s = document.createElement('script');
  s.src = url;
  s.async = true;
  s.onreadystatechange = s.onload = callback;
  s.onerror = function(){console.warn("failed to load library " + url);};
  document.getElementsByTagName("head")[0].appendChild(s);
}

if(typeof(mpld3) !== "undefined" && mpld3._mpld3IsLoaded){
   // already loaded: just create the figure
   !function(mpld3){
       
       mpld3.draw_figure("resultat_2011", {"axes": [{"xlim": [0.0, 1.3959999999999999], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [{"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.864", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, -0.09999999999999998], "rotation": -0.0, "id": "el12009140631944558480"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.968", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 0.9], "rotation": -0.0, "id": "el12009140631944558928"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.616", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 1.9000000000000001], "rotation": -0.0, "id": "el12009140631944559504"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.249", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 2.9000000000000004], "rotation": -0.0, "id": "el12009140631944518544"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.534", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 3.9000000000000004], "rotation": -0.0, "id": "el12009140631944516880"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.816", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 4.8999999999999995], "rotation": -0.0, "id": "el12009140631944989328"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.582", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 5.8999999999999995], "rotation": -0.0, "id": "el12009140631944585296"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.996", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 6.8999999999999995], "rotation": -0.0, "id": "el12009140631944586384"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.282", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 7.8999999999999995], "rotation": -0.0, "id": "el12009140631944587472"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.859", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 8.9], "rotation": -0.0, "id": "el12009140631944588560"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.092", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 9.9], "rotation": -0.0, "id": "el12009140631944634768"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.515", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 10.9], "rotation": -0.0, "id": "el12009140631944635856"}, {"v_baseline": "hanging", "h_anchor": "middle", "color": "#000000", "text": "F-score", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [0.49999999999999989, -0.0625], "rotation": -0.0, "id": "el12009140631945315408"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "Classification 2011,\tK : 0.878,\tOA : 0.916", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 14.399999999999999, "position": [0.49999999999999989, 1.0144675925925926], "rotation": -0.0, "id": "el12009140631950113232"}], "zoomable": true, "images": [], "xdomain": [0.0, 1.3959999999999999], "ylim": [-2.0, 12.0], "paths": [{"edgecolor": "#000000", "facecolor": "#FF5500", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data01", "id": "el12009140631945127696"}, {"edgecolor": "#000000", "facecolor": "#FFFF7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data02", "id": "el12009140631945129296"}, {"edgecolor": "#000000", "facecolor": "#AAFF00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data03", "id": "el12009140631945184272"}, {"edgecolor": "#000000", "facecolor": "#55AA7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data04", "id": "el12009140631945185936"}, {"edgecolor": "#000000", "facecolor": "#FF00FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data05", "id": "el12009140631945187216"}, {"edgecolor": "#000000", "facecolor": "#FF0000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data06", "id": "el12009140631945238480"}, {"edgecolor": "#000000", "facecolor": "#FFB802", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data07", "id": "el12009140631945240144"}, {"edgecolor": "#000000", "facecolor": "#0000FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data08", "id": "el12009140631944754448"}, {"edgecolor": "#000000", "facecolor": "#BEBEBE", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data09", "id": "el12009140631944756112"}, {"edgecolor": "#000000", "facecolor": "#AAAA00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data10", "id": "el12009140631944811088"}, {"edgecolor": "#000000", "facecolor": "#AAAAFF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data11", "id": "el12009140631944812752"}, {"edgecolor": "#000000", "facecolor": "#550000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data12", "id": "el12009140631944814416"}], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 8, "tickvalues": null}, {"scale": "linear", "tickformat": ["ete", "hiver", "pelouses", "lande ligneuse", "bati", "surfaces minerales", "plages et dunes", "eau", "glaciers ou neiges et", "prairie", "verger", "vigne"], "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 12, "tickvalues": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}], "lines": [], "markers": [], "id": "el12009140631947924880", "ydomain": [-2.0, 12.0], "collections": [], "xscale": "linear", "bbox": [0.23099999999999998, 0.099999999999999978, 0.66900000000000004, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data12": [[0.0, 10.6], [0.515, 10.6], [0.515, 11.4], [0.0, 11.4]], "data11": [[0.0, 9.6], [0.092, 9.6], [0.092, 10.4], [0.0, 10.4]], "data10": [[0.0, 8.6], [0.859, 8.6], [0.859, 9.4], [0.0, 9.4]], "data08": [[0.0, 6.6], [0.996, 6.6], [0.996, 7.3999999999999995], [0.0, 7.3999999999999995]], "data09": [[0.0, 7.6], [0.282, 7.6], [0.282, 8.4], [0.0, 8.4]], "data06": [[0.0, 4.6], [0.816, 4.6], [0.816, 5.3999999999999995], [0.0, 5.3999999999999995]], "data07": [[0.0, 5.6], [0.582, 5.6], [0.582, 6.3999999999999995], [0.0, 6.3999999999999995]], "data04": [[0.0, 2.6], [0.249, 2.6], [0.249, 3.4000000000000004], [0.0, 3.4000000000000004]], "data05": [[0.0, 3.6], [0.534, 3.6], [0.534, 4.4], [0.0, 4.4]], "data02": [[0.0, 0.6], [0.968, 0.6], [0.968, 1.4], [0.0, 1.4]], "data03": [[0.0, 1.6], [0.616, 1.6], [0.616, 2.4000000000000004], [0.0, 2.4000000000000004]], "data01": [[0.0, -0.4], [0.864, -0.4], [0.864, 0.4], [0.0, 0.4]]}, "id": "el12009140631949909136"});
   }(mpld3);
}else if(typeof define === "function" && define.amd){
   // require.js is available: use it to load d3/mpld3
   require.config({paths: {d3: "https://mpld3.github.io/js/d3.v3.min"}});
   require(["d3"], function(d3){
      window.d3 = d3;
      mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
         
         mpld3.draw_figure("resultat_2011", {"axes": [{"xlim": [0.0, 1.3959999999999999], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [{"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.864", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, -0.09999999999999998], "rotation": -0.0, "id": "el12009140631944558480"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.968", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 0.9], "rotation": -0.0, "id": "el12009140631944558928"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.616", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 1.9000000000000001], "rotation": -0.0, "id": "el12009140631944559504"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.249", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 2.9000000000000004], "rotation": -0.0, "id": "el12009140631944518544"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.534", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 3.9000000000000004], "rotation": -0.0, "id": "el12009140631944516880"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.816", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 4.8999999999999995], "rotation": -0.0, "id": "el12009140631944989328"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.582", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 5.8999999999999995], "rotation": -0.0, "id": "el12009140631944585296"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.996", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 6.8999999999999995], "rotation": -0.0, "id": "el12009140631944586384"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.282", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 7.8999999999999995], "rotation": -0.0, "id": "el12009140631944587472"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.859", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 8.9], "rotation": -0.0, "id": "el12009140631944588560"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.092", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 9.9], "rotation": -0.0, "id": "el12009140631944634768"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.515", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 10.9], "rotation": -0.0, "id": "el12009140631944635856"}, {"v_baseline": "hanging", "h_anchor": "middle", "color": "#000000", "text": "F-score", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [0.49999999999999989, -0.0625], "rotation": -0.0, "id": "el12009140631945315408"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "Classification 2011,\tK : 0.878,\tOA : 0.916", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 14.399999999999999, "position": [0.49999999999999989, 1.0144675925925926], "rotation": -0.0, "id": "el12009140631950113232"}], "zoomable": true, "images": [], "xdomain": [0.0, 1.3959999999999999], "ylim": [-2.0, 12.0], "paths": [{"edgecolor": "#000000", "facecolor": "#FF5500", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data01", "id": "el12009140631945127696"}, {"edgecolor": "#000000", "facecolor": "#FFFF7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data02", "id": "el12009140631945129296"}, {"edgecolor": "#000000", "facecolor": "#AAFF00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data03", "id": "el12009140631945184272"}, {"edgecolor": "#000000", "facecolor": "#55AA7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data04", "id": "el12009140631945185936"}, {"edgecolor": "#000000", "facecolor": "#FF00FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data05", "id": "el12009140631945187216"}, {"edgecolor": "#000000", "facecolor": "#FF0000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data06", "id": "el12009140631945238480"}, {"edgecolor": "#000000", "facecolor": "#FFB802", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data07", "id": "el12009140631945240144"}, {"edgecolor": "#000000", "facecolor": "#0000FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data08", "id": "el12009140631944754448"}, {"edgecolor": "#000000", "facecolor": "#BEBEBE", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data09", "id": "el12009140631944756112"}, {"edgecolor": "#000000", "facecolor": "#AAAA00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data10", "id": "el12009140631944811088"}, {"edgecolor": "#000000", "facecolor": "#AAAAFF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data11", "id": "el12009140631944812752"}, {"edgecolor": "#000000", "facecolor": "#550000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data12", "id": "el12009140631944814416"}], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 8, "tickvalues": null}, {"scale": "linear", "tickformat": ["ete", "hiver", "pelouses", "lande ligneuse", "bati", "surfaces minerales", "plages et dunes", "eau", "glaciers ou neiges et", "prairie", "verger", "vigne"], "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 12, "tickvalues": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}], "lines": [], "markers": [], "id": "el12009140631947924880", "ydomain": [-2.0, 12.0], "collections": [], "xscale": "linear", "bbox": [0.23099999999999998, 0.099999999999999978, 0.66900000000000004, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data12": [[0.0, 10.6], [0.515, 10.6], [0.515, 11.4], [0.0, 11.4]], "data11": [[0.0, 9.6], [0.092, 9.6], [0.092, 10.4], [0.0, 10.4]], "data10": [[0.0, 8.6], [0.859, 8.6], [0.859, 9.4], [0.0, 9.4]], "data08": [[0.0, 6.6], [0.996, 6.6], [0.996, 7.3999999999999995], [0.0, 7.3999999999999995]], "data09": [[0.0, 7.6], [0.282, 7.6], [0.282, 8.4], [0.0, 8.4]], "data06": [[0.0, 4.6], [0.816, 4.6], [0.816, 5.3999999999999995], [0.0, 5.3999999999999995]], "data07": [[0.0, 5.6], [0.582, 5.6], [0.582, 6.3999999999999995], [0.0, 6.3999999999999995]], "data04": [[0.0, 2.6], [0.249, 2.6], [0.249, 3.4000000000000004], [0.0, 3.4000000000000004]], "data05": [[0.0, 3.6], [0.534, 3.6], [0.534, 4.4], [0.0, 4.4]], "data02": [[0.0, 0.6], [0.968, 0.6], [0.968, 1.4], [0.0, 1.4]], "data03": [[0.0, 1.6], [0.616, 1.6], [0.616, 2.4000000000000004], [0.0, 2.4000000000000004]], "data01": [[0.0, -0.4], [0.864, -0.4], [0.864, 0.4], [0.0, 0.4]]}, "id": "el12009140631949909136"});
      });
    });
}else{
    // require.js not available: dynamically load d3 & mpld3
    mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){
         mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
                 
                 mpld3.draw_figure("resultat_2011", {"axes": [{"xlim": [0.0, 1.3959999999999999], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [{"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.864", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, -0.09999999999999998], "rotation": -0.0, "id": "el12009140631944558480"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.968", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 0.9], "rotation": -0.0, "id": "el12009140631944558928"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.616", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 1.9000000000000001], "rotation": -0.0, "id": "el12009140631944559504"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.249", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 2.9000000000000004], "rotation": -0.0, "id": "el12009140631944518544"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.534", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 3.9000000000000004], "rotation": -0.0, "id": "el12009140631944516880"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.816", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 4.8999999999999995], "rotation": -0.0, "id": "el12009140631944989328"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.582", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 5.8999999999999995], "rotation": -0.0, "id": "el12009140631944585296"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.996", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 6.8999999999999995], "rotation": -0.0, "id": "el12009140631944586384"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.282", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 7.8999999999999995], "rotation": -0.0, "id": "el12009140631944587472"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.859", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 8.9], "rotation": -0.0, "id": "el12009140631944588560"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.092", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 9.9], "rotation": -0.0, "id": "el12009140631944634768"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "0.515", "coordinates": "data", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [1.196, 10.9], "rotation": -0.0, "id": "el12009140631944635856"}, {"v_baseline": "hanging", "h_anchor": "middle", "color": "#000000", "text": "F-score", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 12.0, "position": [0.49999999999999989, -0.0625], "rotation": -0.0, "id": "el12009140631945315408"}, {"v_baseline": "auto", "h_anchor": "middle", "color": "#000000", "text": "Classification 2011,\tK : 0.878,\tOA : 0.916", "coordinates": "axes", "zorder": 3, "alpha": 1, "fontsize": 14.399999999999999, "position": [0.49999999999999989, 1.0144675925925926], "rotation": -0.0, "id": "el12009140631950113232"}], "zoomable": true, "images": [], "xdomain": [0.0, 1.3959999999999999], "ylim": [-2.0, 12.0], "paths": [{"edgecolor": "#000000", "facecolor": "#FF5500", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data01", "id": "el12009140631945127696"}, {"edgecolor": "#000000", "facecolor": "#FFFF7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data02", "id": "el12009140631945129296"}, {"edgecolor": "#000000", "facecolor": "#AAFF00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data03", "id": "el12009140631945184272"}, {"edgecolor": "#000000", "facecolor": "#55AA7F", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data04", "id": "el12009140631945185936"}, {"edgecolor": "#000000", "facecolor": "#FF00FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data05", "id": "el12009140631945187216"}, {"edgecolor": "#000000", "facecolor": "#FF0000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data06", "id": "el12009140631945238480"}, {"edgecolor": "#000000", "facecolor": "#FFB802", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data07", "id": "el12009140631945240144"}, {"edgecolor": "#000000", "facecolor": "#0000FF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data08", "id": "el12009140631944754448"}, {"edgecolor": "#000000", "facecolor": "#BEBEBE", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data09", "id": "el12009140631944756112"}, {"edgecolor": "#000000", "facecolor": "#AAAA00", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data10", "id": "el12009140631944811088"}, {"edgecolor": "#000000", "facecolor": "#AAAAFF", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data11", "id": "el12009140631944812752"}, {"edgecolor": "#000000", "facecolor": "#550000", "edgewidth": 1.0, "pathcodes": ["M", "L", "L", "L", "Z"], "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 1, "alpha": 0.4, "xindex": 0, "data": "data12", "id": "el12009140631944814416"}], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 8, "tickvalues": null}, {"scale": "linear", "tickformat": ["ete", "hiver", "pelouses", "lande ligneuse", "bati", "surfaces minerales", "plages et dunes", "eau", "glaciers ou neiges et", "prairie", "verger", "vigne"], "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 12, "tickvalues": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}], "lines": [], "markers": [], "id": "el12009140631947924880", "ydomain": [-2.0, 12.0], "collections": [], "xscale": "linear", "bbox": [0.23099999999999998, 0.099999999999999978, 0.66900000000000004, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data12": [[0.0, 10.6], [0.515, 10.6], [0.515, 11.4], [0.0, 11.4]], "data11": [[0.0, 9.6], [0.092, 9.6], [0.092, 10.4], [0.0, 10.4]], "data10": [[0.0, 8.6], [0.859, 8.6], [0.859, 9.4], [0.0, 9.4]], "data08": [[0.0, 6.6], [0.996, 6.6], [0.996, 7.3999999999999995], [0.0, 7.3999999999999995]], "data09": [[0.0, 7.6], [0.282, 7.6], [0.282, 8.4], [0.0, 8.4]], "data06": [[0.0, 4.6], [0.816, 4.6], [0.816, 5.3999999999999995], [0.0, 5.3999999999999995]], "data07": [[0.0, 5.6], [0.582, 5.6], [0.582, 6.3999999999999995], [0.0, 6.3999999999999995]], "data04": [[0.0, 2.6], [0.249, 2.6], [0.249, 3.4000000000000004], [0.0, 3.4000000000000004]], "data05": [[0.0, 3.6], [0.534, 3.6], [0.534, 4.4], [0.0, 4.4]], "data02": [[0.0, 0.6], [0.968, 0.6], [0.968, 1.4], [0.0, 1.4]], "data03": [[0.0, 1.6], [0.616, 1.6], [0.616, 2.4000000000000004], [0.0, 2.4000000000000004]], "data01": [[0.0, -0.4], [0.864, -0.4], [0.864, 0.4], [0.0, 0.4]]}, "id": "el12009140631949909136"});
            })
         });
}
