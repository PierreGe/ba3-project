#!/usr/bin/python2
# -*- coding: utf8 -*-

import json
import io

from os import listdir
from os.path import isfile, join



import HelpWidget
import OpenGLWidget

class Controller(object):
    """Controller will controll :
            - what widget is diplayed on the left part of the splitPane
            - what the statusBar show
        The controller also know all the scene"""
    def __init__(self,statusBar):
        self._statusBar = statusBar
        self._splitPane = None
        self._scene = {} # nom : obj-liste  (from assets/scene/)
        self._parseAllScene() #

    def initSplitPane(self,splitPane):
        """ """
        self._setStatusComputing()
        self._splitPane = splitPane
        self.glWidget = OpenGLWidget.OpenGLWidget(self._scene["Basic Scene"]["obj-liste"]) # name from json file
        self.helpWidget = HelpWidget.HelpWidget()
        self._setStatusReady()

    def showGL(self, item):
        """ Set the right widget in the splitpane as the gl widget """
        self._setStatusComputing()
        print(item)
        pass
        # TODO use item
        self._replaceRightWidget(self.glWidget)
        self._setStatusReady()

    def showHelp(self):
        """ Set the right widget in the splitpane as help """
        self._setStatusComputing()
        self._replaceRightWidget(self.helpWidget)
        self._setStatusReady()

    def getAllScene(self):
        """ get the scene dictionnary"""
        return self._scene

    def _parseAllScene(self):
        """ This method will assets/scene/ and add all the scene to a dictionnary"""
        mypath = "assets/scene/"
        scenesFiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
        # remove auto-generated file : thanks macos!!!
        for singleFile in scenesFiles:
            if "json" in singleFile.lower():
                jasonDict = json.loads(open(mypath + singleFile).read())
                name = jasonDict["name"]
                dicti = jasonDict
                if name in self._scene:
                    print("[WARNING] : Two scenes with same name found : the first one will be overwrited!")
                self._scene[name] = dicti

    def _replaceRightWidget(self,newWidget):
        """ replace the splitpane right widget"""
        self._splitPane.replaceRightWidget(newWidget)

    def _setStatusReady(self):
        """ set the statutus bar to ready"""
        self._statusBar.showMessage("Ready!")

    def _setStatusComputing(self):
        """ set the status bar to computing"""
        self._statusBar.showMessage("Computing ....")
