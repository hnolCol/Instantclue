"""
PlotOptioFrame

"""



from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from ..plotter.plotTypeManager import PlotTypeManager, plotTypeTooltips, gridPosition 
from ..custom.buttonDesigns import PlotTypeButton, MainFigureButton, SettingsButton
from ..custom.mainFigure import MainFigure, MainFigureRegistry
from ..custom.warnMessage import WarningMessage
from ..custom.ICDataTable import PandaTableDialog
from ..dialogs.ICConfiguration import ConfigDialog
from ..dialogs.ICDataInputDialog import ICDataInput
from ..utils import createSubMenu
import numpy as np
import os




class PlotOptionFrame(QWidget):
    def __init__(self,parent=None, mainController  = None, *args,**kwargs):
        super(PlotOptionFrame,self).__init__(parent=parent,*args,**kwargs)

        self.mC = mainController
        self.typeManager = PlotTypeManager()
        self.mainFigureRegistry = MainFigureRegistry()
        self.currentPlotType = self.getDefaultPlotType()
        self._controls()
        self._layout()
        self._connectEvents()
        self.updateTypeSpecMenus()
        self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)
        self.setMaximumWidth(100)

    def _controls(self):
        ""
        self.buttons = []
        for plotType in self.typeManager.getAvailableTypes():
            button = PlotTypeButton(parent=self,plotType=plotType,tooltipStr = plotTypeTooltips[plotType] if plotType in plotTypeTooltips else "")
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            self.buttons.append(button)
                
        self.mainFigureButton = MainFigureButton(tooltipStr="Opens a Main Figure (A4).\nCreate an axis to export plots from the main window to the main figure.")
        self.configButton = SettingsButton(tooltipStr="Opens Settings.")

    def _layout(self):
        ""
        self.setLayout(QGridLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        for b in self.buttons:
            nRow, nCol = gridPosition[b.plotType]
            self.layout().addWidget(b,nRow,nCol)
        self.layout().setRowStretch(8,1)
        self.layout().addWidget(self.mainFigureButton,9,0)
        self.layout().addWidget(self.configButton,10,0)

        self.layout().setAlignment(Qt.AlignTop)

    
    def _connectEvents(self):
        ""
        for n,plotType in enumerate(self.typeManager.getAvailableTypes()):
            self.buttons[n].clicked.connect(lambda _,plotType = plotType:self.setType(plotType))
            self.buttons[n].customContextMenuRequested.connect(lambda _,plotType = plotType:self.postContextMenu(plotType))

        self.mainFigureButton.clicked.connect(self.openMainFigure)
        self.configButton.clicked.connect(self.openConfig)

    def updateTypeSpecMenus(self):
        ""
        self.typeMenus = {}

        hclustMenuColorRange = ["raw values","center 0","min = -1, max = 1","Custom values"]
        menu = createSubMenu(subMenus=["Set color range .."])
        menu["main"].addMenu(menu["Set color range .."])
        for hclustColorRange in hclustMenuColorRange:
            action = menu["Set color range .."].addAction(hclustColorRange)
            action.triggered.connect(lambda _,scaleString = hclustColorRange:self.updateColorScaleInClustermap(scaleString))
        for name,fn in [("Enforce row label",self.setEnforceRowLabeling),("Export Cluster ID",self.addClusterLabel)]:
            action = menu["main"].addAction(name)
            action.triggered.connect(fn)
        
        action = menu["main"].addAction("Export to Excel")
        action.triggered.connect(self.exportHClustToExcel)
        
        self.typeMenus["hclust"] = menu["main"]
        menu = createSubMenu(subMenus=["Method","Results","Set color range .."])
        #menu["main"].addMenu(menu["Method"])
        #menu["main"].addMenu(menu["Results"])
        #
        for hclustColorRange in hclustMenuColorRange:
            action = menu["Set color range .."].addAction(hclustColorRange)
            action.triggered.connect(lambda _,scaleString = hclustColorRange:self.updateColorScaleInClustermap(scaleString))
        #set methods
        for method in ["pearson","spearman","kendall"]:
            action = menu["Method"].addAction(method)
            action.triggered.connect(lambda _,method = method : self.changeCorrMethod(method))
        for name, fn in [("View",self.showCorrResults)]:
            action = menu["Results"].addAction(name) 
            action.triggered.connect(fn)
        #set other options for corrmatrix
        for name,fn in [("Enforce row label",self.setEnforceRowLabeling)]:
            action = menu["main"].addAction(name)
            action.triggered.connect(fn)

        self.typeMenus["corrmatrix"] = menu["main"]

        #scatter menu 
        menu = createSubMenu(subMenus=["Markers .. ","Axis limits .."])

        #marker for scatter
        for marker in self.mC.config.getParamRange("scatter.marker"):
            action = menu["Markers .. "].addAction(marker)
            action.triggered.connect(lambda _, marker = marker: self.mC.config.setParam("scatter.marker", marker))

        for actionName, fnName in [("Raw limits","rawAxesLimits"),("Center x to 0","centerXToZero"),("Equal limits","alignLimitsOfAllAxes"),("Set x- and y-limits equal","alignLimitsOfXY")]:
            action = menu["Axis limits .."].addAction(actionName)
            action.triggered.connect(lambda _,fnName = fnName: self.adjustAxisLimitsInScatter(fnName=fnName))

        #label in all plots
        action = menu["main"].addAction("{} annotations in all subplots".format("Disable" if self.mC.config.getParam("annotate.in.all.plots") else "Enable"), self.toggleAnnotations)
        
        self.typeMenus["scatter"] = menu["main"]


        #swarmplot menu 
        menu = createSubMenu(subMenus=[])
        for paramName,actionName in [("xy.plot.show.marker",{False:"Show markers",True:"Hide markers"}),
                                     ("xy.plot.against.index",{False:"Against index",True:"Against column"})]:
            currentState = self.mC.config.getParam(paramName)
            action = menu["main"].addAction(actionName[currentState])
            action.triggered.connect( lambda _, paramName = paramName,actionName = actionName: self.changeXYParams(paramName,actionName) )

        self.typeMenus["x-ys-plot"] = menu["main"]
        #boxplot menu



        menu = createSubMenu(subMenus=["Outliers .. "])
        menu["Outliers .. "].addAction("Hide", self.hideOutliersInBoxplot)
        currentParamState = self.mC.config.getParam("boxplot.split.data.on.category")
        if currentParamState:
            menu["main"].addAction("Disable split by category", self.handleSplitOfDataByCategory)
        else:
            menu["main"].addAction("Enable split by category", self.handleSplitOfDataByCategory)
        self.typeMenus["boxplot"] = menu["main"]


        #barplot menu 
        menu = createSubMenu(subMenus=["Error bars .. "])
        for errorType in ["Std","CI (95%)", "CI (90%)", "CI (85%)","CI (75%)", "SEM-CI (68%)"]:
            menu["Error bars .. "].addAction(errorType, self.setPlotError)
        
        self.typeMenus["barplot"] = menu["main"]

        #pointplot menu 
        menu = createSubMenu(subMenus=["Error bars .. ","Dodge .. "])
        for errorType in ["Std","CI (95%)", "CI (90%)", "CI (85%)","CI (75%)"]:
            menu["Error bars .. "].addAction(errorType, self.setPlotError)
        menu["Dodge .. "].addAction("True", self.setDodge)

        self.typeMenus["pointplot"] = menu["main"]

        #add swarmplot menu
        menu = createSubMenu(subMenus=["Size ..","Markers .."])
        
        for marker in self.mC.config.getParamRange("swarm.scatter.marker"):
            action = menu["Markers .."].addAction(marker)
            action.triggered.connect(lambda _, marker = marker: self.mC.config.setParam("swarm.scatter.marker", marker))

        for scatterSize in [10,20,50,80,120,300]:
            action = menu["Size .."].addAction(str(scatterSize))
            action.triggered.connect(lambda _, size = scatterSize: self.mC.config.setParam("swarm.scatterSize",size))


        self.typeMenus["addSwarmplot"] = menu["main"]


    def handleSplitOfDataByCategory(self):
        ""
        currentParamState = self.mC.config.getParam("boxplot.split.data.on.category")

        if currentParamState:
            self.sender().setText("Enable split by category")
        else:
            self.sender().setText("Disable split by category")
        
        self.mC.config.toggleParam("boxplot.split.data.on.category")



    def changeXYParams(self,paramName,actionName):
        ""
        self.mC.config.toggleParam(paramName)
        currentState = self.mC.config.getParam(paramName)
        self.sender().setText(actionName[currentState])

    def addClusterLabel(self,event=None):
        "Add cluster ID to source data."
        exists, graph = self.mC.getGraph() 
        if exists:
            clusterID, dataID = graph.getClusterIDsByDataIndex()
            if clusterID is not None:
                
                fkey = "data::joinDataFrame"
                kwargs = dict(
                              dataID = dataID,
                              dataFrame = clusterID,
                            )
                funcProps = {"key":fkey,"kwargs":kwargs}
                #send to thread
                self.mC.sendRequestToThread(funcProps)

    def adjustAxisLimitsInScatter(self,event=None,fnName=None):
        ""
        exists, graph = self.mC.getGraph() 
        if exists and graph.hasScatters() and fnName is not None:
            if hasattr(graph,fnName):
                getattr(graph,fnName)()
       

    def changeCorrMethod(self,method="pearson"):
        "Modifies the correlation matrix used."
        self.mC.config.setParam("colorMatrixMethod",method)
       
    def postContextMenu(self, plotType):
        ""
        if plotType in self.typeMenus:
            self.sender().mouseLostFocus()
            senderGeom = self.sender().geometry()
            topLeft = self.mapToGlobal(senderGeom.bottomLeft())
            self.typeMenus[plotType].exec_(topLeft)

    def getReceiverBoxItems(self):
        ""
        return self.mC.mainFrames["middle"].getReceiverBoxItems()

    def getReceiverBoxItemProps(self):
        receiverBoxItems = self.mC.mainFrames["middle"].getReceiverBoxItems()
        nNumCol = len(receiverBoxItems["numericColumns"])
        nCatCol = len(receiverBoxItems["categoricalColumns"])
        return nNumCol, nCatCol

    def getDefaultPlotType(self):
        ""
        return self.typeManager.getDefaultType()

    def getCurrentPlotType(self):
        ""
        
        return self.currentPlotType

    def updatePlotTypeInFigure(self,*args,**kwargs):
        ""
        #emit signal that receiver boxes changed will cause update of plot types.
        self.mC.mainFrames["middle"].recieverBoxItemsChanged(*args,**kwargs)

    def setType(self,plotType, update=True):
        ""
        isValid, errorMsg, plotType = self.checkType(plotType)

        if isValid:
            self.currentPlotType = plotType
            if update:
                self.updatePlotTypeInFigure(alreadyChecked=True)
        else:
            w = WarningMessage(infoText = errorMsg)
            w.exec_() 
        
    def checkType(self, plotType = None, setDefaultIsInvalid = True):
        ""
        if plotType is None:
            plotType = self.currentPlotType

        nNumCol, nCatCol = self.getReceiverBoxItemProps()
        if nNumCol == 0 and nCatCol > 0:
            plotType = "countplot"
            self.currentPlotType = plotType
        isValid, errorMsg = self.typeManager.isTypeValid(plotType,nNumCol,nCatCol)
        if setDefaultIsInvalid and not isValid:
            plotType = self.getDefaultPlotType() 
            self.currentPlotType = plotType
        return isValid, errorMsg, plotType

    def hideOutliersInBoxplot(self,event=None):
        ""
        currentSetting = self.mC.config.getParam("boxplot.showfliers")
        self.mC.config.setParam("boxplot.showfliers",not currentSetting)
        self.sender().setText("Show" if currentSetting else "Hide")

    def setPlotError(self,event=None):
        ""
        self.mC.config.setParam("barplotError",self.sender().text())
      
    def openMainFiguresForSession(self,mainFigures,mainFigureRegistry, mainFigureComboSettings):
        ""
        self.mainFigureRegistry = mainFigureRegistry
        for ID,fig in mainFigures.items():
            self.openMainFigure(mainFigure=fig, figureID = ID)
            #mainFigure.updateComboSettings(mainFigureComboSettings[ID])
            

    def openMainFigure(self,event=None,mainFigure=None, figureID = None):
        ""
        mainFigure = MainFigure(parent=self, mainController = self.mC, mainFigureRegistry = self.mainFigureRegistry, mainFigure = mainFigure, figureID = figureID)
        mainFigure.show()
        return mainFigure

    def updateColorScaleInClustermap(self, scaleString = "Raw data"):
        ""
        if scaleString not in ['raw values','center 0','min = -1, max = 1','Custom values']:
            return
        if scaleString == "Custom values":
            try:
                askLimits = ICDataInput(title = "Cluster color map limits.",valueNames = ["min","max"], valueTypes = {"min":float,"max":float})
                if askLimits.exec_():
                    minValue, maxValue = askLimits.providedValues["min"], askLimits.providedValues["max"]
                    self.mC.config.setParam("colorMapLimits","custom")
                    self.mC.config.setParam("colorMapLimits.min",minValue)
                    self.mC.config.setParam("colorMapLimits.max",maxValue)
                    exists,graph = self.mC.getGraph()
                    if exists:
                        graph.updateClim()
            except Exception as e:
                print(e)
        else:
            try:
                self.mC.config.setParam("colorMapLimits",scaleString)
                self.mC.mainFrames["middle"].ICPlotter.graph.updateClim()
            except Exception as e:
                print(e)
    
    def setEnforceRowLabeling(self,event=None):
        "Enfore/Disable row Labeling"
        plt = self.mC.mainFrames["middle"].plotter
        currentValue = plt.numRows
        if currentValue == np.inf:
            updatedValue = plt.defaultNumRows 
        else:
            updatedValue = np.inf
        
        setattr(plt,"numRows",updatedValue)
        #check if hclust is at the moment in use
        if plt.currentPlotType in ['hclust','corrmatrix']:
            plotterInUse = plt.nonCategoricalPlotter
            #check if plotter is not none
            if plotterInUse is not None:
                setattr(plotterInUse._hclustPlotter, "numRows", updatedValue)
                #update row labels
                plotterInUse._hclustPlotter.on_ylim_change()
    
    def setDodge(self,event=None):
        ""
        plt = self.mC.mainFrames["middle"].plotter
        currentValue = plt.getDodge()
        if self.sender().text() == "True":
            self.sender().setText("False")
        else:
            self.sender().setText("True")
        plt.setDodge(not currentValue)
    

    def showCorrResults(self,event=None):
        ""
        
        exists, graph = self.mC.getGraph()
        if exists:
            if self.mC.getPlotType() == "corrmatrix":
                
                corrMatrixData = graph.getPlotData()
                dlg = PandaTableDialog(parent=self,df = corrMatrixData, addToMainDataOption = False, ignoreChanges =  True)
                dlg.exec_()

            else:
                warn = WarningMessage(title="Error",infoText="No data found. Perform clustering first.")
                warn.exec_()

    def toggleAnnotations(self,e=None):
        ""
        self.mC.config.toggleParam("annotate.in.all.plots")

        self.sender().setText("{} annotations in all subplots".format("Disable" if self.mC.config.getParam("annotate.in.all.plots") else "Enable")) 


    def openConfig(self,event=None):
        ""
        cdl = ConfigDialog(self.mC)
        cdl.exec_()

    def getFileSaveFileName(self):
        workingDir = self.mC.config.getParam("WorkingDirectory")
        fileName,_ = QFileDialog.getSaveFileName(self,"Save HClust Map",os.path.join(workingDir,"HClustExport.xlsx"),"Excel Files (*.xlsx)")
        return fileName

    def exportHClustToExcel(self,event=None):
        ""
        if self.mC.getPlotType() != "hclust":
            w = WarningMessage(infoText="Perform hierarchical clustering first.")
            w.exec_()
            return

        fileName = self.getFileSaveFileName()
        if fileName != "":
            exists,graph = self.mC.getGraph()
            if exists:
                colorArray = graph.getColorArray()
                clusteredData = graph.getClusteredData()
                clusterLabels, clusterColors = graph.getClusterLabelsAndColor()
                print(clusterLabels, clusterColors)
                dataID = self.mC.getDataID()

                fkey = "data::exportHClustToExcel"
                kwargs = dict(dataID = dataID,
                                        pathToExcel = fileName,
                                        clusteredData = clusteredData,
                                        colorArray = colorArray,
                                        totalRows = clusteredData.index.size,
                                        clusterLabels = clusterLabels,
                                        clusterColors = clusterColors)
                funcProps = {"key":fkey,"kwargs":kwargs}
                #send to thread
                self.mC.sendRequestToThread(funcProps)