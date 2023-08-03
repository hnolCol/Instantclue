
from asyncore import write
import xlsxwriter
import numpy as np 
import pandas as pd

from matplotlib.colors import to_hex
from ..utils.stringOperations import getRandomString

baseNumFormat =   {'align': 'center',
                    'valign': 'vcenter',
                    'border':1}


class ICDataExcelExporter(object):
    ""
    def __init__(self,pathToExcel,data, sheetNames, softwareParams, groupings=None):
        """
        pathToExcel : 
        data : 
        """
        self.pathToExcel = pathToExcel
        self.groupings = groupings
       
        self.data = data
        self.softwareParams = softwareParams
        
        self.sheetNames = [sheetName[0:30] if len(sheetName) > 30 else sheetName for sheetName in sheetNames]
        #to do: take this to a new function
        self.sheetNames = [sheetName.replace(":","_").replace("*","_").replace("/","_").replace("?","_").replace("[","_").replace("]","_")  for sheetName in sheetNames]
        if len(self.sheetNames) != np.unique(self.sheetNames).size:
            #lazy . just create random names if the shortening leads to duplicates!
            self.sheetNames = [getRandomString(N=5) for _ in self.sheetNames]
        self.worksheets = dict() 
       

    def export(self):

        workbook = xlsxwriter.Workbook(self.pathToExcel, {'constant_memory': True, "nan_inf_to_errors":True} )
        self.headerFormat = workbook.add_format({"bg_color":"#efefef","text_wrap":True,"valign":"vcenter"})
        for sheetName in self.sheetNames:
            self.worksheets[sheetName] = workbook.add_worksheet(name=sheetName)
        self.paramWorksheet = workbook.add_worksheet(name="Software Info")
        self.addDataToWorksheet(workbook)
        self.addParams(len(self.groupings["groupings"]) if "groupings" in self.groupings else 0)
        workbook.close()
        

    def addHeader(self, workbook, worksheet, columnHeaders, writeRow, columnOffset):
        header_format = workbook.add_format({"bg_color":"#efefef","text_wrap":True,"valign":"vcenter"})
        for n,columnHeader in enumerate(columnHeaders):
            worksheet.write_string(writeRow,n+columnOffset,columnHeader,header_format)
            worksheet.freeze_panes(writeRow+1,0)

    def addDataToWorksheet(self, workbook):
        ""
        if len(self.data) == len(self.sheetNames):
            
            for n, data in enumerate(self.data):
                sheetName = self.sheetNames[n]
                writeRow, rowOffset, columnOffset = self.addGroupingToWorkSheets(self.worksheets[sheetName],workbook,data.columns.to_list())
                self.addHeader(workbook,self.worksheets[sheetName],data.columns.array,writeRow,columnOffset)
                self.addDataValues(data.columns.array, self.worksheets[sheetName],data,writeRow,columnOffset)
    
    def addDataValues(self, columnHeaders, worksheet, data, writeRow, columnOffset):
        ""
        for nRow in range(data.index.size):
            for nCol in range(data.columns.size):
                nWRow = writeRow + nRow + 1 #row to write now, +1 because of the header
                dtype = data[columnHeaders[nCol]].dtype
                if dtype == np.float64 or dtype == np.int64:
                    worksheet.write_number(nWRow,nCol+columnOffset,data[columnHeaders[nCol]].iloc[nRow])
                else:
                    worksheet.write_string(nWRow,nCol+columnOffset,str(data[columnHeaders[nCol]].iloc[nRow]))
        
        self.addFilter(worksheet,writeRow,columnOffset,nWRow,columnHeaders.size-1)
    
    def addFilter(self,worksheet,rowOffset,columnOffset,lastRow,lastColumn):
        ""
        worksheet.autofilter(rowOffset, columnOffset, lastRow, lastColumn)

    def addGroupingToWorkSheets(self,worksheet,workbook,columnHeaders):
        ""
        writeRow, rowOffset, columnOffset = 0, 0, 0
        if self.groupings is not None and isinstance(self.groupings,dict) and len(self.groupings) > 0:
            columnOffset = 1 
            rowOffset = len(self.groupings["groupings"])

            for n, (groupingName, grouping) in enumerate(self.groupings["groupings"].items()):
                worksheet.write_string(n,0,groupingName)
                for groupName, groupItems in grouping.items():
                    for groupItem in groupItems:
                        if groupItem in columnHeaders:
                            columnIndex = columnHeaders.index(groupItem) + columnOffset
                            group_format = workbook.add_format({"bg_color":"#efefef"})
                            if "colors" in self.groupings and groupingName in self.groupings["colors"] and groupName in self.groupings["colors"][groupingName]:
                                group_format.set_bg_color(self.groupings["colors"][groupingName][groupName])

                            worksheet.write_string(n,columnIndex,groupName,group_format)
                writeRow += 1
        return writeRow, rowOffset, columnOffset

    def addParams(self, numberGroupings = 0):
        ## add params
        self.paramWorksheet.write_string(0,0,"Parameters",self.headerFormat)
        self.paramWorksheet.write_string(0,1,"Value",self.headerFormat)
        
        for n, (paramName,value) in enumerate(self.softwareParams):
            self.paramWorksheet.write_string(n+1,0,paramName)
            self.paramWorksheet.write_string(n+1,1,value)

        #add grouping
        self.paramWorksheet.write_string(n+2,0,"Groupings")
        self.paramWorksheet.write_string(n+2,1,str(numberGroupings))


