from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# internal imports
from ui.custom.Widgets.ICButtonDesgins import LabelButton, TooltipButton, SizeButton, ColorButton, FilterButton, SelectButton , MarkerButton, SubsetDataButton
from ui.custom.tableviews.ICColorTable import ICColorTable 
from ui.custom.tableviews.ICSizeTable import ICSizeTable
from ui.custom.tableviews.ICLabelTable import ICLabelTable
from ui.custom.tableviews.ICMarkerTable import ICMarkerTable
from ui.custom.tableviews.ICStatisticTable import ICStatisticTable
from ui.custom.tableviews.ICQuickSelectTable import ICQuickSelectTable
from ..dialogs.Marks.ICColorChooser import ColorChooserDialog
from ..dialogs.Marks.ICSizeDialog import ICSizeDialog
from ..dialogs.Filter.ICCategoricalFilter import CategoricalFilter, FindStrings, CustomCategoricalFilter
from ..dialogs.Filter.ICNumericFilter import NumericFilter
from ui.custom.warnMessage import WarningMessage,AskOptionsMessage
from ..utils import createSubMenu, createLabel, getStdTextColor, getLargeWidgetBG
from ..tooltips import SLICE_MARKS_TOOLTIPSTR

import seaborn as sns
from backend.utils.stringOperations import mergeListToString

#selection sqaure size in percentage of axis limits
selectValueMatch = {"Single":0,"small (2%)":0.02,"middle (5%)":0.05,"huge (10%)":0.1,"extra huge (15%)":0.15}

class ThreadCircle(QWidget):
    def __init__(self, parent=None):
        super(ThreadCircle, self).__init__(parent)
        self.setFixedSize(QSize(30,30))
        self._circleColor = 0
        self._colors = sns.color_palette("RdYlBu",n_colors=60).as_hex()
        self.animation = QPropertyAnimation(self, b"circleColor", self)
        self.animation.setKeyValueAt(0,1)
        self.animation.setKeyValueAt(0.5,59)
        self.animation.setKeyValueAt(1,1)
        #self.animation.setStartValue(0)
        #self.animation.setEndValue(9)
        self.animation.setLoopCount(-1)
        self.animation.setDuration(8000)
        self.animation.start()



    @pyqtProperty(int)
    def circleColor(self):
        return self._circleColor

    @circleColor.setter
    def circleColor(self, value):
        self._circleColor = value
        self.update()

    def paintEvent(self, ev=None):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        c = QColor(self._colors[self._circleColor])
        painter.setBrush(c)
        pen = QPen(QColor(getStdTextColor()))
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.drawEllipse(15,15,13,13)



class ThreadWidget(QWidget):
    def __init__(self, parent=None):
        super(ThreadWidget, self).__init__(parent)
        self.setFixedHeight(120)

        self.maxThreads = 1
        self.activeThreads = dict() 
        self.__controls()
        self.__layout() 


    def __controls(self):
        ""
        self.threadInfoText = createLabel("Threads")
        self.threadCompletedMsg = createLabel("")
        self.threadCompletedMsg.setFixedWidth(200)
        self.threadCompletedMsg.setWordWrap(True)

    def __layout(self):
        ""

       
        self.setLayout(QVBoxLayout())
        
        self.threadCircleLayout = QHBoxLayout()
        self.threadCircleLayout.setContentsMargins(0,0,0,0)
        self.threadCircleLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignLeft)
        #self.layout().setVerticalSpacing(1)
        self.layout().addWidget(self.threadInfoText)
        self.layout().addLayout(self.threadCircleLayout)
        self.layout().addWidget(self.threadCompletedMsg)
        self.layout().addStretch()

    def addActiveThread(self,ID, fnKey):
        ""
        self.activeThreads[ID] = ThreadCircle()
        self.activeThreads[ID].setToolTip("Task: {}\nID: {}".format(fnKey,ID))
        self.threadCircleLayout.addWidget(self.activeThreads[ID])
        self.updateThreadText()
        
        
    def setMaxThreadNumber(self,n):
        ""
        self.maxThreads = n
        self.updateThreadText()
    
    def threadFinished(self, ID, msg):
        ""
        self.layout().removeWidget(self.activeThreads[ID])
        self.activeThreads[ID].deleteLater()
        del self.activeThreads[ID]
        self.updateThreadText()
        self.updateMessageText(msg)
    
    def updateThreadText(self):
        ""
        self.threadInfoText.setText("Threads ({}/{})".format(len(self.activeThreads),self.maxThreads))

    def updateMessageText(self, msg):
        ""
        self.threadCompletedMsg.setText(f"{msg}")
        

