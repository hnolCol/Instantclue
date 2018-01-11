import string 
import os
import sys
	
import tkinter as tk
from tkinter import ttk             
import tkinter.simpledialog as ts
import matplotlib.pyplot as plt
import tkinter.filedialog as tf
from modules import images
from modules.utils import * 
from modules.dialogs import VerticalScrolledFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from modules.dialogs import text_editor
from modules.dialogs import artist_editor
from modules.dialogs import simple_dialog

alphabeticLabel  = list(string.ascii_lowercase)+list(string.ascii_uppercase)
rangePositioning = list(range(1,20))

labelsAndGridInfo = dict(
								positionRow = ['Position (row,column):',dict(row=5,column=0, sticky=tk.E, columnspan=2,pady=3),
											dict(row=5, column = 2, sticky=tk.W,pady=3,padx=1)],
								positionColumn = ['','',dict(row=5, column = 3, sticky=tk.W,pady=3,padx=1)],
								columnSpan = ['Column span:',dict(row=5,column = 6, sticky=tk.W,pady=3),
											dict(row=5,column = 7, sticky=tk.W,pady=3) ], 
								rowSpan = ['Row span:',dict(row=5,column = 4, sticky=tk.E,pady=2),
											dict(row=5,column = 5, sticky=tk.W,pady=3)], 
								gridRow = ['Rows:',dict(row=2, column = 0,columnspan=2, sticky =tk.E,pady=3),
											dict(row=2, column = 2, sticky=tk.W,pady=3)],
								gridColumn = ['Columns:',dict(row=2, column =4, sticky=tk.W,pady=3),
												dict(row=2, column = 5, sticky=tk.W,pady=3)],
								subplotLabel = ['Subplot label:', dict(row=5,column =8, sticky=tk.W,pady=3),
												dict(row=5,column =9, sticky=tk.W,pady=3) ])



class mainFigureCollection(object):	
	
	def __init__(self,analyzeClass =None):
		self.mainFigureId = 0
		
		self.mainFigureTemplates = OrderedDict()
		self.mainFigures = {}
		self.exportDetails = {}
		self.figText = {}
				
		self.analyze = analyzeClass
		self.default_label_settings()

	
	def initiate(self, figureId = None):
		'''
		'''
		if figureId is None:
			self.mainFigureId += 1
			self.exportDetails[self.mainFigureId] = {}
			self.figText[self.mainFigureId] = {}
		else:
			## this happens when 
			self.mainFigureId = figureId
			
			
		self.mainFigureTemplates[self.mainFigureId] = {}
		self.mainFigures[self.mainFigureId] = {}
		
		
		return self.mainFigureId

	def store_export(self,axisId,figureId,plotCount,subplotNum,exportId,boxBool,gridBool):
		'''
		'''
		limits = self.get_limits(axisId,figureId)
		
		self.exportDetails[figureId][axisId] = {'plotCount':plotCount,
												'subplotNum':subplotNum,
												'limits':limits,
												'exportId':exportId,
												'boxBool':boxBool,
												'gridBool':gridBool}
	def store_image_export(self,axisId,figureId,imagePath):
		'''
		'''
		self.exportDetails[figureId][axisId] = {'path':imagePath}	
						
	def store_figure(self,figure,templateClass):
		'''
		Store in different dict, since we cannot pickle the 
		figure in a tk canvas.
		'''
		self.mainFigures[self.mainFigureId]['figure'] = figure
		self.mainFigures[self.mainFigureId]['template'] = templateClass
	
	
	def store_figure_text(self,figureId,id,props):
		'''
		Stores figure text added by the user. To enable session upload.
		'''
		self.figText[figureId][id] = props
		
	
	def get_limits(self,axisId,figureId):
		'''
		'''
		ax = self.mainFigureTemplates[figureId][axisId]['ax']
		xLim = ax.get_xlim()
		yLim = ax.get_ylim()
		return [xLim,yLim]
			
	def update_params(self, figureId, axisId = None, params = None, how = 'add'):
		'''
		'''
		if how == 'add':
			self.mainFigureTemplates[figureId][axisId] = params
			self.update_menu(params['ax'],axisId,figureId,params['axisLabel'])
			
		elif how == 'delete':
			params =  self.mainFigureTemplates[figureId][axisId]
			self.analyze.main_figure_menu.delete('Figure {} - Subplot {}'.format(figureId,params['axisLabel']))
			del self.mainFigureTemplates[figureId][axisId]
			if axisId in self.exportDetails[figureId]:
				del self.exportDetails[figureId][axisId]
		
		elif how == 'clear':
			params =  self.mainFigureTemplates[figureId][axisId]
			if axisId in self.exportDetails[figureId]:
				del self.exportDetails[figureId][axisId]		
		
		elif how == 'clean_up':			
			for axisId,params in self.mainFigureTemplates[figureId].items():
				self.analyze.main_figure_menu.delete('Figure {} - Subplot {}'.format(figureId,params['axisLabel']))
			self.mainFigureTemplates[figureId] = {}
			self.exportDetails[figureId] = {}
		
		elif how == 'destroy':			
			for axisId,params in self.mainFigureTemplates[figureId].items():
				self.analyze.main_figure_menu.delete('Figure {} - Subplot {}'.format(figureId,params['axisLabel']))
			del self.mainFigureTemplates[figureId]
			del self.exportDetails[figureId]

	def update_menu_label(self,old,new):
		'''
		Updates the menu if user re-labels.
		'''
		self.analyze.main_figure_menu.entryconfigure(old,label=new)						
								
	def update_menu(self,ax,axisId,figureId,label):
		'''
		'''
		self.analyze.main_figure_menu.add_command(label='Figure {} - Subplot {}'.format(figureId,label), 
			command = lambda ax = ax:self.analyze.perform_export(ax,axisId,self.mainFigures[figureId]))
	
	def default_label_settings(self):
		'''
		'''
		self.subplotLabelStyle = {'xy':(0.0,1),'xytext':(-12,12),
						'xycoords':('axes fraction'),'textcoords':'offset points',
						'size':12, 'family':'Verdana','ha':'left',
						'weight':'bold','color':'black','va':'bottom',
						'rotation':'0'}
		
	def __getstate__(self):
		'''
		Cant pickle menu since it is a tkinter menu object.
		We need to remove it before pickle
		'''
		for figureId, axisDict in self.mainFigureTemplates.items():
			for axisId, params in axisDict.items():
				if 'ax' in params: # if user saves session twice this will be gone already
					del params['ax']
		state = self.__dict__.copy()
		for attr in ['analyze','mainFigures']:
			if attr in state: 
				del state[attr]
		return state	