class ICHClustExporter(object):
    ""
    def __init__(self,
            pathToExcel,
            clusteredData,
            columnHeaders,
            colorArray,
            totalRows,
            extraData,
            clusterLabels,
            clusterColors,
            hclustParams = [],
            groupings=None,
            colorData = None,
            colorDataArray=None,
            colorColumnNames=[]):
        ""
        self.pathToExcel = pathToExcel
        self.clusteredData = clusteredData
        self.columnHeaders = columnHeaders
        self.colorArray = colorArray
        self.totalRows = totalRows
        self.extraData = extraData
        self.clusterLabels = clusterLabels
        self.clusterColors = clusterColors
        self.groupings = groupings
        self.hclustParams = hclustParams
        self.colorData = colorData 
        self.colorDataArray = colorDataArray
        self.colorColumnNames = colorColumnNames

    def export(self):

        try:
       
            self.clusteredData = self.clusteredData.iloc[::-1]
            
            self.extraData = self.extraData.iloc[::-1]
            self.columnHeaders.extend(["IC Cluster Index","IC Data Index"])
            if self.clusterLabels is not None:
                self.clusterLabels = self.clusterLabels.loc[self.clusteredData.index]
            #reshape color array to fit.
            self.colorArray = self.colorArray.reshape(self.clusteredData.index.size,-1,4)
            if self.colorDataArray is not None:
                self.colorDataArray = self.colorDataArray.reshape(self.clusteredData.index.size,-1,4)
            if self.colorData is not None:
                self.colorData = self.colorData.iloc[::-1]
               
                
            workbook = xlsxwriter.Workbook(self.pathToExcel, {'constant_memory': True, "nan_inf_to_errors":True} )
            worksheet = workbook.add_worksheet(name="data")
            paramWorksheet = workbook.add_worksheet(name="params")

            #add groupings
            if self.groupings is not None and isinstance(self.groupings,dict) and len(self.groupings) > 0 and "groupings" in self.groupings:
                if "groupings" in self.groupings:
                    columnOffset = 1 
                    rowOffset = len(self.groupings["groupings"])

                    for n, (groupingName, grouping) in enumerate(self.groupings["groupings"].items()):
                        worksheet.write_string(n,0,groupingName)
                        for groupName, groupItems in grouping.items():
                            for groupItem in groupItems:
                                if groupItem in self.columnHeaders:
                                    columnIndex = self.columnHeaders.index(groupItem) + columnOffset
                                    group_format = workbook.add_format({"bg_color":"#efefef"})
                                    if "colors" in self.groupings and groupingName in self.groupings["colors"] and groupName in self.groupings["colors"][groupingName]:
                                        group_format.set_bg_color(self.groupings["colors"][groupingName][groupName])

                                    worksheet.write_string(n,columnIndex,groupName,group_format)

            else:
                columnOffset = 0
                rowOffset = 0 


            #start with headers
            writeRow = 0  + rowOffset
            header_format = workbook.add_format({"bg_color":"#efefef","text_wrap":True,"valign":"vcenter"})
            for n,columnHeader in enumerate(self.columnHeaders):
                worksheet.write_string(writeRow,n+columnOffset,columnHeader,header_format)
            worksheet.freeze_panes(writeRow+1,0)


            for nRow in range(self.totalRows):
                for nCol in range(len(self.columnHeaders)):
                    nWRow = writeRow + nRow + 1
                    if self.columnHeaders[nCol] == "Cluster ID" and self.clusterLabels is not None:
                        #find cluster ID format
                        clustID = self.clusterLabels.iloc[nRow].values[0]
                        formatDict = baseNumFormat.copy()
                        formatDict["bg_color"] = self.clusterColors[clustID] 
                        cell_format = workbook.add_format(formatDict)
                        worksheet.write_string(nWRow,nCol+columnOffset,clustID,cell_format)

                    elif nCol < self.clusteredData.columns.size + 1:#include all columns (first one is alsoway "Cluster ID") 
                        c = self.colorArray[self.totalRows-nRow-1,nCol - 1].tolist()
                        formatDict = baseNumFormat.copy()
                        formatDict["bg_color"] = to_hex(c)
                        cell_format = workbook.add_format(formatDict)
                        worksheet.write_number(nWRow ,nCol+columnOffset,self.clusteredData.iloc[nRow,nCol - 1], cell_format) #-1 to account for first Cluster ID column
                    elif nCol < self.clusteredData.columns.size + 1 + len(self.colorColumnNames) and self.colorData is not None and self.columnHeaders[nCol] in self.colorColumnNames:
                       
                        colIdx = nCol - 1- self.clusteredData.columns.size
                        
                        c = self.colorDataArray[self.totalRows-nRow-1,colIdx].tolist()
                        
                        formatDict = baseNumFormat.copy()
                        formatDict["bg_color"] = to_hex(c)
                        cell_format = workbook.add_format(formatDict)
                        worksheet.write_number(nWRow ,nCol+columnOffset,self.colorData.iloc[nRow,colIdx], cell_format) 
                        
                    elif self.columnHeaders[nCol] == "IC Data Index":
                        worksheet.write_number(nWRow,nCol+columnOffset, self.clusteredData.index.values[nRow])
                    elif self.columnHeaders[nCol] == "IC Cluster Index":
                        worksheet.write_number(nWRow,nCol+columnOffset,nRow)
                    elif self.columnHeaders[nCol] == "QuickSelect":
                        colorValue = self.extraData[self.columnHeaders[nCol]].iloc[nRow]
                        
                        if colorValue != "":
                            worksheet.write_string(nWRow,nCol+columnOffset,"+",workbook.add_format({"bg_color":colorValue}))

                    else:
                        dtype = self.extraData[self.columnHeaders[nCol]].dtype
                        if dtype == np.float64 or dtype == np.int64:
                            worksheet.write_number(nWRow,nCol+columnOffset,self.extraData[self.columnHeaders[nCol]].iloc[nRow])
                        else:
                            worksheet.write_string(nWRow,nCol+columnOffset,str(self.extraData[self.columnHeaders[nCol]].iloc[nRow]))

            
            ## add params
            paramWorksheet.write_string(0,0,"Parameters",header_format)
            
            for n, (paramName,value) in enumerate(self.hclustParams):
                paramWorksheet.write_string(n+1,0,paramName)
                paramWorksheet.write_string(n+1,1,value)


            workbook.close()
        except Exception as e:
            print(e)
                    


        #totalRows = int(colorArray.shape[0]/len(self.numericColumns))
        #write data row by row (needed due to "constant_memory" : True)