class SliceMarksFrame(QWidget):
    def __init__(self,parent=None, mainController = None):
        
        super(SliceMarksFrame, self).__init__(parent)

        self.mC = mainController
        self.__controls()
        self.__layout() 
        self.__connectEvents()
      
    def __controls(self):
        #control background role
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(getLargeWidgetBG()))
        self.setPalette(p)
        self.setAutoFillBackground(True)
        #create buttons
        self.colorButton = ColorButton(self, 
                                tooltipStr=SLICE_MARKS_TOOLTIPSTR["color"], 
                                callback = self.handleColorDrop, 
                                getDragType = self.getDragType, 
                                acceptDrops=True,
                                acceptedDragTypes= ["Categories" , "Numeric Floats","Integers"])

        self.sizeButton = SizeButton(self, 
                                tooltipStr = SLICE_MARKS_TOOLTIPSTR["size"], 
                                callback = self.handleSizeDrop, 
                                getDragType = self.getDragType, 
                                acceptDrops=True,
                                acceptedDragTypes= ["Categories" , "Numeric Floats","Integers"])

        self.markerButton = MarkerButton(self,
                                tooltipStr = SLICE_MARKS_TOOLTIPSTR["marker"], 
                                acceptDrops = True,
                                callback = self.handleMarkerDrop, 
                                getDragType = self.getDragType,
                                acceptedDragTypes= ["Categories"])

        self.toolTipButton = TooltipButton(self, tooltipStr=SLICE_MARKS_TOOLTIPSTR["tooltip"],
                                callback= self.handleTooltipDrop,
                                getDragType = self.getDragType,
                                acceptDrops = True,
                                acceptedDragTypes= ["Categories" , "Numeric Floats", "Integers"])



        self.labelButton = LabelButton(self, 
                                tooltipStr=SLICE_MARKS_TOOLTIPSTR["label"],
                                callback= self.handleLabelDrop,
                                getDragType = self.getDragType,
                                acceptDrops = True,
                                acceptedDragTypes= ["Categories" , "Numeric Floats", "Integers"])
                                

        self.filterButton = FilterButton(self, 
                    callback=self.applyFilter, 
                    getDragType = self.getDragType ,
                    acceptDrops=True ,
                    tooltipStr=SLICE_MARKS_TOOLTIPSTR["filter"], 
                    acceptedDragTypes= ["Categories" , "Numeric Floats", "Integers"],
                    menuFn = self.showSettingMenu,
                    menuKeyWord = "Filter")

        self.selectButton = SelectButton(self, tooltipStr=SLICE_MARKS_TOOLTIPSTR["select"])
        self.subsetDataButton = SubsetDataButton(#DropButton(parent=self,
            callback = self.subsetData,
            getDragType= self.getDragType,
            acceptDrops= True,

            tooltipStr = "Subset Data\nDrop categorical columns to split data on unique values.\nNaN Object String ('-') will be ignored by default.\nCan be controlled using the parameter 'data.quick.subset.ignore.nanString' in 'Data Settings'"
                )
        self.tableScrollArea = QScrollArea(parent = self)
        self.colorTable = ICColorTable(mainController=self.mC)
        self.quickSelectTable = ICQuickSelectTable(mainController=self.mC)
        self.sizeTable = ICSizeTable(mainController=self.mC)
        self.labelTable = ICLabelTable(mainController=self.mC)
        self.tooltipTable = ICLabelTable(mainController=self.mC, header="Tooltip")
        self.statisticTable = ICStatisticTable(mainController=self.mC)
        self.markerTable = ICMarkerTable(mainController=self.mC)
        
        self.scrollWidget = QWidget()
        p = self.scrollWidget.palette()
        p.setColor(self.scrollWidget.backgroundRole(), QColor(getLargeWidgetBG()))
        self.scrollWidget.setPalette(p)

        self.tableScrollArea.setWidget(self.scrollWidget)
        self.tableScrollArea.setWidgetResizable(True)
        self.tableScrollArea.setContentsMargins(0,0,0,0)
        self.tableScrollArea.setFrameShape(QFrame.Shape.NoFrame)
        

        self.threadWidget = ThreadWidget()
        

    def __layout(self):
        ""

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(5,0,5,0)

        topGrid = QGridLayout()
        topGrid.setContentsMargins(2,2,2,2)
        topGrid.setSpacing(10)
        topGrid.addWidget(self.filterButton,0,2)
        topGrid.addWidget(self.selectButton,0,0)
        topGrid.addWidget(self.subsetDataButton,0,1)
        topGrid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bottomGrid = QGridLayout()
        bottomGrid.setContentsMargins(2,2,2,2)
        bottomGrid.setSpacing(10)
        bottomGrid.addWidget(self.colorButton,0,0)
        bottomGrid.addWidget(self.sizeButton,0,1)
        bottomGrid.addWidget(self.markerButton,0,2)
        bottomGrid.addWidget(self.labelButton,2,0)
        bottomGrid.addWidget(self.toolTipButton,2,1)
        bottomGrid.setAlignment(Qt.AlignmentFlag.AlignCenter)
       

        self.layout().addWidget(QLabel("Slice data"))
        self.layout().addLayout(topGrid)
        self.layout().addWidget(QLabel("Marks"))
        self.layout().addLayout(bottomGrid)
        self.layout().addWidget(self.tableScrollArea)
        
        tableVBox = QVBoxLayout()

        tableVBox.addWidget(self.colorTable)
        tableVBox.addWidget(self.quickSelectTable)
        tableVBox.addWidget(self.sizeTable)
        tableVBox.addWidget(self.markerTable)
        tableVBox.addWidget(self.labelTable)
        tableVBox.addWidget(self.tooltipTable)
        tableVBox.addWidget(self.statisticTable)
        tableVBox.addStretch(1)
        tableVBox.setContentsMargins(0,0,0,0)

        self.scrollWidget.setLayout(tableVBox)
       # self.scrollWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
        #self.layout().addStretch(1)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        #self.layout().addStretch(1)
        self.layout().addWidget(self.threadWidget)
        #self.layout().addWidget(self.spinner)

    def __connectEvents(self):
        ""
        self.selectButton.clicked.connect(self.chooseSelectMode)
        self.colorButton.clicked.connect(self.chooseColor)
        self.sizeButton.clicked.connect(self.chooseSize)
        self.labelButton.clicked.connect(lambda: self.mC.getTable("labelTable").showAnnotationsInDataTable())
        #self.filterButton.clicked.connect(self.applyFilter)


    def chooseSelectMode(self,e = None):
        ""
        menu = createSubMenu(subMenus=["Point Selection","Rectangle Selection"])
        menu["main"].addMenu(menu["Rectangle Selection"])
        for ellipseSize in ["small (2%)","middle (5%)","huge (10%)","extra huge (15%)"]:
            menu["Rectangle Selection"].addAction(ellipseSize)
        menu["Point Selection"].addAction("Single")
        #menu["Point Selection"].addAction("Lasso")
        #find bottom left corner
        bottomLeft = self.findSendersBottomLeft(self.sender())
        #cast menu
        action = menu["main"].exec(bottomLeft)
        if action:
            self.adjustSelectMode(mode = action.text())

    def subsetData(self):
        ""
        columnNames = self.mC.mainFrames["data"].getDragColumns()
        dataID = self.mC.getDataID()
        funcProps = {"key":"filter::splitDataFrame","kwargs":{"dataID" : dataID,"columnNames":columnNames}}
        self.mC.sendRequestToThread(funcProps)

    def showSettingMenu(self,menuKeyWord,sender):
        ""
        bottomLeft = self.findSendersBottomLeft(sender)
        menu = self.mC.createSettingMenu(menuKeyWord)
        menu.exec(bottomLeft)
        
    def findSendersBottomLeft(self,sender):
        ""
        #find bottom left corner
        senderGeom = sender.geometry()
        bottomLeft = self.mapToGlobal(senderGeom.bottomLeft())
        #set sender status 
        if hasattr(sender,"mouseOver"):
            sender.mouseOver = False
        return bottomLeft

    def chooseColor(self,event=None):
        ""
        bottomLeft = self.findSendersBottomLeft(self.sender())
        #cast menu
        dlg = ColorChooserDialog(mainController = self.mC)
        dlg.setGeometry(bottomLeft.x(),bottomLeft.y(),350,300)
        dlg.exec() 
    
    def chooseSize(self,event=None):
        ""
        bottomLeft = self.findSendersBottomLeft(self.sender())
        dlg = ICSizeDialog(mainController=self.mC)
        dlg.setGeometry(bottomLeft.x(),bottomLeft.y(),250,200)
        dlg.exec() 

    def checkGraph(self):
        ""
        exists, graph = self.mC.getGraph()
        if not exists:
            w = WarningMessage(infoText="Create a chart first.", iconDir = self.mC.mainPath)
            w.exec() 
        return exists, graph
    
    def applyFilter(self, event = None, columnNames = None, dragType = None, dataID = None, filterType = "category"):
        ""            
        
        dataFrame = self.mC.mainFrames["data"]
        if dataID is None:
            dataID = dataFrame.getDataID()
        if columnNames is None:
            columnNames = dataFrame.getDragColumns()

        if dragType is None:
            dragType = dataFrame.getDragType()

        if dragType == "Integers": 
            
            w = AskOptionsMessage(
                parent=self,
                options = ["Numeric","Categorical"],
                infoText = "Filtering integers can be performed by applying a numeric filter (greater than, between two numbers) or categorical filter (int == 3)", 
                title="How to filter integer column.",
                iconDir = self.mC.mainPath)
            if not w.exec(): return 
            if w.selectedOption == "Categorical":
                dragType = "Categories"
            
        if dragType == "Categories":
            
                filterType = self.mC.data.categoricalFilter.setupLiveStringFilter(dataID,columnNames, filterType = filterType)
                if filterType == "category":
                    self.filterDlg = CategoricalFilter(mainController = self.mC, categoricalColumns = columnNames)
                elif filterType == "string":
                    self.filterDlg = FindStrings(mainController = self.mC, categoricalColumns = columnNames)
                elif filterType == "multiColumnCategory":
                    self.filterDlg = CustomCategoricalFilter(mainController = self.mC, categoricalColumns = columnNames)
        else:
            
                self.filterDlg = NumericFilter(mainController = self.mC, selectedNumericColumn = columnNames)
        if hasattr(self,"filterDlg"):
            self.filterDlg.exec()
    
    def handleColorDrop(self):
        ""
        plotType = self.mC.getPlotType()
        if plotType == "scatter":
            fkey = "plotter:getScatterColorGroups"
        elif plotType == "hclust":
            fkey = "plotter:getHclustColorGroups"
        elif plotType == "swarmplot":
            fkey = "plotter:getSwarmColorGroups"
        else:
            return
        columnNames = self.mC.mainFrames["data"].getDragColumns()
        dragType = self.mC.mainFrames["data"].getDragType()
        dataID = self.mC.mainFrames["data"].getDataID()
        funcProps = {"key":fkey,"kwargs":{"dataID":dataID,"colorColumn":columnNames,"colorColumnType":dragType}}
        self.mC.sendRequestToThread(funcProps)

    def handleLabelDrop(self):
        ""
        try:
            plotType = self.mC.getPlotType()
            columnNames = self.mC.mainFrames["data"].getDragColumns()
            dataID = self.mC.mainFrames["data"].getDataID()
            exists, graph = self.checkGraph()
            if exists:
                if plotType not in ["scatter","hclust"]:
                    w = WarningMessage(infoText="Labels can not be assigned to this plot type.",iconDir = self.mC.mainPath)
                    w.exec()
                else:
                    graph.addAnnotations(columnNames,dataID)
            
        except Exception as e:
            print(e)

    def handleMarkerDrop(self):
        ""
        
        columnNames = self.mC.mainFrames["data"].getDragColumns()
        dragType = self.mC.mainFrames["data"].getDragType()
        dataID = self.mC.mainFrames["data"].getDataID()
        fkey = "plotter:getScatterMarkerGroups"
        funcProps = {"key":fkey,"kwargs":{"dataID":dataID,"markerColumn":columnNames,"markerColumnType":dragType}}
        self.mC.sendRequestToThread(funcProps)

    def handleSizeDrop(self):
        ""
        plotType = self.mC.getPlotType()
        if plotType == "scatter":
            fkey = "plotter:getScatterSizeGroups"
        elif plotType == "hclust":
            fkey = "plotter:getHclustSizeGroups"
        else:
            return
        columnNames = self.mC.mainFrames["data"].getDragColumns()
        dragType = self.mC.mainFrames["data"].getDragType()
        dataID = self.mC.mainFrames["data"].getDataID()
        funcProps = {"key":fkey,"kwargs":{"dataID":dataID,"sizeColumn":columnNames,"sizeColumnType":dragType}}
        self.mC.sendRequestToThread(funcProps)

    def handleTooltipDrop(self):
        ""
        plotType = self.mC.getPlotType()
        columnNames = self.mC.mainFrames["data"].getDragColumns()
        dataID = self.mC.mainFrames["data"].getDataID()
        exists, graph = self.checkGraph()
        if exists:
            if plotType not in ["scatter","hclust","swarmplot","x-ys-plot"]:
                w = WarningMessage(infoText="Tooltips can not be assigned to this plot type.",iconDir = self.mC.mainPath)
                w.exec()
            else:
                graph.addTooltip(columnNames,dataID)

    def updateFilter(self,boolIndicator,resetData=False):
        ""
        if hasattr(self,"filterDlg"):
            self.filterDlg.updateModelDataByBool(boolIndicator,resetData)

    def adjustSelectMode(self, mode):
        ""
        if mode in selectValueMatch:
            r = selectValueMatch[mode]
            self.mC.config.setParam("selectionRectangleSize",r)

    def getDragType(self):
        ""
        return self.mC.mainFrames["data"].getDragType()

    def sendRequestToThread(self,funcProps, addDraggedColumns = True, addDataID = True):
        
        if "kwargs" not in funcProps:
            funcProps["kwargs"] = dict()
        if addDraggedColumns:
            funcProps["kwargs"]["columnNames"] = self.mC.mainFrames["data"].getDragColumns()
        if addDataID:
            funcProps["kwargs"]["dataID"] = self.mC.mainFrames["data"].getDataID()
        self.mC.sendRequestToThread(funcProps)
    
  
    def setColorGroupData(self,colorGroupData,title="",isEditable = True, encodedColumnNames = None):
        ""
        self.colorTable.setData(colorGroupData,title,isEditable,encodedColumnNames)

    def setSizeGroupData(self,sizeGroupData,title="", isEditable = True,encodedColumnNames = None):
        ""
        self.sizeTable.setData(sizeGroupData,title,isEditable,encodedColumnNames)

    def setQuickSelectData(self,quickSelectData,title="",isEditable=True, encodedColumnNames = None):
        ""
        self.quickSelectTable.setData(quickSelectData,title,isEditable,encodedColumnNames)

    def setMarkerGroupData(self,markerGroupData,title="", encodedColumnNames = None):
        ""
        self.markerTable.setData(markerGroupData,title,encodedColumnNames)