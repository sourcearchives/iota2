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

try:
    from cStringIO import StringIO#Python 2
except ImportError:
    from io import StringIO


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

        log_lvl_dic = {"CRITICAL":50, "ERROR":40, "WARNING":30, "INFO":20, "DEBUG":10, "NOTSET":0}
        log_level_code = log_lvl_dic[cfg.getParam('chain', 'logFileLevel')]

        # logging format
        logFormatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] - %(message)s")

        rootLogger = logging.getLogger()
        # set the logging level
        rootLogger.setLevel(log_level_code)
        if not hasattr(self, 'first'):
            # First call to serviceLogger
            self.first = True
            # create a log file
            self.fileHandler = logging.FileHandler(cfg.getParam('chain', 'logFile'), mode='w')
            self.fileHandler.setFormatter(logFormatter)
            self.fileHandler.setLevel(cfg.getParam('chain', 'logFileLevel'))
            rootLogger.addHandler(self.fileHandler)

            if (cfg.getParam('chain', 'logConsole') is True):
                # logging in console
                self.consoleHandler = logging.StreamHandler()
                self.consoleHandler.setFormatter(logFormatter)
                self.consoleHandler.setLevel(cfg.getParam('chain', 'logConsoleLevel'))
                rootLogger.addHandler(self.consoleHandler)


class Log_task(logging.getLoggerClass()):


    def __init__(self, log_level="INFO", enable_console=False):
        """
        Init class serviceLogger
        log_level [string] : logging level "DEBUG" or "INFO" or "WARNING"
                                           or "ERROR" or "CRITICAL"
        """

        #logging format
        self.logFormatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] - %(message)s")

        #rootLogger
        rootLogger = logging.getLogger()

        #reset handlers
        rootLogger.handlers = []

        #set the logging level
        rootLogger.setLevel(log_level)

        #create a log string
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(self.logFormatter)
        self.handler.setLevel(log_level)
        rootLogger.addHandler(self.handler)

        if enable_console:
            #logging in console
            self.consoleHandler = logging.StreamHandler()
            self.consoleHandler.setFormatter(self.logFormatter)
            self.consoleHandler.setLevel(log_level)
            rootLogger.addHandler(self.consoleHandler)

