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

import figureClassification as figClassif
import codeStrings as CS
from config import Config
import argparse,shutil,errno,os
import figureClassification

"""
python generateHTML.py -config /home/vincenta/IOTA/Publishing/publishing.cfg
"""

def updateDirectory(src, dst):

    content = os.listdir(src)
    for currentContent in content:
        if os.path.isfile(src+"/"+currentContent):
            if not os.path.exists(dst+"/"+currentContent):
                shutil.copy(src+"/"+currentContent,dst+"/"+currentContent)
        if os.path.isdir(src+"/"+currentContent):
            if not os.path.exists(dst+"/"+currentContent):
                try:
                    shutil.copytree(src+"/"+currentContent, dst+"/"+currentContent)
                except OSError as exc: # python >2.5
                    if exc.errno == errno.ENOTDIR:
                        shutil.copy(src, dst)
                    else: raise


def filterLayer(AllLayers,file_JS):
	
	for currentLayerName in AllLayers:
		file_JS.write(CS.var_filterLayer%(currentLayerName))

def addClassDescription(classDescriptions,file_JS):

	file_JS.write("\tvar dict = {\n")
	stringList = ["\t"+str(classNumber)+":\""+label+"\"" for classNumber,label,r,g,b in classDescriptions]
	stringDico = ",\n".join(stringList)
	file_JS.write(stringDico)
	file_JS.write("\n\t};\n")

def generateOneClassificationHTML(cfgFile):
	f = file(cfgFile)
	cfg = Config(f)

	workingDirectory = cfg.Global_parameters.workingDirectory
	publishingRepo = cfg.Global_parameters.PublishingIOTA2_repo
	updateDirectory(publishingRepo+"/DATAs/scripts",workingDirectory)

	layerswitcherCSS = cfg.Global_parameters.layerswitcherCSS
	layerswitcherJS = cfg.Global_parameters.layerswitcherJS
	bingKey = cfg.Global_parameters.bingKey
	bing = cfg.Global_parameters.bingMap

	Classif = cfg.Classification
	Res = Classif.results
	Title = Classif.title
	Color = Classif.color
	Out = workingDirectory+"/"+Classif.fig_out
	Url = Classif.url
	Layer = Classif.layerName
	ClassesDescriptions = Classif.classesDescriptions
	classDescriptions = figureClassification.getNomenclatureFromXML(Color)
	validityLayer = Classif.validityLayer
	validityTitle = Classif.validityTitle

	confidenceLayer = Classif.confidenceLayer
	confidenceTitle = Classif.confidenceTitle

	fig_id = figClassif.genFigure(Res,Color,Out,Title,ClassesDescriptions)

	AllLayers = [fig_id,"validity","confidence"]

	file_JS = open(workingDirectory+"/layer.js","w")
	file_JS.write(CS.JS_headers)

	file_JS.write(CS.var_Classif%(fig_id,Title,'true',Url,Layer))
	file_JS.write(CS.var_Classif%("validity",validityTitle,'false',Url,validityLayer))
	file_JS.write(CS.var_Classif%("confidence",confidenceTitle,'false',Url,confidenceLayer))

	visible = 'true'
	for imType in bing:
		file_JS.write(CS.var_Bings%(imType,imType,visible,bingKey,imType))
		visible = 'false'

	file_JS.write(CS.var_layerSwitcher)
	file_JS.write(CS.var_mousePositionControl)
	file_JS.write(CS.var_scaleLineControl)
	file_JS.write(CS.var_container)
	file_JS.write(CS.var_mapHeaders)
	file_JS.write(CS.var_mapOptions)
	file_JS.write(CS.var_mapLayers_head+",".join(bing)+"]}),\n")
	file_JS.write(CS.var_mapLayers_overlays+",".join([fig_id,"validity","confidence"])+"]}),\n")
	file_JS.write("]});\nurl = 'filter.geojson';\n")
	file_JS.write(CS.var_filterHeader)
	filterLayer(AllLayers,file_JS)
	file_JS.write("      });\n")
	file_JS.write(CS.var_control)
	addClassDescription(classDescriptions,file_JS)
	file_JS.write(CS.var_mapEvent%(AllLayers[0],AllLayers[1],AllLayers[2]))
	file_JS.write(CS.var_mapEventTAIL)
	file_JS.write("\n\
	function OpaChange() {\n\
var opcity = selectOpa.value;\n"
	)

	file_JS.write(str(fig_id)+".setOpacity(opcity);\n")
	file_JS.write("validity"+".setOpacity(opcity);\n")
	file_JS.write("confidence"+".setOpacity(opcity);\n")
	file_JS.write("\n\
}\n\
\n\
	selectOpa.addEventListener('change', OpaChange);\n\
	OpaChange();\n\
   	map.addControl(layerSwitcher);\n\
})();")
	file_JS.close()

	#Step3 -> generate HTML
	file_HTML = open(workingDirectory+"/layer.html","w")
	file_HTML.write(CS.htmlHEADER)
	file_HTML.write("<div id="+fig_id+" style=\"border: 1px solid white;float: left;width:100%\"></div>")
	file_HTML.write(CS.htmlTAIL)
	file_HTML.write("<script src="+fig_id+".js></script>\n</body>\n</html>")
	file_HTML.close()

