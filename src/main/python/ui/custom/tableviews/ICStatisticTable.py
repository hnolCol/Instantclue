from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import * 

from ..utils import clearLayout, getStandardFont
from ...utils import getHoverColor, createSubMenu, createMenu, createLabel, createTitleLabel
from ...delegates.ICSpinbox import SpinBoxDelegate #borrow delegate
from .ICTableBase import ICTableBase, ICModelBase
from backend.utils.stringOperations import getReadableNumber
import pandas as pd
import numpy as np

class ICStatisticTable(ICTableBase):
    
    def __init__(self,*args,**kwargs):

        super(ICStatisticTable,self).__init__(*args,**kwargs)
        self.selectionChanged.connect(self.updateStatsInGraph)
        
        self.__controls()
        self.__layout()

    def __controls(self):
        ""
        self.mainHeader = createTitleLabel("Statistics",fontSize = 14)
        self.titleLabel = createLabel(text = self.title)
        self.table = StatisticTable(parent = self, mainController=self.mC)
        self.model = StatisticTableModel(parent=self.table)
        self.table.setModel(self.model)
       
        
        
    def __layout(self):
        ""
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.mainHeader)
        self.layout().addWidget(self.titleLabel)
        self.layout().addWidget(self.table)

    def resetSizeInGraph(self):
        ""
        exists, graph =  self.mC.getGraph()
        if exists:
            graph.setHoverObjectsInvisible()
            graph.resetSize()
        
    @pyqtSlot()
    def updateStatsInGraph(self):
        ""
        

    def toggleVisibility(self):
        ""
        exists, graph = self.mC.getGraph() 
        internalID = self.table.model().getCurrentInternalID()
        if exists:
            graph.toggleStatVisibilityByInternalID(internalID)
    
    def removeStats(self):
        ""
        exists, graph = self.mC.getGraph() 
        internalID = self.table.model().getCurrentInternalID()
        if exists:
            graph.removeStatsArtistsByInternalID(internalID)

class StatisticTableModel(ICModelBase):
    
    def __init__(self, labels = pd.DataFrame(), parent=None):
        super(StatisticTableModel, self).__init__(parent)
        self.initData(labels)

    def initData(self,labels):

        self._labels = labels
        self._inputLabels = labels.copy()

    def columnCount(self, parent=QModelIndex()):
        
        return 5

    def getDataIndex(self,row):
        ""
        if self.validDataIndex(row):
            return self._labels.index[row]

    def updateData(self,value,index):
        ""
        dataIndex = self.getDataIndex(index.row())
        if dataIndex is not None:
            self._labels[dataIndex] = value
            self._inputLabels = self._labels.copy()
            
    def setData(self,index,value,role):
        ""
        row =index.row()
        indexBottomRight = self.index(row,self.columnCount())
        if role == Qt.ItemDataRole.UserRole:
            self.dataChanged.emit(index,indexBottomRight)
            return True
        if role == Qt.CheckStateRole:
            self.setCheckState(index)
            self.dataChanged.emit(index,indexBottomRight)
            return True

    def data(self, index, role=Qt.ItemDataRole.DisplayRole): 
        "Shows data"
        if not index.isValid(): 

            return QVariant()
            
        elif role == Qt.ItemDataRole.DisplayRole: 
            if index.column() < 2:
                
                value = self._labels.iloc[index.row(),index.column()]
                if isinstance(value,str):
                    try:
                        value = float(value)
                    except:
                        return str(self._labels.iloc[index.row(),index.column()])
                return str(getReadableNumber(value))
            else:
                return str(self._labels.iloc[index.row(),index.column()])
        
        elif role == Qt.ItemDataRole.FontRole:

            return getStandardFont()
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            if "visible" in self._labels.columns:
                if self._labels["visible"].iloc[index.row()]:
                    return QColor("black")
                else:
                    return QColor("grey")                
            return QColor("black")

        elif role == Qt.ItemDataRole.ToolTipRole:
            
            if "Group1" and "Group2" in self._labels.columns:
                return "Comparision:\n{}\nvs\n{}\nColumn Headers: p-value, test-statistic, Test".format(self._labels["Group1"].iloc[index.row()],self._labels["Group2"].iloc[index.row()])
            return ""

        elif self.parent().mouseOverItem is not None and role == Qt.ItemDataRole.BackgroundRole and index.row() == self.parent().mouseOverItem:
            return QColor(getHoverColor())

            
    def flags(self, index):
        "Set Flags of Column"
        if index.column() == 0:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setNewData(self,labels):
        ""
        
        self.initData(labels)
        self.completeDataChanged()