# 		totalRows = int(colorArray.shape[0]/len(self.numericColumns))









# pathSave = tf.asksaveasfilename(initialdir=path_file,
#                                         title="Choose File",
#                                         filetypes = (("Excel files","*.xlsx"),),
#                                         defaultextension = '.xlsx',
#                                         initialfile='hClust_export')
# 		if pathSave == '' or pathSave is None:
# 			return
       
# 		selectableColumns = self.dfClass.get_columns_of_df_by_id(self.dataID)
# 		columnsNotUsed = [col for col in selectableColumns if col not in self.df.columns]
# 		selection = []
# 		if len(columnsNotUsed) != 0:
# 			dialog = simpleListboxSelection('Select column to add from the source file',
#          		data = columnsNotUsed)   		
# 			selection = dialog.selection
		
# 		workbook = xlsxwriter.Workbook(pathSave)
# 		worksheet = workbook.add_worksheet()
# 		nColor = 0
# 		currColumn = 0
# 		colorSave = {}
# 		clustRow = 0
		
# 		progBar = Progressbar(title='Excel export')
		
# 		colorsCluster = sns.color_palette(self.cmapRowDendrogram,self.uniqueCluster.size)[::-1]
# 		countClust_r = self.countsClust[::-1]
# 		uniqueClust_r = self.uniqueCluster[::-1]
# 		progBar.update_progressbar_and_label(10,'Writing clusters ..')
# 		for clustId, clustSize in enumerate(countClust_r):
# 			for n in range(clustSize):
# 				cell_format = workbook.add_format() 
# 				cell_format.set_bg_color(col_c(colorsCluster[clustId]))
# 				worksheet.write_string(clustRow + 1,
# 					0,'Cluster_{}'.format(uniqueClust_r[clustId]), 
# 					cell_format)
# 				clustRow += 1
		