def generateMultiClassificationHTML(cfgFile):
	f = file(cfgFile)
	cfg = Config(f)

	workingDirectory = cfg.Global_parameters.workingDirectory
	layerswitcherCSS = cfg.Global_parameters.layerswitcherCSS
	layerswitcherJS = cfg.Global_parameters.layerswitcherJS
	bingKey = cfg.Global_parameters.bingKey
	bing = cfg.Global_parameters.bingMap

	#step 0.2 -> get classifications chain informations
	AllRes=[]
	AllTitle=[]
	AllColor=[]
	AllOut=[]
	AllUrl=[]
	AllLayer=[]
	AllClassesDescriptions=[]

	AllClassif = cfg.All_Classifications
	for num_classif in range(len(AllClassif)):
		AllRes.append(AllClassif[num_classif].results)
		AllTitle.append(AllClassif[num_classif].title)
		AllColor.append(AllClassif[num_classif].color)
		AllOut.append(workingDirectory+"/"+AllClassif[num_classif].fig_out)
		AllUrl.append(AllClassif[num_classif].url)
		AllLayer.append(AllClassif[num_classif].layerName)
		AllClassesDescriptions.append(AllClassif[num_classif].classesDescriptions)

		

	#Step1 -> for each classification, generate one figure of results
	Allfig_id = []
	for resultat,title,color,desc,out in zip(AllRes,AllTitle,AllColor,AllClassesDescriptions,AllOut):
		fig_id = figClassif.genFigure(resultat,color,out,title,desc)
		Allfig_id.append(fig_id)

	#Step2 -> generate Javascript

	file_JS = open(workingDirectory+"/layer.js","w")

	file_JS.write(CS.JS_headers)
	visible = 'true'
	for url,layer,fig_id,title in zip(AllUrl,AllLayer,Allfig_id,AllTitle):
		file_JS.write(CS.var_Classif%(fig_id,title,visible,url,layer))
		visible = 'false'
	visible = 'true'
	for imType in bing:
		file_JS.write(CS.var_Bings%(imType,imType,visible,bingKey,imType))
		visible = 'false'

	file_JS.write(CS.var_layerSwitcher)
	file_JS.write(CS.var_mousePositionControl)
	file_JS.write(CS.var_scaleLineControl)
	file_JS.write(CS.var_mapHeaders)
	file_JS.write(CS.var_mapOptions)
	file_JS.write(CS.var_mapLayers_head+",".join(bing)+"]}),\n")
	file_JS.write(CS.var_mapLayers_overlays+",".join(Allfig_id)+"]}),\n")
	file_JS.write("]});\n")
	file_JS.write("\n\
	function OpaChange() {\n\
var opcity = selectOpa.value;\n"
	)
	for id_fig in Allfig_id:
		file_JS.write(str(id_fig)+".setOpacity(opcity);\n")
	file_JS.write("\n\
}\n\
\n\
	selectOpa.addEventListener('change', OpaChange);\n\
	OpaChange();\n\
   	map.addControl(layerSwitcher);\n\
})();")
	file_JS.close()

	#Step3 -> generate HTML
	file_HTML = open(workingDirectory+"/layer.html","w")

	file_HTML.write(CS.html_headers%(layerswitcherCSS,layerswitcherJS))
	for i in range(len(Allfig_id)):
		file_HTML.write("\t\t\t<tr><td ><input type=checkbox name=ckb value="+str(i+1)+" onClick=\"chkcontrol("+str(i+1)+",'"+Allfig_id[i]+"')\"></td><td >"+AllTitle[i]+"</td></tr>\n")

	file_HTML.write(CS.html_head_res)
	for i in range(len(Allfig_id)):
		file_HTML.write('\t<div id="'+Allfig_id[i]+'" style="float: left;display:none;width:50%"></div>\n')
	file_HTML.write(CS.html_end)

	for i in range(len(AllOut)):
		file_HTML.write('<script src="file://'+AllOut[i]+'"></script>\n')
	file_HTML.write('</body>\n</html>')
  	

	file_HTML.close()
	#Step 4 -> generate CSS
	file_CSS = open(workingDirectory+"/layer.css","w")
	file_CSS.write(CS.CSS_File)
	file_CSS.close()

def generateHTML_code(cfgFile):

	f = file(cfgFile)
	cfg = Config(f)

	#step 0.1 -> get global chain informations
	outputFormat = cfg.Global_parameters.outputFormat

	if outputFormat == "multiClassifications": generateMultiClassificationHTML(cfgFile)
	elif outputFormat == "oneClassification": generateOneClassificationHTML(cfgFile)

	

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function generate a html page, representing classifications describe by a configuration file")
	parser.add_argument("-config",dest = "configPath",help ="path to the configuration file",required=True)
	args = parser.parse_args()
	generateHTML_code(args.configPath)







