import pandas as pd
import numpy as np
from collections import OrderedDict
from ..utils.stringOperations import getRandomString


def _lv_outliers(vals, k):
        """Find the outliers based on the letter value depth."""
        box_edge = 0.5 ** (k + 1)
        perc_ends = (100 * box_edge, 100 * (1 - box_edge))
        edges = np.percentile(vals, perc_ends)
        lower_out = vals[np.where(vals < edges[0])[0]]
        upper_out = vals[np.where(vals > edges[1])[0]]
        return np.concatenate((lower_out, upper_out))

def _lv_box_ends(vals, k_depth="tukey",trust_alpha=0.05,):
    """Get the number of data points and calculate `depth` of
    letter-value plot."""
    vals = np.asarray(vals)
    # Remove infinite values while handling a 'object' dtype
    # that can come from pd.Float64Dtype() input
    with pd.option_context('mode.use_inf_as_na', True):
        vals = vals[~pd.isnull(vals)]
    n = len(vals)
    p = 0.007
    if n > 0:
        # Select the depth, i.e. number of boxes to draw, based on the method
        if k_depth == 'full':
            # extend boxes to 100% of the data
            k = int(np.log2(n)) + 1
        elif k_depth == 'tukey':
            # This results with 5-8 points in each tail
            k = int(np.log2(n)) - 3
        elif k_depth == 'proportion':
            k = int(np.log2(n)) - int(np.log2(n * p)) + 1
        elif k_depth == 'trustworthy':
            point_conf = 2 * qf((1 - trust_alpha / 2)) ** 2
            k = int(np.log2(n / point_conf)) + 1
        else:
            k = int(k_depth)  # allow having k as input
        # If the number happens to be less than 1, set k to 1
        if k < 1:
            k = 1

        # Calculate the upper end for each of the k boxes
        upper = [100 * (1 - 0.5 ** (i + 1)) for i in range(k, 0, -1)]
        # Calculate the lower end for each of the k boxes
        lower = [100 * (0.5 ** (i + 1)) for i in range(k, 0, -1)]
        # Stitch the box ends together
        percentile_ends = [(i, j) for i, j in zip(lower, upper)]
        box_ends = [np.percentile(vals, q) for q in percentile_ends]
        return box_ends, k

def _width_functions(width_func):
    # Dictionary of functions for computing the width of the boxes
    width_functions = {'linear': lambda h, i, k: (i + 1.) / k,
                        'exponential': lambda h, i, k: 2**(-k + i - 1),
                        'area': lambda h, i, k: (1 - 2**(-k + i - 2)) / h}
    return width_functions[width_func]


def getAxisPosition(n,nRows = None, nCols = None, maxCol = 4):
    ""
    if nRows is None:
        if n < maxCol:
            nRows = 1
            nCols = n 

        else:
            nRows = int(np.ceil(n / maxCol))
            nCols = maxCol

    return OrderedDict([(n,[nRows,nCols,n + 1 ]) for n in range(n)])



