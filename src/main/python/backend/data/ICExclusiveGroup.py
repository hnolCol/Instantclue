
import pandas as pd 
import numpy as np 
from collections import OrderedDict

class ICExlcusiveGroup(object):
    ""
    def __init__(self, grouping, sourceData):

        self.sourceData = sourceData 
        self.grouping = grouping
        

    def findExclusivePositives(self,dataID):
        ""
        return self._findExclusives(dataID)

    def findExclusiveNegatives(self,dataID):
        ""
        return self._findExclusives(dataID,findPositives=False)

    def _findExclusives(self,dataID,findPositives=True):
        ""
        groupColumnNames = self.grouping.getColumnNames() 
        data = self.sourceData.getDataByColumnNames(dataID,groupColumnNames)["fnKwargs"]["data"]
        #init results
        columnGrouping = self.grouping.getCurrentGrouping()
       # exclusiveQuant = pd.DataFrame([""] * self.sourceData.getRowNumber(dataID), index = self.sourceData.getIndex(dataID), columns = list(columnGrouping.keys()))
        results = OrderedDict([(idx,[]) for idx in self.sourceData.getIndex(dataID)])
        for groupName, columnNames in columnGrouping.items():
            restColumns = [colName for colName in groupColumnNames if colName not in columnNames.values]
            if findPositives:
                background = data[restColumns].dropna(thresh=1)#len(restColumns)) 
                fullTargets = data[columnNames].dropna(thresh=columnNames.size)
                idcs = fullTargets.index.difference(background.index)
            else:
                background = data[restColumns].dropna(thresh=self.grouping.exclusivesMinNonNaN)#len(restColumns)) 
                nonEmptyTargets = data[columnNames].dropna(thresh=1)
                idcs = background.index.difference(nonEmptyTargets.index)
            for idx in idcs:
                results[idx].append(groupName)
                
            
            
        X = pd.DataFrame(data = [", ".join(groupNames) if len(groupNames) > 0 else "-" for groupNames in results.values()], index=list(results.keys()), columns = ["Exclusively"])
        return X