# 		progBar.update_progressbar_and_label(20,'Writing column headers ..')
		
# 		for n ,colHead in enumerate(['Clust_#'] +\
# 			 self.numericColumns + self.colorData.columns.tolist()  + \
# 			 ['Cluster Index','Data Index'] +\
# 			 self.labelColumnList + selection):
			 
# 			worksheet.write_string(0, n, colHead)		 
		
# 		colorArray = self.colorMesh.get_facecolors()#np.flip(,axis=0)	
# 		totalRows = int(colorArray.shape[0]/len(self.numericColumns))
# 		progBar.update_progressbar_and_label(22,'Writing cluster map data ..')

# 		for nRow in range(totalRows):
# 			for nCol in range(len(self.numericColumns)):
# 				c = colorArray[nColor].tolist()
# 				if str(c) not in colorSave:
# 					colorSave[str(c)] = col_c(c)
# 				cell_format = workbook.add_format({'align': 'center',
#                                      			   'valign': 'vcenter',
#                                      			   'border':1,
#                                      			   'bg_color':colorSave[str(c)]}) 
# 				worksheet.write_number(totalRows - nRow ,nCol + 1,self.df.iloc[nRow,nCol], cell_format)
# 				nColor += 1
				
# 		worksheet.set_column(1,len(self.numericColumns),3)
# 		worksheet.freeze_panes(1, 0)
# 		progBar.update_progressbar_and_label(37,'Writing color data ..')

# 		if len(self.colorData.columns) != 0:
# 			currColumn = nCol + 1
# 			colorFac_r = dict((v,k) for k,v in self.factorDict.items())
# 			colorArray = self.colorDataMesh.get_facecolors()
# 			nColor = 0		
# 			totalRows = int(colorArray.shape[0]/len(self.colorData.columns))	
# 			for nRow in range(totalRows):
# 				for nCol in range(len(self.colorData.columns)):
# 					c = colorArray[nColor].tolist()
# 					if str(c) not in colorSave:
# 						colorSave[str(c)] = col_c(c)
						
# 					cellInt = self.colorData.iloc[nRow,nCol]
# 					cellStr = str(colorFac_r[cellInt])
					
# 					cell_format = workbook.add_format({
#                                      			   'border':1,
#                                      			   'bg_color':colorSave[str(c)]}) 
                                     			   
# 					worksheet.write_string(totalRows - nRow, nCol + 1 + currColumn , cellStr, cell_format)
# 					nColor += 1
					
# 		currColumn = nCol + 1 + currColumn	
						
# 		for n,idx in enumerate(np.flip(self.df.index,axis=0)):
# 			worksheet.write_number(n+1,currColumn+1,n+1)
# 			worksheet.write_number(n+1,currColumn+2,idx + 1)	
			
# 		progBar.update_progressbar_and_label(66,'Writing label data ..')
# 		if len(self.labelColumnList) != 0:
# 			for nRow, labelStr in enumerate(self.labelColumn):
# 				worksheet.write_string(totalRows-nRow,currColumn+3,str(labelStr))
			
# 		progBar.update_progressbar_and_label(77,'Writing additional data ..')
		
# 		df = self.dfClass.join_missing_columns_to_other_df(self.df, self.dataID, definedColumnsList = selection) 
# 		df = df[selection]
# 		dataTypes = dict([(col,df[col].dtype) for col in selection])
# 		if len(selection) != 0:
# 			for nRow in range(totalRows):
# 				data = df.iloc[nRow,:].values
# 				for nCol in range(len(selection)):
# 					cellContent = data[nCol]
# 					if dataTypes[selection[nCol]] == 'object':
# 						worksheet.write_string(totalRows-nRow, currColumn+3+nCol,str(cellContent))
# 					else:
# 						try:
# 							worksheet.write_number(totalRows-nRow, currColumn+3+nCol,cellContent)
# 						except:
# 							#ignoring nans
# 							pass

# 		workbook.close()
# 		progBar.update_progressbar_and_label(100,'Done..')
# 		progBar.close()
	