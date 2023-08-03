from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import * 

from ...utils import createTitleLabel, createLabel, createLineEdit, createMenu
from ...custom.utils import LabelLikeCombo
from ..Selections.ICDSelectItems import ICDSelectItems
from ...custom.Widgets.ICButtonDesgins import ICStandardButton, LabelLikeButton
from ...custom.warnMessage import WarningMessage
import pandas as pd 
from collections import OrderedDict

mergeParameters =   OrderedDict(
                    [
                    ('how',OrderedDict([(0,'left'),(1,'right'),(2,'outer'),(3,'inner')])),
					('indicator',OrderedDict([(0,'True'),(1,'False')])),
					('suffixes',['_x,_y']),
					('left data frame','all'),
					('right data frame','all')
                    ])

descriptionMerge = ['full outer: Use union of keys from both frames\n'+
                'inner: Use intersection of keys from both frames\n'+
                'left out.: Use keys from left frame only\n'+
                'right out.: Use keys from right frame only']


class ICDMergeDataFrames(QDialog):
    def __init__(self, mainController, *args, **kwargs):
        super(ICDMergeDataFrames, self).__init__(*args, **kwargs)
        self.setWindowTitle("Merge data frames.")
        self.mC = mainController
        
        self.mergeParams = dict()
        self.dfWidgets = dict()
        #dict to collect merge parameters
        self.mergeParams["left"] = dict()
        self.mergeParams["right"] = dict()

        
        self.__controls()
        self.__layout()
        self.__connectEvents()

        #set size policy of dialog
        self.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Expanding)
        self.setFixedHeight(200)
        self.setMaximumHeight(200)

    def __controls(self):
        """Init widgets"""
        
        self.headerLabel = createTitleLabel("Merge Two Data Frames", fontSize=14)
        ### add menu button
        self.parameterGrid = self.addParameters()
        self.hbox1 = self.addDataFrame("left")
        self.hbox2 = self.addDataFrame("right")

        self.okButton = ICStandardButton(itemName="Merge")
        self.cancelButton = ICStandardButton(itemName = "Cancel")

        
        
    def __layout(self):

        """Put widgets in layout"""
        self.setLayout(QGridLayout())
        layout = self.layout()
        layout.addWidget(self.headerLabel)
        layout.addLayout(self.parameterGrid,2,0,1,4)
        layout.addLayout(self.hbox1,3,0,1,4)
        layout.addLayout(self.hbox2,4,0,1,4)
        layout.addWidget(self.okButton,6,0)
        layout.addWidget(self.cancelButton,6,3)
        layout.setColumnStretch(2,1)
        layout.setRowStretch(5,1)
        
        
       
       
    def __connectEvents(self):
        """Connect events to functions"""
        self.cancelButton.clicked.connect(self.close)
        self.okButton.clicked.connect(self.merge)
        
    def addDataFrame(self, dfID = "left"):
        """
        Add DataFrame related widgets to the QDialog. 
        Three options: 
        a) Selected the dataframe name
        b) Select Key columns to be used for merging
        c) Select columns to transfer to the merged data frame (if nothing selected, all columns will be attached.)
        """
        gridBox = QGridLayout()
        #data frame selection widgets
        dataFrameLabel = LabelLikeCombo(parent = self, 
                                        items = self.mC.data.fileNameByID, 
                                        text = "Data Frame ({})".format(dfID), 
                                        tooltipStr="Set Data Frame", 
                                        itemBorder=5)
        dataFrameLabel.selectionChanged.connect(self.dfSelected)

        #index columns selection
        mergeColumns = LabelLikeButton(parent = self, 
                        text = "Choose key column(s)", 
                        tooltipStr="Choose key column(s) used for merging\nValue must match in both data frames.", 
                        itemBorder=5)

        mergeColumns.clicked.connect(lambda _,paramID = "mergeColumns": self.openColumnSelection(paramID=paramID))
        
        columnsButton = ICStandardButton(itemName = "...", tooltipStr="Select columns to keep for merging (default: keep all).")
        columnsButton.setFixedSize(15,15)    
        columnsButton.clicked.connect(lambda _,paramID = "selectedColumns": self.openColumnSelection(paramID=paramID))

        #add widgets
        gridBox.addWidget(dataFrameLabel,0,0,Qt.AlignmentFlag.AlignLeft)
        gridBox.addWidget(mergeColumns,0,1,Qt.AlignmentFlag.AlignCenter)
        gridBox.addWidget(columnsButton,0,2,Qt.AlignmentFlag.AlignRight)

        #handle column stretch
        gridBox.setColumnStretch(0,2)
        gridBox.setColumnStretch(1,2)
        gridBox.setColumnStretch(2,0)

        self.dfWidgets[dfID] = [dataFrameLabel,mergeColumns,columnsButton]
        return gridBox

    def addParameters(self):
        ""
        try:
            grid = QGridLayout()
            paramTitle = createTitleLabel("Parameters",fontSize=11)
            howLabel = createLabel(text="How : ",tooltipText=descriptionMerge[0], fontSize = 12)
            self.howCombo = LabelLikeCombo(parent = self, items = mergeParameters["how"], text = "left", tooltipStr="Set data frame merge.", itemBorder=5)
            indicatorLabel = createLabel(text="Indicator : ",tooltipText="", fontSize = 12)
            self.indicatorCombo = LabelLikeCombo(parent = self, items = mergeParameters["indicator"], text = "True", tooltipStr="Adds an indicator for matches.", itemBorder=5)
            
            grid.addWidget(paramTitle,0,0,1,3,Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(howLabel,1,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.howCombo,1,1)
            grid.addWidget(indicatorLabel,2,0,Qt.AlignmentFlag.AlignRight)
            grid.addWidget(self.indicatorCombo,2,1)

        except Exception as e:
            print(e)
        return grid

    def dfSelected(self,item):
        ""
        dataID, fileName = item
        
        dfID = self.getDfID(self.sender())
        self.setDfParams(dfID,dataID)

    def setDfParams(self,dfID,dataID):

        self.mergeParams[dfID]["dataID"] = dataID
        self.mergeParams[dfID]["columnNames"] = self.mC.data.getPlainColumnNames(dataID)
        self.mergeParams[dfID]["mergeColumns"] = pd.Series(dtype="str")
        self.mergeParams[dfID]["selectedColumns"] = pd.Series(dtype="str")


    def getDfID(self,widget):
        ""
        if hasattr(self,"dfWidgets") and isinstance(self.dfWidgets,dict):
            if widget in self.dfWidgets["left"]:
                dfID = "left"
            else:
                dfID = "right"
            return dfID

    def merge(self,e=None):
        ""
        
        funcProps = {"key":"data::mergeDataFrames","kwargs":
                            {
                                "mergeParams":self.mergeParams,
                                "how": self.howCombo.getText(),
                                "indicator":self.indicatorCombo.getText() == "True"}
                    }
        self.mC.sendRequestToThread(funcProps)

    def openColumnSelection(self,event=None, paramID = None):
        ""
        try:
            dfID = self.getDfID(self.sender())
            if dfID in self.mergeParams:
                dfProps = self.mergeParams[dfID]
                if "columnNames" not in dfProps:
                    w = WarningMessage(title = "No data frame.", infoText = "Please select a dataframe first.",iconDir = self.mC.mainPath)
                    w.exec()
                    return
                selectableColumns = pd.DataFrame(dfProps["columnNames"])
                preSelectionIdx = dfProps[paramID].index
            
                dlg = ICDSelectItems(data = selectableColumns)
                dlg.model.setCheckStateByDataIndex(preSelectionIdx)

                # handle position and geomettry
                senderGeom = self.sender().geometry()
                bottomRight = self.mapToGlobal(senderGeom.bottomRight())
                h = dlg.getApparentHeight()
                dlg.setGeometry(bottomRight.x() + 15,bottomRight.y()-int(h/2),190,h)

                #handle result
                if dlg.exec():
                    selectedColumns = dlg.getSelection()
                    self.mergeParams[dfID][paramID] = pd.Series(selectedColumns.values[:,0],index = selectedColumns.index)
                    self.sender().setText(";".join([str(x) for x in selectedColumns.values.flatten()]))
           
                
        except Exception as e:
            print(e)
