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



class osoError(Exception):
    """ Base class for exceptions in oso chain"""
    pass

# Error class definition configFileError inherits the osoError class
class configFileError(osoError):
    """ Base subclass for exception in the configuration file
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        osoError.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

####################################################################
# List of error class definition for the configuration file,
# inherits the configFileError class
####################################################################
class parameterError(configFileError):
    """ Exception raised for errors in a parameter in the configuration file
        (like absence of a mandatory variable)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, section, msg):
        self.section = section
        self.msg = msg
    def __str__(self):
        return "Error: In section " + repr(self.section) + ", " + self.msg

class dirError(configFileError):
    """ Exception raised for errors in mandatory directory
        IN :
            directory [string] : name of the directory
    """
    def __init__(self, directory):
        self.directory = directory
    def __str__(self):
        self.msg = "Error: " + repr(self.directory) + " doesn't exist"
        return self.msg

class configError(configFileError):
    """ Exception raised for configuration errors in the configuration file
        (like incompatible parameters)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "Error: " + repr(self.msg)

class fileError(configFileError):
    """ Exception raised for errors inside an input file
        (like a bad format or absence of a variable)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "Error: " + repr(self.msg)

####################################################################
####################################################################


