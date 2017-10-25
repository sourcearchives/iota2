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

import logging
import logging.config

class serviceLogger(logging.getLoggerClass()):
    """
    The class serviceLogger defines all logging parameter.
    It's an interface to python logging class.
    """
    instance = None
    def __new__(cls, cfg, name):
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance
    
    def __init__(self, cfg, name):
        """
            Init class serviceLogger
            :param cfg: class serviceConfigFile
        """

        # logging format
        logFormatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] - %(message)s")
        
        rootLogger = logging.getLogger()
        # set the logging level
        rootLogger.setLevel(cfg.getParam('chain', 'logFileLevel'))
        if not hasattr(self, 'first'):
            # First call to serviceLogger
            self.first = True
            # create a log file
            self.fileHandler = logging.FileHandler(cfg.getParam('chain', 'logFile'),mode='w')
            self.fileHandler.setFormatter(logFormatter)
            self.fileHandler.setLevel(cfg.getParam('chain', 'logFileLevel'))
            rootLogger.addHandler(self.fileHandler)
            
            if (cfg.getParam('chain', 'logConsole') == True):
                # logging in console
                self.consoleHandler = logging.StreamHandler()
                self.consoleHandler.setFormatter(logFormatter)
                self.consoleHandler.setLevel(cfg.getParam('chain', 'logConsoleLevel'))
                rootLogger.addHandler(self.consoleHandler)
        


####################################################################
####################################################################


