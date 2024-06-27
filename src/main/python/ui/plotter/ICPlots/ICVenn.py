

from .ICChart import ICChart
from collections import OrderedDict
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Circle
import numpy as np
import pandas as pd 
from typing import Iterable

from ...utils import createMenu

class ICVenn(ICChart):
    ""
    def __init__(self,*args,**kwargs):
        ""
        super(ICVenn,self).__init__(*args,**kwargs)
        self.circles = OrderedDict()
        self.hoverCircles = OrderedDict()
        self.alpha = 0.3
        
        self.addHoverBinding()

    def annotateGroup(self, groupName):
        ""
        data = self.data["groupBy"].get_group(groupName)
        dataID = self.data["dataID"]
        columnName = f"{groupName} ({''.join(self.data['categorialColumns'])})"
        funcProps = {
                "key" : "data::annotateDataByIndicies",
                "kwargs" : {
                    "dataID" : dataID,
                    "indices" : data.index.values,
                    "columnName" : columnName
                }
            }
        self.mC.sendRequestToThread(funcProps)

    def subsetGroup(self, groupName):
        "" 
        data = self.data["groupBy"].get_group(groupName)
        dataIndex = data.index.values
        dataID = self.data["dataID"]
        subsetName = "subset:({})_({})".format(groupName,self.mC.data.getFileNameByID(dataID))
        funcProps = {"key":"data::subsetDataByIndex","kwargs":{"dataID":dataID,"filterIdx":dataIndex,"subsetName":subsetName}}
        self.mC.sendRequestToThread(funcProps)

    def addGraphSpecActions(self,menus : dict) -> None:
        ""
        menus["main"].addAction("Counts", self.displayCountData)
            
        for groupName in self.data["groupBy"].groups:
            menus["Annotate In Dataset.."].addAction(f"{groupName} ({self.data['counts'][groupName]})", lambda groupName = groupName: self.annotateGroup(groupName))
            menus["Create Subset .."].addAction(f"{groupName} ({self.data['counts'][groupName]})", lambda groupName = groupName: self.subsetGroup(groupName))

            
    
    def getGraphSpecMenus(self):
        ""
        return ["Annotate In Dataset..", "Create Subset .."]

    def drawCircle(self,ax : Axes, x, y, r, c, fill = True, alpha : float = 0.3):
        ""
        c = Circle(xy = (x,y), radius=r, fill = fill, facecolor = c, ec = "black", alpha = alpha)
        ax.add_patch(c)
        return c 

    def addColumnLabels(self, onlyForID = None, targetAx = None):
        ""
        labelTextProps = self.data["labelTextProps"]
        for internalID, textProps in labelTextProps.items():
            if targetAx is None:
                ax = self.axisDict[0]
            else:
                ax = targetAx 
            xy,s,kwargs = textProps
            
            ax.text(x=xy[0],y=xy[1], s = s, **kwargs)
        
        
        
    def addLabels(self, onlyForID = None, targetAx = None):
        ""
        textProps = self.data["textProps"]
        labels = self.data["labels"]
        if isinstance(textProps,dict):
            for setName, textPosition in textProps.items():
                if setName in labels:
                    if targetAx is None:
                        ax = self.axisDict[0]
                    else:
                        ax = targetAx
                    ax.text(x = textPosition[0], y = textPosition[1], s = labels[setName], va="center", ha="center")
            #self.addText(self.axisDict[0], x = textPosition[0], y = textPosition[1], s = "2")
        
        # def addText(self,ax,axisTransform  = False, stdTextFont = True,  *args,**kwargs) -> None:
		# ""
		# kwargs["transform"] = ax.transAxes if axisTransform else None
		# if stdTextFont:
		# 	kwargs["fontproperties"] = self.getStdFontProps()#"fontproperties"
		# ax.text(*args,**kwargs)


    def displayCountData(self):
        "" 
        if "categorySizes" in self.data:
            self.mC.mainFrames["data"].openDataFrameinDialog(pd.DataFrame(self.data["counts"].reset_index()), 
                                    ignoreChanges=True, 
                                    headerLabel="Venn Diagram Data.", 
                                    tableKwargs={"forwardSelectionToGraph":False})

    def initVenn(self, onlyForID = None, targetAx = None):
        ""

        try:
            for n,(xy,r) in enumerate(self.data["circleProps"]):
                internalID = self.data["internalIDs"][n]
                color = self.data["dataColorGroups"].loc[self.data["dataColorGroups"]["internalID"] == internalID,"color"].values[0]
                if targetAx is None:
                    ax = self.axisDict[0]
                else:
                    ax = targetAx
                circle = self.drawCircle(ax,xy[0],xy[1],r,color,self.alpha)
                self.circles[internalID] = circle
                
        except Exception as e:
            print(e)
            pass 

    def onDataLoad(self, data):
        ""
       
        try:
            
            self.data = data

            self.initAxes(data["axisPositions"])
            #set axis limits
            for n,ax in self.axisDict.items():
                if n in self.data["axisLimits"]:
                    self.setAxisLimits(ax,
                            self.data["axisLimits"][n]["xLimit"],
                            self.data["axisLimits"][n]["yLimit"])
            self.axisDict[0].set_aspect("equal")
            self.setAxisOff(self.axisDict[0])
            self.initVenn()
            self.addLabels()
            self.addColumnLabels()
            self.setDataInColorTable(self.data["dataColorGroups"], title = "Categorical Columns")
            self.updateFigure.emit()
            
           
           
        except Exception as e:
            print(e)
        
    def onHover(self, event=None):
       # print(event)
        
        mouseOverCircleID = [internalID for internalID,circle in self.circles.items() if circle.contains(event)[0]] 
        if len(mouseOverCircleID) == len(self.hoverCircles) and len(mouseOverCircleID) > 0 and all(n in self.hoverCircles for n in mouseOverCircleID):
            return #all already set
        if len(mouseOverCircleID) == 0 and all(circle.get_alpha() < 0.8 for circle in self.circles.values()):
            return #nothing to do here 
        self.hoverCircles.clear()
        for internalID, circle in self.circles.items():
            if internalID in mouseOverCircleID:
                circle.set_alpha(0.5)
            else:
                circle.set_alpha(self.alpha)

        self.updateFigure.emit()

    def setHoverData(self,dataIndex : Iterable, showText : bool = False):
        ""
        


    def setHoverObjectsInvisible(self):
        ""
        

    def getInternalIDByColor(self, color : str):
        ""
        colorGroupData = self.data["dataColorGroups"]
        boolIdx = colorGroupData["color"].values ==  color
        if np.any(boolIdx):
            return colorGroupData.loc[boolIdx,"internalID"].values[0]

    def updateGroupColors(self,colorGroup : pd.DataFrame,changedCategory : str|None = None):
        "changed category is encoded in a internalID"

        for internalID, color in colorGroup[["internalID","color"]].values:
            if internalID in self.circles:
                circle = self.circles[internalID]
                circle.set_facecolor(color)
            
        if hasattr(self,"colorLegend"):
            self.addColorLegendToGraph(colorGroup,update=False)
        
        self.updateFigure.emit()
        

    

    def updateBackgrounds(self):
        "Update Background for blitting"
        self.axBackground = dict()
        for ax in self.axisDict.values():
            self.axBackground[ax] = self.p.f.canvas.copy_from_bbox(ax.bbox)	
    
    def updateQuickSelectItems(self,propsData=None):
        "Saves lines by idx id"

    
    def updateQuickSelectData(self,quickSelectGroup,changedCategory=None):
        ""
       
    
    def mirrorQuickSelectArtists(self,axisID,targetAx):
        ""

    def mirrorAxisContent(self, axisID, targetAx,*args,**kwargs):
        ""

        targetAx.set_aspect("equal")
        self.setAxisOff(targetAx)
        self.initVenn(onlyForID=axisID,targetAx=targetAx)
        self.addLabels(onlyForID=axisID,targetAx=targetAx)
        self.addColumnLabels(onlyForID=axisID,targetAx=targetAx)
    def resetQuickSelectArtists(self):
        ""
        
            