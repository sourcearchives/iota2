#!/usr/bin/python
#-*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
import argparse,re,mpld3,fileinput,sys

from mpld3 import plugins
from config import Config


"""
python figureClassification.py -qml /home/vincenta/IOTA/pyTools/genHtml/testGenFig/FR_ALLCLASSES.qml -mode javascript -out /home/vincenta/IOTA/pyTools/genHtml/exempleRes_2.html -results /home/vincenta/IOTA/pyTools/genHtml/testGenFig/resultat_2009.txt
"""
def getStringBetween(string,ch1,ch2):
	out = ""
	for i in range(len(string)):
		if ch1==string[i]:
			for j in range(i+1,len(string)):
				if string[j]==ch2:
					break
				else:
					out = out+string[j]
			break
	return out

def getResultsFromFile(resFile):
	resFile = open(resFile,"r")
	AllClass = []
	while 1 :
		data = resFile.readline().rstrip('\n\r')
		if "KAPPA : " in data:
			kappa_95 = re.findall(r"[-+]?\d*\.\d+|\d+", data)
			kappa = kappa_95[0]
		elif "OA : " in data:
			OA_95 = re.findall(r"[-+]?\d*\.\d+|\d+", data)
			OA = OA_95[0]
		elif  ("Classes" in data) and ("F-score moyen" in data) :
			data = resFile.readline().rstrip('\n\r')
			while 1 :
				data = resFile.readline().rstrip('\n\r')
				if data == "":
					break
				Currentclass = data.split("|")[0]
				Allcoeff = re.findall(r"[-+]?\d*\.\d+|\d+", data)
				Fscore = Allcoeff[-1]
				AllClass.append((Currentclass,Fscore))
			break

	resFile.close
	return AllClass,kappa,OA

def getNomenclatureFromXML(qmlFile):

	"""
	IN : qmlFile
	OUT : [['classNumber','ClassName',rValue,gValue,bValue],[...],...]
	"""
	#Read the color's file and write into the html file
	color = open(qmlFile,"r")

	lineData = []#[(ClassNumber,ClassName,r,g,b),[...],...]

	while 1:
		data = color.readline().rstrip('\n\r')
		if data.count('</qgis>')!=0:
			break
		elif data.count("colorRampEntry")!=0:
				
			#Get the red value
			ind = data.index("red")
			redVal = int(getStringBetween(data[ind+len("red"):ind+len("red")+7],'"','"'))
			#Get the green value
			ind = data.index("green")
			greenVal = int(getStringBetween(data[ind+len("green"):ind+len("green")+7],'"','"'))
			#Get the blue value
			ind = data.index("blue")
			blueVal = int(getStringBetween(data[ind+len("blue"):ind+len("blue")+7],'"','"'))
			#Get the Class Name
			ind = data.index("label")
			ClassName = getStringBetween(data[ind+len("label"):ind+len(data)],'"','"')
			#Get the Class Number
			ind = data.index("value")
			ClassNum = getStringBetween(data[ind+len("value"):ind+len(data)],'"','"').split(".")[0]
				
			lineData.append((ClassNum,ClassName,redVal,greenVal,blueVal))
	color.close()

	return lineData

def autolabel(rects,Score,color,ax):
    
    #get the X max
    Xmax = 0
    for rect,perf,col in zip(rects,Score,color):
	X = rect.get_width()+rect.get_height()/4.0
	if X > Xmax:
		Xmax=X

    for rect,perf,col in zip(rects,Score,color):
	rect.set_facecolor(col)
	ax.text(Xmax, float(rect.get_y())+0.75 * float(rect.get_height())/2.0,
                '%.3f' % float(perf),
                ha='center', va='bottom')
	space = rect.get_height()/2.0
    return space

def replaceAll(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

def organizedDescriptions(classes,desc):
	f = file(desc)
	cfg = Config(f)
	AllDesc = cfg.AllClasses
	descriptions = []
	for cl in classes:
		for cl_desc in AllDesc:
			if cl_desc.classeName == cl:
				descriptions.append(cl_desc.classeDescription)
	return descriptions

def genFigure(resFile,qmlFile,out,title,desc,mode="javascript"):

	AllRes,K,OA = getResultsFromFile(resFile)
	AllColor = getNomenclatureFromXML(qmlFile)
	classes = []
	Score = []
	color = []
	sizeClassMax = 0
	for classNum,className,r,g,b in AllColor:
		for className_r,Fscore in AllRes:
			if className.replace(" ","") == className_r.replace(" ",""):
				if len(className)>sizeClassMax:
					sizeClassMax = len(className)
				classes.append(className)
				Score.append(float(Fscore))
				color.append((r/255.0,g/255.0,b/255.0,1))
	
	descriptions = organizedDescriptions(classes,desc)
	#fig, ax = plt.subplots()
	fig = plt.figure(figsize=(15, 8), dpi=100)
        ax = plt.subplot(111)

	#plt.figure(figsize=(15, 8), dpi=100)

	#y_pos = np.arange(len(classes))
	y_pos = np.arange(-4,len(classes)-4,1)
	rects = plt.barh(y_pos, Score, align='center', alpha=0.4)
	plt.yticks(y_pos, classes)
	plt.xlabel('F-score')
	plt.title(title+",\tK : "+K+",\tOA : "+OA)
	
	space = autolabel(rects,Score,color,ax)
	
	plt.xlim([0,max(Score)+space])
	plt.subplots_adjust(left=float(sizeClassMax)*0.011)

	if mode == "matplotlib":		
		plt.savefig(out,bbbox='tight')
	else:
		for i, box in enumerate(rects.get_children()):
    			tooltip = mpld3.plugins.LineLabelTooltip(box,descriptions[i])
    			mpld3.plugins.connect(fig, tooltip)

		fig_id = out.split("/")[-1].split(".")[0]

		fig_js = mpld3.fig_to_html(fig)
		resFile = open(out,"w")
		resFile.write(fig_js)
		resFile.close()
	
		idFig = re.search('%s(.*)%s' % ('<div id="', '"></div>'), fig_js).group(1)
		replaceAll(out,idFig,fig_id)

		#suppression du div et des tag script style
		replaceAll(out,'<div id="'+fig_id+'"></div>',"")
		replaceAll(out,'<style>',"")
		replaceAll(out,'</style>',"")
		replaceAll(out,'<script>',"")
		replaceAll(out,'</script>',"")
	
	return fig_id

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "This function allow you to generate a classification result in bar chart, and save it into matplotlib or javascript format.")
	parser.add_argument("-qml",help = "path to the qml file which link the class and their color (mandatory)",dest = "qmlFile", required = True)
	parser.add_argument("-mode ",help = "save mode",dest = "mode", choices ={"matplotlib","javascript"} ,required = True)
	parser.add_argument("-title ",help = "figure's title",dest = "title",required = True)
	parser.add_argument("-out ",help = "save path",dest = "out",required = True)
	parser.add_argument("-results",help = "path to the file containing classification's results (mandatory)",dest = "resulats", required = True)
	args=parser.parse_args()

	genFigure(args.resulats,args.qmlFile,args.out,args.title,args.mode)
















