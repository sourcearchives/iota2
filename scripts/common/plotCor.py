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

import numpy as np
import matplotlib
matplotlib.use("AGG")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator
from numpy import linspace


class Parametres:
    '''
    This class contains all the paramater required by the plot
    '''

    def __init__(self):
        '''
        Initialise the class
        '''
        self.xlims = [1000000, 0]
        self.ylims = [100, 0]
        self.xBinStep = 1
        self.yBinStep = 1

    def canWeUseXlims(self):
        '''
        That method returns a boolean accordingly if we can use those values of xlims
        '''
        retour = False
        if self.xlims[0] <= self.xlims[1]:
            retour = True
        return retour

    def canWeUseYlims(self):
        '''
        That method returns a boolean accordingly if we can use those values of ylims
        '''
        retour = False
        if self.ylims[0] <= self.ylims[1]:
            retour = True
        return retour

def plotCorrelation(x, y, xLabel, yLabel, outputPath, forceParameter=Parametres()):

    # Define the locations for the axes
    left, width = 0.12, 0.50
    bottom, height = 0.12, 0.50
    bottom_h = left_h = left+width+0.02

    # Set up auto x and y limits
    xlims = [min(x), max(x)]
    ylims = [min(y), max(y)]
    #if forceParameter.has_key("xlims"):
    #    xlims = forceParameter["xlims"]
    #if forceParameter.has_key("ylims"):
    #    ylims = forceParameter["ylims"]
    if isinstance(forceParameter, Parametres):
        if forceParameter.canWeUseXlims():
            xlims = forceParameter.xlims
        if forceParameter.canWeUseYlims():
            ylims = forceParameter.ylims
    
    #Find the min/max of the data
    xmin = min(xlims)
    xmax = max(xlims)
    ymin = min(ylims)
    ymax = max(ylims)
    
    #Set up the histogram bins
    #if forceParameter.has_key("xBinStep"):
    #    xbins = np.arange(xmin, xmax+1, forceParameter["xBinStep"])
    #else:
    #    xbins = np.arange(xmin, xmax, (xmax-xmin)/nbins)
    #    
    #if forceParameter.has_key("yBinStep"):
    #    ybins = np.arange(ymin, ymax+1, forceParameter["yBinStep"])
    #else:
    #    ybins = np.arange(ymin, ymax, (ymax-ymin)/nbins)
    xbins = np.arrange(xmin, xmax+1, forceParameter.xBinStep)
    ybins = np.arrange(ymin, ymax, forceParameter.yBinStep)
    
    # Set up the size of the figure
    figure = plt.figure(1, figsize=(9.5, 9))
    
    # Set up the geometry of the three plots
    rect_data = [left, bottom, width, height] # dimensions of temp plot
    rect_histx = [left, bottom_h, width, 0.25] # dimensions of x-histogram
    rect_histy = [left_h, bottom, 0.25, height] # dimensions of y-histogram
    # Make the three plots
    axData = plt.axes(rect_data) # data plot
    axHistx = plt.axes(rect_histx) # x histogram
    axHisty = plt.axes(rect_histy) # y histogram

    # Remove the inner axes numbers of the histograms
    nullfmt = NullFormatter()
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)   

    aspectratio = 1.0*(xmax-0)/(1.0*ymax-0)   

    # Plot the temperature data
    axData.hist2d(x, y, bins=[xbins, ybins])

    #Plot the axes labels
    axData.set_xlabel(xLabel, fontsize=25)
    axData.set_ylabel(yLabel, fontsize=25)
     
    #Make the tickmarks pretty
    ticklabels = axData.get_xticklabels()
    for label in ticklabels:
        label.set_fontsize(18)
        label.set_family('serif')
     
    ticklabels = axData.get_yticklabels()
    for label in ticklabels:
        label.set_fontsize(18)
        label.set_family('serif')
     
    #Set up the plot limits
    axData.set_xlim((xmin, xmax))
    axData.set_ylim((ymin, ymax))
     
    #Plot the histograms
    axHistx.hist(x, bins=xbins, color='blue')
    axHisty.hist(y, bins=ybins, orientation='horizontal', color='red')
     
    #Set up the histogram limits
    axHistx.set_xlim(min(xlims), max(xlims))
    axHisty.set_ylim(min(ylims), max(ylims))
     
    #Make the tickmarks pretty
    ticklabels = axHistx.get_yticklabels()
    for label in ticklabels:
        label.set_fontsize(12)
        label.set_family('serif')
     
    #Make the tickmarks pretty
    ticklabels = axHisty.get_xticklabels()
    for label in ticklabels:
        label.set_fontsize(12)
        label.set_family('serif')
        
    #Cool trick that changes the number of tickmarks for the histogram axes
    axHisty.xaxis.set_major_locator(MaxNLocator(4))
    axHistx.yaxis.set_major_locator(MaxNLocator(4))

    plt.savefig(outputPath)