class mainFigureTemplateDialog(object):
	'''
	Class that manages main figures.
	We have decided to split this from the actual creation to achieve easier opening from saved session. 
	'''
	def __init__(self, mainFigureCollection, figureId = None):
		## defining StringVars for grid layout and positioning of axis

		self.define_variables()
		
		self.mainFigureCollection = mainFigureCollection
		self.figureId = self.mainFigureCollection.initiate(figureId)
		
		self.axisId = 0
		self.figureProps = OrderedDict()
								
		self.load_images()	
		self.build_toplevel()
		self.create_frame()
		self.create_widgets()
		self.define_menu()
		self.mainFigureCollection.store_figure(self.figure,self)
		
	def define_variables(self):
				 
		self.main_fig_add_text = None
		self.delete_axis_event = None
		self.motionLabel = None
		self.textsAdded = {}
		self.axisLabels = {}
		self.axisItems = {}
		self.associatedAxes = {}
		
		
				
		self.positionColumn = tk.StringVar(value='1') 
		self.positionRow = tk.StringVar(value='1') 
		self.columnSpan = tk.StringVar(value='1') 
		self.rowSpan = tk.StringVar(value='1') 	
		self.gridColumn = tk.StringVar(value='3') 
		self.gridRow = tk.StringVar(value='4') 
		self.subplotLabel = tk.StringVar(value='a')	
		self.infolabel = tk.StringVar(value = 'Add subplots to build main figure') 
				
		self.positionGridDict = OrderedDict(positionColumn = self.positionColumn,positionRow = self.positionRow,
								columnSpan = self.columnSpan, rowSpan = self.rowSpan, gridRow = self.gridRow,
								gridColumn = self.gridColumn, subplotLabel = self.subplotLabel)			
	def close(self):
		'''
		closing the toplevel
		'''
		quest = tk.messagebox.askquestion('Confirm ..',
			'Closing main figure template window. Proceed?',
			parent = self.toplevel)
			
		if quest == 'yes':	
			self.mainFigureCollection.update_params(self.figureId,how='destroy')	
			self.toplevel.destroy() 
		
		
	def build_toplevel(self):
	
		'''
		Builds the toplevel to put widgets in 
		'''
        
		popup = tk.Toplevel(bg=MAC_GREY) 
		popup.wm_title('Setup main figure ...') 
         
		popup.protocol("WM_DELETE_WINDOW", self.close)
		
		w = 845
		h = 840
             
		self.toplevel = popup
		self.center_popup((w,h))
		
	def create_frame(self):
		
		'''
		Creates frame to put widgets in
		'''
		self.cont = tk.Frame(self.toplevel,bg=MAC_GREY)
		self.cont.pack(fill='both', expand=True)
		self.cont.grid_columnconfigure(9, weight = 1)
		self.cont.grid_rowconfigure(10, weight=1)
			
	def create_widgets(self):
		'''
		Creates all widgets
		'''
		labelGridSetup = tk.Label(self.cont, text='Define grid layout for main figure',**titleLabelProperties)
		labelAxisSetup = tk.Label(self.cont, text='Add subplot to figure',**titleLabelProperties)
		labelInfoLab = tk.Label(self.cont, textvariable = self.infolabel,**titleLabelProperties)
		labelFigIdLabel = tk.Label(self.cont, text = 'Figure {}'.format(self.figureId),**titleLabelProperties)
		
		
		labelGridSetup.grid(row=1, column = 0, sticky=tk.W, columnspan=6, padx=3,pady=5)       
		for id,variable in labelsAndGridInfo.items():
			
			labelText = variable[0]
			if labelText == 'Position (row,column):':
			
				labelFigIdLabel.grid(row=2,column = 7, sticky = tk.E, columnspan=14, padx=30)
				ttk.Separator(self.cont, orient = tk.HORIZONTAL).grid(sticky=tk.EW, columnspan=15,pady=4, row=3)  
				labelAxisSetup.grid(row=4, column = 0, sticky=tk.W, columnspan=15,padx=3,pady=5)
				
			if labelText != '':
				labCombobox = tk.Label(self.cont, text = labelText, bg=MAC_GREY)
				labCombobox.grid(**variable[1])
			if labelText != 'Subplot label:':
				valuesCombo = rangePositioning 
			else:
				valuesCombo = alphabeticLabel

			combobox = ttk.Combobox(self.cont, textvariable = self.positionGridDict[id], values = valuesCombo, width=5) 
			combobox.grid(**variable[2])
			
		ttk.Separator(self.cont, orient = tk.HORIZONTAL).grid(sticky=tk.EW, columnspan=15,pady=4)
		buttonFrame = tk.Frame(self.cont,bg=MAC_GREY)
		buttonFrame.grid(row=7,column=0,columnspan=8,sticky=tk.W)
		## crate and grid main buttons  on MAC ttk Buttons with images are buggy in width
		but_add_axis  = create_button(buttonFrame, image = self.add_axis_img, command = self.add_axis_to_figure)
		but_add_text = create_button(buttonFrame, image = self.add_text_img, command = self.add_text)	
		but_add_image = create_button(buttonFrame, image =  self.add_image, command = self.add_image_to_axis)
		self.but_delete_ax = create_button(buttonFrame, image = self.delete_axis_img, command = self.delete_axis)
		but_clear = create_button(buttonFrame, image = self.clean_up_img, command = self.clean_up_figure)
		
			
		btns= [but_add_axis,but_add_text,but_add_image,self.but_delete_ax,but_clear]
		
		for n,btn in enumerate(btns):
			if n == 0:
				padx_ = (8,4)
			else:
				padx_ = 4
			btn.grid(row=7,column=n, padx=padx_,pady=2)
		
		labelInfoLab.grid(row=7,column=n+1, padx=4,pady=2,columnspan=30,sticky=tk.W)
		vertFrame = VerticalScrolledFrame.VerticalScrolledFrame(self.cont)
		vertFrame.grid(row=10,columnspan=20, sticky=tk.NSEW)
		figureFrame = tk.Frame(vertFrame.interior) ##scrlollable
		toolbarFrame = tk.Frame(self.cont,bg=MAC_GREY)
		
		figureFrame.grid(columnspan=20) 
		toolbarFrame.grid(columnspan=16, sticky=tk.W)#+tk.EW)
		self.display_figure(figureFrame,toolbarFrame)
		self.figure.canvas.mpl_connect('button_press_event', self.edit_items_in_figure)
		
            	
	def load_images(self):
		
		self.add_axis_img, self.add_text_img,self.add_image,\
		self.delete_axis_img,self.clean_up_img,self.delete_axis_active_img  = images.get_main_figure_images()      
        
        
	def display_figure(self, frameFigure,toolbarFrame):
	
		self.figure = plt.figure(figsize=(8.27,11.7))      
		self.figure.subplots_adjust(top=0.94, bottom=0.05,left=0.1,
									right=0.95, wspace = 0.32, hspace=0.32)
		canvas  = FigureCanvasTkAgg(self.figure,frameFigure)
		canvas.show() 
		self.toolbar_main = NavigationToolbar2TkAgg(canvas, toolbarFrame)
		canvas._tkcanvas.pack(in_=frameFigure,side="top",fill='both',expand=True)
		canvas.get_tk_widget().pack(in_=frameFigure,side="top",fill='both',expand=True)
		

	
	def add_axis_label(self,ax, axisId, label = None):
		'''
		Adds a subplot label to the created/updated subplot
		'''
		if label is None:
			text = self.subplotLabel.get()
		else:
			text = label
			
		axesLabel = ax.annotate(text,**self.mainFigureCollection.subplotLabelStyle)
		self.axisLabels[axisId] = axesLabel
		
	
	def edit_items_in_figure(self,event):
		'''
		'''

		if event.dblclick:
					
			for id,label in self.textsAdded.items():
				if label.contains(event)[0]:
					editedStyle = self.modify_text_items(label)
					if editedStyle is not None:	
						editedStyle['x'], editedStyle['y'] = label.get_position()
						self.mainFigureCollection.store_figure_text(self.figureId,id,editedStyle)
					
			if event.inaxes is None:
				for id, subplotLabel in self.axisLabels.items():
					if subplotLabel.contains(event)[0]:
						editedStyle = self.modify_text_items(subplotLabel,
										type = 'subplot labels', axisId =id,
										extraCb = {'global':['Modify all subplots labels',True],
												   'variant':['Transfer variant changes (upper ..)',True]})
						
									
			if event.inaxes:
				typesToCheck = ['collections','patches','annotations',
								'lines','artists']
				mustBeText = False
			elif event.inaxes is None:
				typesToCheck = ['x-ticks','y-ticks','axis labels','titles',
								'legend texts','legend caption']
				mustBeText = True
			for axisId, artists in self.axisItems.items():
				for type, items in artists.items():
					if type in typesToCheck:
						for item in items:
							if hasattr(item,'contains'):
								if item.contains(event)[0]:
									if mustBeText or type == 'annotations':
										self.modify_text_items(item,type,axisId)
									else:
										self.handle_artist_modification(axisId,type,item,items)	
		else:
			toDelete = None
			for id,label in self.textsAdded.items():
				if label.contains(event)[0]:
					if event.button == 1:
						self.onMotionEvent = \
						self.figure.canvas.mpl_connect('motion_notify_event', lambda event, setLabel=label:\
						self.on_motion_with_label(event,setLabel))
						self.onReleaseEvent = self.figure.canvas.mpl_connect('button_release_event',\
						lambda event, id = id : self.on_release(event,id))			
					else:
						label.remove()
						del self.mainFigureCollection.figText[self.figureId][id]
						toDelete = id
			if toDelete is not None:
				del self.textsAdded[toDelete]
			
			elif event.button == 3 and event.inaxes:	
				self.event = event				
				idClicked = self.identify_id_of_axis(self.event.inaxes)
				self.menu.entryconfigure(2, 
					label = 'Selected : {}'.format(self.figureProps[idClicked]['axisLabel']))
				self.cast_menu()
				
						
		self.redraw()	
	
	
	def cast_menu(self):
		'''
		'''
		x = self.toplevel.winfo_pointerx()
		y = self.toplevel.winfo_pointery()
		self.menu.post(x,y)
	

	def define_menu(self):
		'''
		'''
		self.menu = tk.Menu(self.toplevel, **styleDict)
		
		self.menu.add_command(label='Transfer to ..', 
			state=tk.DISABLED, foreground='darkgrey')
		self.menu.add_separator()	
		self.menu.add_command(label='Selected: ',state=tk.DISABLED,foreground = 'darkgrey')
		self.menu.add_separator()	
		self.menu.insert_command(index=30,label = 'Clear subplot', 
			command = self.clear_axis_from_menu,foreground="red")
	
	
		
	def modify_text_items(self, item, type = None, axisId = None, extraCb = None):
		'''
		Modify text item(s). The text editor can be used to apply the 
		properties to global and to axis items of the same type.
		'''
		textProps = self.extract_text_props(item)
		
		if type is not None and extraCb is None:
			extraCb = OrderedDict([('global',['Modify all {}'.format(type),False]),
				   ('axis',['Modify {} in subplot'.format(type),True])])
		if extraCb is not None:
			textProps['extraCB'] = extraCb
				
		edit = text_editor.textEditorDialog(**textProps)
		editedStyle,extraCbState = edit.get_results()
		
		
		if editedStyle is not None:
			
			if  type == 'subplot labels' and \
			self.figureProps[axisId]['axisLabel'] != editedStyle['s']:
			
			
			
				old = 'Figure {} - Subplot {}'.format(self.figureId,
								self.figureProps[axisId]['axisLabel'])
								
				new = 'Figure {} - Subplot {}'.format(self.figureId,
										editedStyle['s'])
				self.menu.entryconfigure('Subplot - %s' % self.figureProps[axisId]['axisLabel'],
					label = 'Subplot - %s' % editedStyle['s'])
				self.mainFigureCollection.update_menu_label(old,new)
				
			item.set(**editedStyle['fontdict'])
			item.set_text(editedStyle['s'])

			if type == 'subplot labels':
				self.figureProps[axisId]['axisLabel'] = editedStyle['s']
				variant = edit.get_variant()
				if variant != 'None' and extraCbState['variant']:
					for axisIdSub,axisProps in self.figureProps.items():
						for key,label in axisProps.items():
							if key == 'axisLabel' and axisIdSub != axisId:
								newLabel = edit.check_variant(label)
								old = 'Figure {} - Subplot {}'.format(self.figureId,
								self.figureProps[axisIdSub]['axisLabel'])
								new = 'Figure {} - Subplot {}'.format(self.figureId,
										newLabel)
								self.menu.entryconfigure('Subplot - %s' % self.figureProps[axisIdSub]['axisLabel'],
										label = 'Subplot - %s' % newLabel)
								
								self.mainFigureCollection.update_menu_label(old,new)
								self.axisLabels[axisIdSub].set_text(newLabel)
								self.figureProps[axisIdSub]['axisLabel'] = newLabel
					self.get_next_subplot_label(newLabel)
								
			
			how = 'single'
			if 'global' in extraCbState:
				if extraCbState['global']:
					how = 'global'
			if 'axis' in extraCbState and how != 'global':
				if extraCbState['axis']:
					how = 'axis'
			if how != 'single':
				self.modify_multiple_items(how,editedStyle,axisId = axisId,type=type)
			
			if type == 'x-ticks':
				xticks = self.figureProps[axisId]['ax'].get_xticklabels()
				self.figureProps[axisId]['ax'].set_xticklabels(xticks)
			elif type == 'y-ticks':
				yticks = self.figureProps[axisId]['ax'].get_yticklabels()
				self.figureProps[axisId]['ax'].set_yticklabels(yticks)
			return editedStyle

	def modify_multiple_items(self,how,editedStyle,axisId = None,type = 'subplot labels'):
		'''
		how - can be - 'global' or 'axis'
		'''
		if type == 'subplot labels':
			toModify = self.axisLabels
			for prop,value in editedStyle['fontdict'].items():
				self.mainFigureCollection.subplotLabelStyle[prop] = value
		
		else:
			if how == 'axis':
				toModify = self.axisItems[axisId][type]
			elif how == 'global':
				toModify = []
				for axisId,artists in self.axisItems.items():
					for textType,texts in artists.items():
						if textType == type:
							toModify.extend(texts)
							
		if isinstance(toModify,dict):
			for id,item in toModify.items():
				item.set(**editedStyle['fontdict'])
				
		elif isinstance(toModify,list):
			for item in toModify:
				item.set(**editedStyle['fontdict'])
		
	def extract_text_props(self, text):
		'''
		'''
		props = {'size':text.get_size(),
				 'font':text.get_fontname(),
				 'weight':text.get_weight(),
				 'style':text.get_style(),
				 'ha':text.get_ha(),
				 'color':col_c(text.get_color()),
				 'rotation':str(text.get_rotation())}
		
		style = {'inputText':text.get_text(),
				'props':props}
				
		return style  	

	
	def handle_artist_modification(self,axisId,type,item,itemList):
		'''
		Opens dialog to alter some settings of artists.
		'''
		artist_editor.artistEditorDialog(type,item,
			itemList,axis=self.figureProps[axisId]['ax'])
		
	
		
	def add_axis_to_figure(self, axisParams = None, axisId = None,
										redraw = True, addToId = True):
		'''
		Adss an axis to the figure . Gets the settings from the dictionary that stores self.positionGridDict
		'''
		if axisParams is None:
			axisParams =  self.get_axis_parameters()
		gridRow, gridCol,posRow, posCol,rowSpan, colSpan, subplotLabel = axisParams
		
		if posRow-1 + rowSpan > gridRow or posCol -1 + colSpan > gridCol:
			tk.messagebox.showinfo('Invalid input ..',
					'Axis specification out of grid.',
					parent = self.toplevel)
			return 	
		
		grid_spec = plt.GridSpec(gridRow,gridCol) 
		subplotspec = grid_spec.new_subplotspec(loc=(posRow-1,posCol-1),
												rowspan=rowSpan,colspan=colSpan)
										
		ax = self.figure.add_subplot(subplotspec)
		self.save_axis_props(ax,axisParams,addToId = addToId)
		
		if addToId:
			axisId = self.axisId
			self.add_axis_label(ax, axisId)
		else:
			self.add_axis_label(ax, axisId, 
								label = self.figureProps[axisId]['axisLabel'])
		
		
		if redraw:							
			self.redraw()
			self.update_axis_parameters(axisParams)	
			self.infolabel.set('Axis added!')									
												
        
	
	def get_axis_parameters(self):
		'''
		Returns axis and grid parameters
		'''
		gridRow, gridCol = self.positionGridDict['gridRow'].get(), self.positionGridDict['gridColumn'].get()		
		posRow , posCol = self.positionGridDict['positionRow'].get(), self.positionGridDict['positionColumn'].get()	
		rowSpan, colSpan = self.positionGridDict['rowSpan'].get(), self.positionGridDict['columnSpan'].get()
		
		propsStrings = [gridRow, gridCol,posRow, posCol,rowSpan, colSpan]
		propsIntegers = [int(float(item)) for item in propsStrings]
		
		subplotLabel = self.positionGridDict['subplotLabel'].get()
		propsIntegers.append(subplotLabel) 
		
		return propsIntegers
	
	
	
	def get_next_subplot_label(self,subplotLabel):
		'''
		'''
		if subplotLabel in alphabeticLabel:
		
			idxLabel = 	alphabeticLabel.index(subplotLabel)
			nextLabelIdx = idxLabel+1
			if nextLabelIdx == len(alphabeticLabel):
				nextLabelIdx = 0
			
			nextLabel = alphabeticLabel[nextLabelIdx]
			self.positionGridDict['subplotLabel'].set(nextLabel)
		

	def update_axis_parameters(self, parametersList = None):
		'''
		Updates the comboboxes to provide convenient addition of mroe axes.
		'''	
		if parametersList is None:
			gridRow, gridCol,posRow, posCol,rowSpan, colSpan, subplotLabel  = self.get_axis_parameters() 
		else:
			gridRow, gridCol,posRow, posCol,rowSpan, colSpan, subplotLabel = parametersList 
		## updating 
		
		self.get_next_subplot_label(subplotLabel)	

		# reset position in Grid..
		if posCol + colSpan > gridCol:
			posCol = 1
			posRow = posRow + rowSpan 
		else:
			posCol = posCol + colSpan
		
		self.positionGridDict['positionRow'].set(str(posRow))
		self.positionGridDict['positionColumn'].set(str(posCol))

	def check_if_axes_created(self):
		'''
		'''
		if len(self.figure.axes) == 0:
			tk.messagebox.showinfo('Create axis ..','Please create a subplot.', 
													parent = self.toplevel)
			return False
		else:
			return True

	def align_image_in_axis(self,ax, axOriginalPos):
		'''
		'''
		
		axCurrentPos = ax.get_position()
		
		if axCurrentPos.y1-axCurrentPos.y0 < axOriginalPos.y0:
			newYPos = axOriginalPos.y1-(axCurrentPos.y1-axCurrentPos.y0)
		else:	
			newYpos = axOriginalPos.y0
		#x,y,width,height
		newAxPosition = [axOriginalPos.x0,newYPos,
						(axCurrentPos.x1-axCurrentPos.x0),
						(axCurrentPos.y1-axCurrentPos.y0)]
		ax.set_position(newAxPosition)

	
	def add_text(self):
		'''
		Adds user defined text
		'''
		txtEditor = text_editor.textEditorDialog()
		self.textDict, _  = txtEditor.get_results()
		del txtEditor
		# reset focus to figure toplevel 
		self.toplevel.focus_force()
		self.infolabel.set('Click to place text in figure.')
		if self.textDict is not None:
			self.on_motion_event = self.figure.canvas.mpl_connect('motion_notify_event', self.on_motion_with_label)
			self.on_click_event = self.figure.canvas.mpl_connect('button_press_event', self.on_click)

	def on_motion_with_label(self,event,setLabel = None):
		'''
		motion_notify_event handler. Moves text item on figure (maybe 
		a trick to use blit would be better? - Done
		'''
		x,y = self.figure.transFigure.inverted().transform((event.x,event.y)).tolist()
		if self.motionLabel is None:
			# trick to hide label when using blit
			# otherwise would exists in two version(e.g one from background)
			if setLabel is not None:
				setLabel.set_visible(False)
				self.redraw()
			self.background = self.figure.canvas.copy_from_bbox(self.figure.bbox)
			
			if setLabel is None:
				self.motionLabel = self.figure.text(x,y,**self.textDict)
			else:
				setLabel.set_visible(True)
				self.motionLabel = setLabel
				self.infolabel.set('Release mouse button to set new position.')
		else:
			self.figure.canvas.restore_region(self.background)
			self.motionLabel.set_position((x,y))
			self.motionLabel.draw(self.figure.canvas.get_renderer())
			self.figure.canvas.blit(self.figure.bbox)
						
				
	def on_release(self,event,id):
		'''
		Figure text can be moved around. Release cancels this and stores the 
		new position and the old style (is restored from the figText Collection)
		Parameter
		===========
		event - matplotlib button_release_event
		id	  - id that was given to the text when created
		'''
		self.figure.canvas.mpl_disconnect(self.onMotionEvent)
		self.figure.canvas.mpl_disconnect(self.onReleaseEvent)
		if self.motionLabel is not None:
			self.textDict = self.mainFigureCollection.figText[self.figureId][id]		
			self.textDict['x'], self.textDict['y'] = self.motionLabel.get_position()
			self.mainFigureCollection.store_figure_text(self.figureId,id,self.textDict)
					
		self.motionLabel = None		
		self.redraw()	
		self.infolabel.set('Text moved and stored.')			
	
	def on_click(self,event):
		'''
		Handles on click events when motion is enabled 
		Either 
			button-1 places item in figure
		Or
			button-2/3 remove items
		'''
		textItem = self.motionLabel
		if event.button > 1:
			textItem.remove()
			self.disconnect_events()
			self.redraw()
			
		elif event.button == 1:
			self.disconnect_events()	
			self.save_added_text(textItem)
			self.redraw()
					
		self.motionLabel = None
		self.infolabel.set('Done. Double click on text opens the editor again.')
		
	def save_added_text(self,text):
		'''
		'''
		id = len(self.textsAdded)
		self.textsAdded[id] = text
		self.textDict['x'], self.textDict['y'] = text.get_position()
		self.mainFigureCollection.store_figure_text(self.figureId,id,self.textDict)
		
		
	def disconnect_events(self):
		'''
		'''
		self.figure.canvas.mpl_disconnect(self.on_motion_event)	
		self.figure.canvas.mpl_disconnect(self.on_click_event)		
		
		
	def add_image_to_axis(self, pathToFile = None, axisId = None):
		'''
		'''
		if self.check_if_axes_created() == False:
			return
		if pathToFile is None:
			pathToFile = tf.askopenfilename(initialdir=path_file,
                                        title="Choose File",parent = self.toplevel)
		
		if pathToFile == '':
			return
		
		fileEnd = pathToFile.split('.')[-1]	
		if fileEnd != 'png':
			tk.messagebox.showinfo('File error ..','At the moment only png files are supported.'+
									' Your file path ends with: {}'.format(fileEnd),
									parent = self.toplevel)
			return

		im = plt.imread(pathToFile)
		if axisId is None:
			axesInFigure = []
			for id, props in self.figureProps.items():
				axesInFigure.append('Subplot Id: {} - Label: {}'.format(id,props['axisLabel']))
			
		## select axis
			dialog = simple_dialog.simpleUserInputDialog(['Subplot: '],
				[axesInFigure[0]],[axesInFigure],
				title='Select subplot',infoText='Select subplot.')
		
			axisId = int(float(dialog.selectionOutput['Subplot: '].split(' ')[2]))	
		ax = self.figureProps[axisId]['ax']
		
		axOrigPosition = ax.get_position()
		## show image 
		ax.imshow(im)
		ax.axis('off')
		self.infolabel.set('The original resolution is restored upon export.')	
		self.redraw()
		self.align_image_in_axis(ax,axOrigPosition)
		self.redraw()
		self.mainFigureCollection.store_image_export(axisId,self.figureId,pathToFile)

	def restore_axes(self,figureProps):
		'''
		Restores axis by a dict. Used when restored from saved session
		'''
		axisParams = None
		for id,props in figureProps.items():
		
			self.axisId = id
			
			axisParams = props['axisParams']
			axisParams[-1] = props['axisLabel']
			self.add_axis_to_figure(axisParams,axisId = id,
									redraw=False,addToId=False)
		if axisParams is not None:
			self.update_axis_parameters(axisParams)
				
	def identify_id_of_axis(self,ax):	
		'''
		'''
		axClicked = ax
		for id,props in self.figureProps.items():
			if props['ax'] == axClicked:
				return id
				
		for id, axes in self.associatedAxes.items():
			if axClicked in axes:
				return id
		

	def save_axis_props(self,ax,axisParams,addToId = True):
		'''
		Need to save:
			- axis with id
			- label 
			- subplot specs 
			- associated axis (for example hclust)
		'''
		# we dont want to add 1 if we restore figures
		if addToId:
			self.axisId += 1
		id = self.axisId
		self.figureProps[id] = {}
		self.figureProps[id]['ax'] = ax
		self.figureProps[id]['axisParams'] = axisParams
		# save label for quick change
		self.figureProps[id]['axisLabel'] = axisParams[-1]
		self.figureProps[id]['addAxis'] = []
		self.mainFigureCollection.update_params(self.figureId,id,self.figureProps[id])
		self.menu.insert_command(index = len(self.figureProps)+2,label='Subplot - %s' % axisParams[-1],
			command = lambda: self.initiate_transfer(id,self.figureId)) 
		self.axisItems[id] = {}
		
	def initiate_transfer(self,axisId,figureId):
		'''
		'''
		idClicked = self.identify_id_of_axis(self.event.inaxes)
		if axisId == idClicked:
			tk.messagebox.showinfo('Error..','Already in position.',parent=self.toplevel)
			return
		else:
			self.clear_axis(self.figureProps[axisId]['ax'])
			axisDict = self.mainFigureCollection.exportDetails[figureId]
			self.mainFigureCollection.analyze.unpack_exports(axisDict,figureId,
															 specAxisId = idClicked,
															 specificAxis = self.figureProps[axisId]['ax'],
															 transferAxisId = axisId)
			self.add_axis_label(ax = self.figureProps[axisId]['ax'],
								axisId = axisId,
								label = self.figureProps[axisId]['axisLabel'])
			self.redraw()
	def clear_axis_from_menu(self):
		'''
		'''
		axisId = self.identify_id_of_axis(self.event.inaxes)
		quest = tk.messagebox.askquestion('Confirm ..',
			'Clear subplot?',
			parent=self.toplevel)
		if quest == 'yes':
		
			self.mainFigureCollection.update_params(self.figureId,axisId = axisId,how='clear')
			self.clear_axis(self.figureProps[axisId]['ax'])
			self.add_axis_label(ax = self.figureProps[axisId]['ax'],
								axisId = axisId,
								label = self.figureProps[axisId]['axisLabel'])
			self.redraw()
		
	def delete_axis(self):
		'''
		'''
		if self.delete_axis_event is not None:
			self.disconnect_and_reset_deleting()
			return
			
		if self.check_if_axes_created():
			self.but_delete_ax.configure(image=self.delete_axis_active_img)
			self.infolabel.set('Deleting active. Click on subplot to delete.')
			self.delete_axis_event = self.figure.canvas.mpl_connect('button_press_event', 
															   self.identify_and_remove_axis)
		
	def identify_and_remove_axis(self,event):
		'''
		Identify the clicked axis and remove it
		'''
		if len(self.figure.axes) == 0:
			return
		if event.inaxes is None:
			return
		if event.button != 1:
			return
		id = self.identify_id_of_axis(event.inaxes)
		self.check_for_associations_and_remove(id)
		self.mainFigureCollection.update_params(self.figureId,axisId = id,how='delete')
		self.menu.delete('Subplot - %s' % self.figureProps[id]['axisLabel']) 
		self.figure.delaxes(self.figureProps[id]['ax'])
		
		del self.figureProps[id]
		del self.axisItems[id]
		del self.axisLabels[id]
		
		self.redraw()
		
		if len(self.figure.axes) == 0:
			self.disconnect_and_reset_deleting()
			self.infolabel.set('Deleting done. No subplots left.')	
			self.update_axis_parameters([float(self.gridRow.get()),
										 float(self.gridColumn.get()),
										 1,0,1,1,'Z'])
			
	def check_for_associations_and_remove(self,axisId):
		'''
		'''
		if axisId in self.associatedAxes:
			axes = self.associatedAxes[axisId]
		
			for ax in axes:
				self.figure.delaxes(ax)
			del self.associatedAxes[axisId] 
			
		

	def clear_axis(self, axis):
		'''
		Clear axis and its axis associations
		'''
		id = self.identify_id_of_axis(axis)
		self.check_for_associations_and_remove(id)
		self.figureProps[id]['ax'].clear()
			
	def disconnect_and_reset_deleting(self):
		'''
		'''
		self.but_delete_ax.configure(image=self.delete_axis_img)
		self.figure.canvas.mpl_disconnect(self.delete_axis_event)
		self.delete_axis_event = None
				
	def clean_up_figure(self):
		'''
		Clean up figure
		'''
		quest = tk.messagebox.askquestion('Confirm ..','Clean up main figure template?',
										parent = self.toplevel)
		if quest == 'yes':
			self.figure.clf()
			self.redraw()
			self.update_axis_parameters([float(self.gridRow.get()),
									 float(self.gridColumn.get()),
									 1,0,1,1,'Z'])
			self.infolabel.set('Cleaned up.')
			self.clear_dicts()
			self.define_menu()

			self.mainFigureCollection.update_params(self.figureId,how='clean_up')	
	
	def clear_dicts(self):
		'''
		'''
		self.axisLabels.clear()
		self.figureProps.clear()
		self.textsAdded.clear()
		self.axisItems.clear()	
	
	def associate_axes_with_id(self,axisId,axes):
		'''
		Function if additional axes were added.  Like in hierarchical clustering
		'''
		self.associatedAxes[axisId] = axes
		

	def extract_artists(self,ax,id):
		'''
		'''
		self.axisItems[id]['axis labels']= [ax.xaxis.get_label(),ax.yaxis.get_label()]
		self.axisItems[id]['x-ticks'] = ax.get_xticklabels()
		self.axisItems[id]['y-ticks'] = ax.get_yticklabels()
		self.axisItems[id]['annotations'] = [txt for txt in ax.texts]
		self.axisItems[id]['titles'] = [ax.title]
		self.axisItems[id]['lines'] = ax.lines
		self.axisItems[id]['collections'] = ax.collections
		self.axisItems[id]['patches'] = ax.patches
		self.axisItems[id]['artists'] = ax.artists
		
		leg =  ax.get_legend()
		
		legendTexts = []
		if leg is not None:
			self.axisItems[id]['legend texts'] = [leg.get_texts()]
			self.axisItems[id]['legend caption'] = [leg.get_title()]
		
		
	def redraw(self):
		'''
		Redraws figure canvas
		'''
		self.figure.canvas.draw()	
		
	def center_popup(self,size):
         	'''
         	Casts the popup in center of screen
         	'''

         	w_screen = self.toplevel.winfo_screenwidth()
         	h_screen = self.toplevel.winfo_screenheight()
         	x = w_screen/2 - size[0]/2
         	y = h_screen/2 - size[1]/2
         	self.toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))	