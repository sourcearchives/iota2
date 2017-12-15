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

import os,random,argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from collections import defaultdict

import bisect

import logging

logger = logging.getLogger(__name__)

"""
python repartitionModel.py -out ~/tmp/testRepartition.txt --model.delta 2 -model.number 5 -tiles D0003H0009 D0005H0009 D0008H0009 D0010H0008 D0003H0007 D0005H0007 D0007H0007 D0008H0006 D0004H0005 D0007H0004 D0004H0003 D0010H0003 D0006H0002 D0009H0002 D0005H0001 D0004H0009 D0006H0009 D0002H0008 D0004H0007 D0006H0007 D0008H0007 D0005H0005 D0009H0005 D0003H0004 D0006H0004 D0008H0003 D0003H0002 D0010H0002 D0007H0001 D0007H0009 D0009H0009 D0004H0008 D0006H0008 D0002H0007 D0009H0007 D0004H0006 D0006H0006 D0007H0005 D0004H0004 D0009H0004 D0006H0003 D0005H0002 D0008H0002 D0003H0001 D0007H0010 D0003H0008 D0005H0008 D0008H0008 D0001H0007 D0003H0006 D0005H0006 D0008H0005 D0005H0004 D0007H0003 D0009H0003 D0004H0002 D0006H0001 D0010H0007 D0006H0010 D0001H0008 D0007H0008 D0009H0008 D0002H0006 D0007H0006 D0009H0006 D0003H0005 D0006H0005 D0008H0004 D0010H0004 D0003H0003 D0005H0003 D0007H0002 D0004H0001
"""
class Tile(object):

	def __init__(self,NomTuile):
		self.name = NomTuile
		self.x = int(NomTuile[1:5])
		self.y = int(NomTuile[6:len(NomTuile)])
		self.model = 0
	def getX(self):
		return self.x
	def getY(self):
		return self.y
	def getName(self):
		return self.name
	def getModel(self):
		return self.model
	def setModel(self,model):
		self.model = model

def getFirst(item):
	return item[0]

def weighted_choice(choices):
    values, weights = zip(*choices)
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect.bisect(cum_weights, x)
    return values[i]


def getDiag(listTiles,Tile):
	v = []
	X = Tile.getX()
	Y = Tile.getY()

	for currentTile in listTiles:
		currentX = currentTile.getX()
		currentY = currentTile.getY()
		if (currentX == X-1 and (currentY == Y-1 or currentY == Y+1)) or (currentX == X+1 and (currentY == Y-1 or currentY == Y+1)):
			v.append(currentTile)
	return v

def get4voisins(listTiles,Tile):
	v = []
	X = Tile.getX()
	Y = Tile.getY()

	for currentTile in listTiles:
		currentX = currentTile.getX()
		currentY = currentTile.getY()
		if (currentX == X and (currentY == Y-1 or currentY == Y+1)) or (currentY == Y and (currentX == X-1 or currentX == X+1)):
			v.append(currentTile)
	return v

def modelChoice(modelPossible,diag) :
	NbMp = len(modelPossible)
	
	#construction du vecteur de choix
	VC = []
	for m in modelPossible:
		VC.append([m,float(100/float(NbMp))])
	for model in VC:
		for tile in diag:
			if tile.getModel() == model[0]:
				model[1] = 0.01
	return weighted_choice(VC)
	

def genGraph(listTile,NbModel):

	allModel = np.arange(1,NbModel+1)#all possible models
	rep = []
	for tile in listTile:
		voisins = get4voisins(listTile,tile)
		#liste des modèles déjà attribué
		mV = []
		for v in voisins:
			mV.append(v.getModel())

		#list des modèle possible pour la tuile courante
		mP = [x for x in allModel if x not in mV]

		#model choisi pour la tuile courante
		diag = getDiag(listTile,tile)
		mC = modelChoice(mP,diag)
		tile.setModel(mC)
		rep.append(mC)

	return Counter(rep).most_common(NbModel)

def GenerateRep(tiles, NbModel, pathOut, delta):

    #init
    out_list = []
    for tile in tiles:
        out_list.append(Tile(tile))

    #Tant qu'on a pas la solution, la chercher... (mettre un time out)
    flag=0
    while flag == 0:
        try:
            rep = genGraph(out_list,NbModel)

            if delta == None:
                flag = 1
            else : 
                diff = rep[0][1]-rep[-1][1]#nb model le plus représenté moins model le moins représenté
                if diff <= delta:
                    flag = 1
        except ValueError:
            flag = 0

    print "---------------------- repartition ----------------------"
    print rep
    print "---------------------------------------------------------"
    
    #Sauvegarde de la solution
    buff = []
    for tile in out_list :
        buff.append((tile.getModel(),tile.getName()))
    
    d = defaultdict(list)
    for k, v in buff:
        d[k].append(v)
    buff = list(d.items())
    buff = sorted(buff,key=getFirst)
    svg = open(pathOut,"w")
    for model,tiles in buff:
        svg.write("m"+str(model)+" : ")
        for i in range(len(tiles)):
            if i == len(tiles)-1:
                svg.write(tiles[i])
            else:
                svg.write(tiles[i]+",")
        svg.write("\n")
    svg.close()
    #Affichage de la solution
    minX = 100000
    maxX = 0
    minY = 100000
    maxY = 0

    for tile in out_list:
        if tile.getX()>maxX:
            maxX = tile.getX()
        if tile.getX()<minX:
            minX = tile.getX()
        if tile.getY()>maxY:
            maxY = tile.getY()
        if tile.getY()<minY:
            minY = tile.getY()
    modelMatrix = []
    #init de la matrice des modèles
    for i in range(maxY):
        modelMatrix.append([])
        for j in range(maxX):
            modelMatrix[i].append(0)
    for tile in out_list:
        x = tile.getX()
        y = tile.getY()
        model = tile.getModel()
        modelMatrix[maxY-y][x-minX]=model

    plt.imshow(modelMatrix,interpolation = "nearest")
    
    path = pathOut.split("/")
    figpath = "/".join(path[0:-1])+"/"+path[-1].replace(".txt",".jpg")
    plt.savefig(figpath, bbox_inches='tight')

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to generate tiles repartition")
	parser.add_argument("-tiles",dest = "tiles",help ="All the tiles", nargs='+',required=True)
	parser.add_argument("-model.number",type = int,dest = "NbModel",help ="number of models",required=True)
	parser.add_argument("--model.delta",default = None,type = int,dest = "delta",help ="difference between the most reprensented model and the less",required=False)
	parser.add_argument("-out",dest = "pathOut",help ="path out",required=True)
	args = parser.parse_args()

	GenerateRep(args.tiles,args.NbModel,args.pathOut,args.delta)






