def calculatePositions(dataID, sourceData, numericColumns, categoricalColumns, maxColumns, splitByCategories = False, **kwargs):
    """
    Return tickposition and axisPositions and colors
    """
    nCatCols = len(categoricalColumns)
    nNumCols = len(numericColumns)
    colorGroups  = pd.DataFrame()
    axisLimits = {}
    axisTitles = {}
    verticalLines = {}
    data = sourceData.getDataByColumnNames(dataID,numericColumns + categoricalColumns)["fnKwargs"]["data"]
    data = data.dropna(subset=numericColumns,how="all")

    scaleXAxis = sourceData.parent.config.getParam("scale.numeric.x.axis")
    splitString = sourceData.parent.config.getParam("split.string.x.category")
    splitIndex = sourceData.parent.config.getParam("split.string.index")


    if nCatCols == 0:
        
        groupedPlotData = data.describe()

        if data.index.size > 1:
            #calculate IQR and attach.
            IQR = pd.DataFrame(groupedPlotData.loc[["25%","75%"],:].diff().dropna(how="all").values.flatten().reshape(1,groupedPlotData.columns.size), index=["IQR"], columns=groupedPlotData.columns)
            groupedPlotData = pd.concat([groupedPlotData,IQR],axis=0)# groupedPlotData.append(IQR)

    elif splitByCategories:
        try :
            groupedPlotData = data.groupby(by=categoricalColumns,sort=False).describe()
            groupedPlotData.columns = ['_'.join(col).rstrip('_') for col in groupedPlotData.columns.values]
            columnNamesForIQR = [colName for colName in groupedPlotData.columns if "75%" in colName or "25%" in colName]
            if len(columnNamesForIQR) > 0:
                IQR = groupedPlotData[columnNamesForIQR].diff(axis=1)
                #filter for every second column 
                IQR = IQR[IQR.columns[1::2]]
                IQR.columns = [(colName[0],"IQR") for colName in columnNamesForIQR[1::2]]
            groupedPlotData = groupedPlotData.join(IQR)
        except Exception as e :
            print(e)
            groupedPlotData = pd.DataFrame()
   
    if not splitByCategories and nCatCols > 0:

        axisPostions = getAxisPosition(n = nNumCols, maxCol=2)

        uniqueValueIndex = {}
        tickPositionByUniqueValue = {}
        tickPositions = {}
        boxPositions = {} 
        faceColors = {}
        groupNames = {}
        plotData = {}
        #get unique values

        replaceObjectNan = sourceData.replaceObjectNan

        uniqueValuesByCatColumns = OrderedDict([(categoricalColumn,[cat for cat in data[categoricalColumn].unique() if cat != replaceObjectNan]) for categoricalColumn in categoricalColumns])
        uniqueValuesForCatColumns = [uniqueValuesByCatColumns[categoricalColumn]  for categoricalColumn in categoricalColumns] 
        uniqueValuesPerCatColumn = dict([(categoricalColumn,uniqueValuesForCatColumns[n]) for n,categoricalColumn in enumerate(categoricalColumns)])
        #numUniqueValuesPerCatColumn = dict([(categoricalColumn,len(uniqueValuesForCatColumns[n])) for n,categoricalColumn in enumerate(categoricalColumns)])
        
        uniqueCategories = ["Complete"] + ["{}:({})".format(uniqueValue,k) for k,v in uniqueValuesByCatColumns.items() for uniqueValue in v]
        colors,_ = sourceData.colorManager.createColorMapDict(uniqueCategories, as_hex=True)
        flatUniqueValues = ["Complete"] + [uniqueValue for sublist in uniqueValuesForCatColumns for uniqueValue in sublist]
        #drop "-"
        totalNumUniqueValues = np.array(uniqueValuesForCatColumns).flatten().size
        
        widthBox = 1/(totalNumUniqueValues + 1)
        border = widthBox/10
       
        colorGroups["color"] = colors.values()
        colorGroups["group"] = uniqueCategories
        colorGroups["internalID"] = [getRandomString() for n in colorGroups["color"].values]
        
        colorCategoricalColumn = "\n".join(categoricalColumns)
        #get data bool index

        groupedPlotData = []
        
        offset = 0 + border + widthBox/2
        tickPositionByUniqueValue["Complete"] = offset

        for categoricalColumn, uniqueValues in uniqueValuesPerCatColumn.items(): 
            uniqueValueIndex[categoricalColumn] = {}
            offset += widthBox/2 #extra offset by categorical column
            
            for uniqueValue in uniqueValues:
                offset += widthBox
                idxBool = data[categoricalColumn] == uniqueValue
                uniqueValueIndex[categoricalColumn][uniqueValue] = idxBool
                tickPositionByUniqueValue["{}:({})".format(uniqueValue,categoricalColumn)] = offset
                # if not uniqueValue == uniqueValues[-1]:
                #     offset += widthBox/5
        offset += border + widthBox/2
        
        for n,numericColumn in enumerate(numericColumns):
            #init lists to stare props
            filteredData = []
            verticalLines[n] = []
            boxPositions[n] = []
            tickPositions[n] = []
            faceColors[n] = []
            groupNames[n] = []
            # add complete data
            X = data[numericColumn].dropna()
            filteredData.append(X)
            describedX = X.describe()
            describedX = pd.concat([describedX,pd.Series(describedX["75%"]-describedX["25%"],index=["IQR"], name=numericColumn)])
           # describedX = describedX.append(pd.Series(describedX["75%"]-describedX["25%"],index=["IQR"], name=numericColumn))
            groupedPlotData.append(describedX)
            boxPositions[n].append(tickPositionByUniqueValue["Complete"] )
            tickPositions[n].append(tickPositionByUniqueValue["Complete"] )
            faceColors[n].append(colors["Complete"])
            groupNames[n].append("{}:Complete".format(numericColumn))
            #iterate through unique values
            for categoricalColumn, uniqueValues in uniqueValuesPerCatColumn.items():
                
                for m,uniqueValue in enumerate(uniqueValues):
                    
                    colorKey ="{}:({})".format(uniqueValue,categoricalColumn)
                    fc = colors[colorKey]
                    idxBool = uniqueValueIndex[categoricalColumn][uniqueValue]
                    uniqueValueFilteredData = data[numericColumn].loc[idxBool].dropna() 
                    tickBoxPos = tickPositionByUniqueValue[colorKey]
                    if m == 0:
                        verticalLines[n].append({
                            "label":categoricalColumn,
                            "color": "darkgrey",
                            "linewidth" : 0.5,
                            "x":tickBoxPos - widthBox/2 - widthBox/4})
                    if uniqueValueFilteredData.index.size > 0:
                        filteredData.append(uniqueValueFilteredData)
                        uniqueValueDescribed = uniqueValueFilteredData.describe()
                        dataColumnName = "{}:{}:{}".format(numericColumn,categoricalColumn,uniqueValue)
                        uniqueValueDescribed.name = dataColumnName 
                        #append IQR
                        IQRData = pd.Series(uniqueValueDescribed["75%"]-uniqueValueDescribed["25%"],index=["IQR"], name=dataColumnName)
                        uniqueValueDescribed = pd.concat([uniqueValueDescribed,IQRData])
                        groupedPlotData.append(uniqueValueDescribed)
                        boxPositions[n].append(tickBoxPos)
                        tickPositions[n].append(tickBoxPos)
                        faceColors[n].append(fc)
                        groupNames[n].append("{}-{}".format(numericColumn,colorKey))

            plotData[n] = {"x":filteredData}

       
        tickLabels = dict([(n,flatUniqueValues) for n in range(nNumCols)])
        axisLabels = dict([(n,{"x":"Categories","y":numericColumn}) for n,numericColumn in enumerate(numericColumns)])
        axisLimits = dict([(n,{"xLimit" : (0,offset),"yLimit":None}) for n in range(nNumCols)])
       
        groupedPlotData = pd.concat(groupedPlotData,axis=1)
    
    elif nCatCols == 0:

        axisPostions = getAxisPosition(n = 1, maxCol=maxColumns)# dict([(n,[1,1,n+1]) for n in range(1)])
        widthBox = 0.75
        tickValues = np.arange(nNumCols) #+ widthBox
        tickPositions = {0:tickValues}
        boxPositions = tickPositions.copy()
        
        colors,_ = sourceData.colorManager.createColorMapDict(numericColumns, as_hex=True)
        
        colorGroups["color"] = colors.values()
        colorGroups["group"] = colors.keys() 
        colorGroups["internalID"] = [getRandomString() for _ in colors.values()]

        faceColors = {0: list(colors.values())}
        tickLabels = {0:numericColumns}
        filteredData = [data[numericColumn].dropna() for numericColumn in numericColumns]
        groupNames = {0:numericColumns}
        plotData =   {0:{
                        "x":filteredData,
                        }}
        axisLabels = {0:{"x":"","y":"value" if len(numericColumns) > 1 else numericColumns[0]}}
        colorCategoricalColumn = "Numeric Columns"
        axisLimits[0] = {"xLimit" :  (tickValues[0]- widthBox,tickValues[-1] + widthBox), "yLimit" : None} 
        

    elif nCatCols == 1:

        axisPostions = getAxisPosition(n = 1)
        colorCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[0])
        colors,_ = sourceData.colorManager.createColorMapDict(colorCategories, as_hex=True)
        nColorCats = colorCategories.size
        colorGroups["color"] = colors.values()
        colorGroups["group"] = colorCategories
        colorGroups["internalID"] = [getRandomString() for n in colors.values()]

        filteredData = []
        tickPositions = []
        boxPositions = []
        faceColors = []
        tickLabels = []
        groupNames = []
        widthBox= 1/(nColorCats)
        singleNumericValue = len(numericColumns) == 1
        if scaleXAxis:
            try:
                numericTickPos = np.array([float(x.split(splitString)[splitIndex]) for x in colorCategories])
            except:
                scaleXAxis = False
            
        
        for m, numericColumn in enumerate(numericColumns):
            numData = data.dropna(subset=[numericColumn])
            axisGroupBy = numData.groupby(categoricalColumns[0],sort=False)
            if scaleXAxis:
                positions = numericTickPos + (m * widthBox)
                endPos = positions[-1]
            else:
                startPos = m if m == 0 else m + (widthBox/3 * m)
                endPos = startPos + widthBox * (nColorCats-1)
                positions = np.linspace(startPos,endPos,num=nColorCats)
           
            if singleNumericValue:
                tickPositions.extend(positions)
                tickLabels.extend([key for key in colorCategories])
            else:
                tickPos = np.median(positions)
                tickPositions.append(tickPos)
                tickLabels.append(numericColumn)
                
            for n,groupName in enumerate(colorCategories):
                if groupName in axisGroupBy.groups:
                    groupData = axisGroupBy.get_group(groupName)
                    
                    filteredData.append(groupData[numericColumn])
                    faceColors.append(colors[groupName])
                    boxPositions.append(positions[n])
                    groupNames.append("({}:{})::({})".format(categoricalColumns[0],groupName,numericColumn))
                    
        axisLimits[0] = {"xLimit" :  (0 - widthBox, endPos + widthBox), "yLimit" : None} 
        
        #overriding names, idiot. change!
        tickPositions = {0:tickPositions}
        boxPositions = {0:boxPositions}
        tickLabels = {0:tickLabels}
        faceColors = {0: faceColors}
        groupNames = {0:groupNames}

        plotData =   {0:{
                        "x":filteredData,
                    }}
                       # "capprops":{"linewidth":self.boxplotCapsLineWidth}}}
        axisLabels = {0:{"x":categoricalColumns[0],"y":"value" if len(numericColumns) > 1 else numericColumns[0]}}
        colorCategoricalColumn = categoricalColumns[0]
        
    
    elif nCatCols == 2:

        tickPositions = {}
        faceColors = {}
        boxPositions = {}
        axisLabels = {}
        plotData = {}
        tickLabels = {}
        groupNames = {}
        
        axisPostions = getAxisPosition(n = len(numericColumns))
        #first category splis data on x axis
        #xAxisCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[1])
       # nXAxisCats = xAxisCategories.size
        #second category is color coded
        colorCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[0])
        tickCats = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[1])
        nXAxisCats = tickCats.size

        nColorCats = colorCategories.size
        colors, _  = sourceData.colorManager.createColorMapDict(colorCategories, 
                                                    as_hex=True, 
                                                    )
        widthBox= 1/(nColorCats)
        border = widthBox / 3
        colorGroups["color"] = colors.values()
        colorGroups["group"] = colorCategories
        colorGroups["internalID"] = [getRandomString() for n in colors.values()]
        catGroupby = data.groupby(categoricalColumns, sort=False)

        for nAxis,numColumn in enumerate(numericColumns):
            filteredData = []
            catTickPositions = []
            catBoxPositions = []
            catFaceColors = []
            catTickLabels = []
            catGroupNames = []
            

            for nTickCat, tickCat in enumerate(tickCats):
                startPos = nTickCat if nTickCat == 0 else nTickCat + (border * nTickCat) #add border
                endPos = startPos + widthBox * nColorCats - widthBox
                positions = np.linspace(startPos,endPos,num=nColorCats)
                catTickPositions.append(np.median(positions))
                catTickLabels.append(tickCat)
                for nColCat, colCat in enumerate(colorCategories):
                    groupName = (colCat,tickCat)
                    if groupName not in catGroupby.groups:
                        continue 
                    groupData = catGroupby.get_group(groupName).dropna(subset=[numColumn])
                    if groupData.index.size > 0:
                        filteredData.append(groupData[numColumn])
                        catFaceColors.append(colors[colCat])
                        catBoxPositions.append(positions[nColCat])
                        catGroupNames.append("({}:{}):({}:{})::({})".format(categoricalColumns[1],tickCat,categoricalColumns[0],groupName,numColumn))

            tickPositions[nAxis] = catTickPositions
            faceColors[nAxis] = catFaceColors
            boxPositions[nAxis] = catBoxPositions 
            tickLabels[nAxis] = catTickLabels
            groupNames[nAxis] = catGroupNames
            axisLabels[nAxis] = {"x":categoricalColumns[1],"y":numColumn}
            plotData[nAxis] =  {
                            "x":filteredData,
                            }
            
            colorCategoricalColumn = categoricalColumns[0]
                            

            

    elif nCatCols == 3:

        tickPositions = {}
        faceColors = {}
        boxPositions = {}
        axisLabels = {}
        plotData = {}
        tickLabels = {}
        groupNames = {}        

        axisCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[2])
        NNumCol = len(numericColumns)

        axisPostions = getAxisPosition(n = axisCategories.size *  NNumCol, maxCol = axisCategories.size)
        #get color cats
        colorCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[0])
        tickCats = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[1])
        #axisCategories = sourceData.getUniqueValues(dataID = dataID, categoricalColumn = categoricalColumns[2])
        #nXAxisCats = tickCats.size
        colorCategoricalColumn = categoricalColumns[0]
        nColorCats = colorCategories.size
        colors, _  = sourceData.colorManager.createColorMapDict(colorCategories, 
                                                    as_hex=True, 
                                                    )
        widthBox= 1/(nColorCats)
        border = widthBox / 3
        colorGroups["color"] = colors.values()
        colorGroups["group"] = colorCategories
        colorGroups["internalID"] = [getRandomString() for n in colors.values()]
        globalMin, globalMax = np.nanquantile(data[numericColumns].values, q = [0,1])
        yMargin = np.sqrt(globalMax**2 + globalMin**2)*0.05
        catGroupby = data.groupby(categoricalColumns,sort=False)
        nAxis = -1

        for n,numColumn in enumerate(numericColumns):
                

                for nAxisCat, axisCat in enumerate(axisCategories):
                    filteredData = []
                    catTickPositions = []
                    catBoxPositions = []
                    catFaceColors = []
                    catTickLabels = []
                    catGroupNames = []
                    nAxis += 1

                    for nTickCat, tickCat in enumerate(tickCats):
                        startPos = nTickCat if nTickCat == 0 else nTickCat + (border * nTickCat) #add border
                        endPos = startPos + widthBox * nColorCats - widthBox
                        positions = np.linspace(startPos,endPos,num=nColorCats)
                        tickPos = np.median(positions)
                        catTickPositions.append(tickPos)
                        catTickLabels.append(tickCat)

                        for nColCat, colCat in enumerate(colorCategories):
                            groupName = (colCat,tickCat,axisCat)
                            if groupName not in catGroupby.groups:
                                continue

                            groupData = catGroupby.get_group(groupName).dropna(subset=[numColumn])
                            if groupData.index.size  > 0:
                                filteredData.append(groupData[numColumn])
                                catFaceColors.append(colors[colCat])
                                catBoxPositions.append(positions[nColCat])
                                catGroupNames.append("({}:{}):({}:{}):({}:{})::({})".format(categoricalColumns[1],tickCat,categoricalColumns[0],colCat,categoricalColumns[2],axisCat,numColumn))


                    if not nAxisCat in axisTitles:   
                        axisTitles[nAxisCat] = "{}:{}".format(categoricalColumns[2],axisCat)
                    tickPositions[nAxis] = catTickPositions
                    faceColors[nAxis] = catFaceColors
                    groupNames[nAxis] = catGroupNames
                    boxPositions[nAxis] = catBoxPositions 
                    tickLabels[nAxis] = catTickLabels
                    axisLabels[nAxis] = {"x":categoricalColumns[1],"y":numColumn}
                    plotData[nAxis] =  {
                                    "x":filteredData,
                                    }
                    axisLimits[nAxis] = {
                        "yLimit":(globalMin-yMargin,globalMax+yMargin),
                        "xLimit":(catBoxPositions[0] - widthBox, catBoxPositions[-1] + widthBox)
                        }
    
    
    #groupedPlotData["metric"] = groupedPlotData.index .map(lambda idx: '_'.join([str(x) for x in idx]))   
    groupedPlotData = groupedPlotData.reset_index()
    return plotData, axisPostions, boxPositions, tickPositions, \
            tickLabels, colorGroups, faceColors, colorCategoricalColumn, widthBox, axisLabels, axisLimits, axisTitles, groupNames, verticalLines, groupedPlotData


          