class StatisticTable(QTableView):

    def __init__(self, parent=None, rowHeight = 22, mainController = None):

        super(StatisticTable, self).__init__(parent)
       
        self.setMouseTracking(True)
        self.setShowGrid(True)
        self.verticalHeader().setDefaultSectionSize(rowHeight)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)

        self.mainController = mainController
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 

        self.createMenu()

        self.rowHeight      =   rowHeight
        self.rightClick     =   False
        self.mouseOverItem  =   None
        self.sizeChangedForItem = None
        
        p = self.palette()
        p.setColor(QPalette.ColorRole.Highlight,QColor(getHoverColor()))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("black"))
        self.setPalette(p)

        self.setStyleSheet("""QTableView {background-color: #F6F6F6;border:None};""")


    def createMenu(self):
        ""
        menu = createSubMenu(None,[])
        menu["main"].addAction("Show/Hide", self.parent().toggleVisibility)
        menu["main"].addAction("Remove", self.parent().removeStats)
        menu["main"].addAction("Copy to clipboard",self.parent().copyToClipboard)
        menu["main"].addAction("Save to xlsx", self.parent().saveModelDataToExcel)
       
        self.menu = menu["main"]
    
    def leaveEvent(self,event=None):
        ""
        if hasattr(self, "mouseOverItem") and self.mouseOverItem is not None:
            prevMouseOver = int(self.mouseOverItem)
            self.mouseOverItem = None
            self.model().rowDataChanged(prevMouseOver)

    def mouseEventToIndex(self,event):
        "Converts mouse event on table to tableIndex"
        row = self.rowAt(event.pos().y())
        column = self.columnAt(event.pos().x())
        return self.model().index(row,column)
    
    def mousePressEvent(self,e):
        ""
       # super().mousePressEvent(e)
        if e.buttons() == Qt.MouseButton.RightButton:
            self.rightClick = True
        else:
            self.rightClick = False
            
            super().mousePressEvent(e)
    
    def mouseReleaseEvent(self,e):
        ""
        #reset move signal
        "Handles Mouse Release Events"
        if not self.model().dataAvailable():
            return
       
        try:
            tableIndex = self.mouseEventToIndex(e)
            if tableIndex is None:
                return
          
            #dataIndex = self.model().getDataIndex(tableIndex.row())
            #if tableIndexCol == 0 and not self.rightClick: 
                
                #if not self.rightClick:
              #      return

              #  else:
               #     return

               # self.sizeChangedForItem = tableIndex.row()
                
               # self.parent().selectionChanged.emit()
               # self.model().rowDataChanged(tableIndex.row())
                
                
            elif self.rightClick:
                #idx = self.model().index(0,0)
                self.rightClickedRowIndex = tableIndex.row()
                self.menu.exec(QCursor.pos() + QPoint(4,4))
                
                self.rightClick = False
            else:
                super().mouseReleaseEvent(e)

        except Exception as e:
            print(e)

    def mouseMoveEvent(self,event):
        
        ""
        if not self.model().dataAvailable():
            return
        rowAtEvent = self.rowAt(event.pos().y())
        
        if rowAtEvent == -1:
            self.mouseOverItem = None
        else:
            self.mouseOverItem = rowAtEvent
        self.model().rowDataChanged(rowAtEvent)
 
    def resizeColumns(self):
        ""
        columnWidths = [(0,40),(1,200)]
        for columnId,width in columnWidths:
            self.setColumnWidth(columnId,width)


        

