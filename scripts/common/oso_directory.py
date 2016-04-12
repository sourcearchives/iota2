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

import argparse,os

def GenerateDirectories(root):
	
	if os.path.exists(root):
		os.system("rm -r "+root)
	os.system("mkdir "+root)
	if os.path.exists(root+"/model"):
		os.system("rm -r "+root+"/model")
	os.system("mkdir "+root+"/model")
	if os.path.exists(root+"/envelope"):
		os.system("rm -r "+root+"/envelope")
	os.system("mkdir "+root+"/envelope")
	if os.path.exists(root+"/classif"):
		os.system("rm -r "+root+"/classif")
	os.system("mkdir "+root+"/classif")
	if os.path.exists(root+"/shapeRegion"):
		os.system("rm -r "+root+"/shapeRegion")
	os.system("mkdir "+root+"/shapeRegion")
	if os.path.exists(root+"/final"):
		os.system("rm -r "+root+"/final")
	os.system("mkdir "+root+"/final")
	if os.path.exists(root+"/dataRegion"):
		os.system("rm -r "+root+"/dataRegion")
	os.system("mkdir "+root+"/dataRegion")
	if os.path.exists(root+"/dataAppVal"):
		os.system("rm -r "+root+"/dataAppVal")
	os.system("mkdir "+root+"/dataAppVal")
	if os.path.exists(root+"/stats"):
		os.system("rm -r "+root+"/stats")
	os.system("mkdir "+root+"/stats")
	if os.path.exists(root+"/cmd"):
		os.system("rm -r "+root+"/cmd")
	os.system("mkdir "+root+"/cmd")
	os.system("mkdir "+root+"/cmd/stats")
	os.system("mkdir "+root+"/cmd/train")
	os.system("mkdir "+root+"/cmd/cla")
	os.system("mkdir "+root+"/cmd/confusion")
	os.system("mkdir "+root+"/cmd/features")
	os.system("mkdir "+root+"/cmd/fusion")
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function creates directories for classifications")
	parser.add_argument("-root",dest = "root",help ="path where all directories will be create",required=True)
	args = parser.parse_args()

	GenerateDirectories(args.root)


















































