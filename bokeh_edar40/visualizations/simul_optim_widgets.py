
from bokeh.layouts import widgetbox, column, row
from bokeh.models import Div, Panel, Tabs
from bokeh.models.widgets import Select, Button, Slider, TextInput, RadioButtonGroup
from collections import OrderedDict
import utils.bokeh_utils as bokeh_utils
import time
import random

def create_div_title(title = ''):
	"""Crea el título para un objeto de la interfaz bokeh
	Parameters:
		title: String con el título a crear
	
	Returns:
		div_title: Objeto Div de bokeh con el título creado
	"""

	div_title = Div(
				text=title,
				style={
					'font-weight': 'bold',
					'font-size': '16px',
					'color': bokeh_utils.TITLE_FONT_COLOR,
					'margin-top': '2px',
					'font-family': 'inherit'},
				height=20,
				sizing_mode='stretch_width')
	
	return div_title

class DynamicSimulRow:
	"""Clase DynamicSimulRow para representar una fila dinámica con slider y textbox
	
	Attributes:
		start: Valor inicial del slider
		end: Valor final del slider
		value: Valor por defecto del slider y el textbox
		title: Título del slider
	"""
	def __init__(self, start, end, value, title):
		self.start = start
		self.end = end
		self.value = value
		self.title = title
		self.slider = Slider(start=self.start, end=self.end, value=self.value, step=0.1, title=self.title, max_width=280)
		self.text_input = TextInput(value=f"{self.value:.2f}", max_width=100)
		self.dyn_row = row([self.slider, self.text_input], sizing_mode='stretch_height')
		self.slider.on_change('value',self.slider_handler)
		self.text_input.on_change('value',self.text_handler)
	def slider_handler(self, attrname, old, new):
		self.text_input.value = f"{new:.2f}"
	def text_handler(self, attrname, old, new):
		self.slider.value = float(new)

class DynamicSimulWidget:
	"""Clase DynamicSimulWidget para representar widget dinámicos con sliders y textbox de simulación
	
	Attributes:
		df: Dataframe con las estadisticas para min, mean, max de los sliders
		target: Target de simulación
	"""
	def __init__(self, target, df):
		self.target = target
		self.df = df
		self.new_rows = OrderedDict([])
		columns = column([])
		target_title = create_div_title(f'Simulación - {self.target}')
		target_title.min_width = 390
		var_title = Div(text='<b>Variables de entrada</b>')
		for var in list(self.df.keys()):
			delta = (self.df[var]['max']-self.df[var]['min']) * 0.1
			self.new_rows.update({var: DynamicSimulRow(start=max(0,self.df[var]['min']-delta),
                                    						end=self.df[var]['max']+delta,
                                          					value=self.df[var]['mean'],
                                          					title=var)})
			columns.children.append(self.new_rows[var].dyn_row)
		button_simulate = Button(label="Simular", button_type="primary", max_width=180, min_width=180)
		button_simulate.on_click(self.simulate)
		self.sim_target = Div(text=f'<b>{self.target}:</b>')
		self.div_spinner = Div(text="")
		self.wb = widgetbox([target_title,
							var_title,
							columns,
							self.sim_target,
							row([button_simulate, self.div_spinner], sizing_mode='stretch_width')],
							min_width = 390,
							max_width=400,
							sizing_mode='stretch_width')
	def show_spinner(self):
		spinner_text = """
					<!-- https://www.w3schools.com/howto/howto_css_loader.asp -->
					<div class="loader">
					<style scoped>
					.loader {
						border: 4px solid #f3f3f3; /* Light grey */
						border-top: 4px solid #3498db; /* Blue */
						border-radius: 50%;
						width: 25px;
						height: 25px;
						animation: spin 2s linear infinite;
					}

					@keyframes spin {
						0% { transform: rotate(0deg); }
						100% { transform: rotate(360deg); }
					} 
					</style>
					</div>
					"""
		# self.div_spinner.visible = True
		self.div_spinner.text = spinner_text
	def hide_spinner(self):
		# self.div_spinner.visible = False
		self.div_spinner.text = ""
	def simulate(self, new):
		"""Callback que simula y obtiene una predicción con los valores fijados por el usuario en los sliders
		"""
		self.show_spinner()
		vars_influyentes = {var: round(drow.slider.value,2) for (var, drow) in self.new_rows.items()}
		self.sim_target.text = f'<b>{self.target}</b>: cluster_{random.randint(0,4)}'
		print(vars_influyentes)
		self.hide_spinner()

        # TODO json_simul = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Simulacion_JSON?,
		#				                    username='rapidminer',
		#				                    password='rapidminer',
		# 				                    parameters={'Modelo': self.target, 'Variables_influyentes': vars_influyentes},
		# 				                    out_json=True)

class DynamicOptimRow:
	"""Clase DynamicOptimRow para representar una fila dinámica con cada variable influyente y sus respectivos combobox para las restricciones
	
	Attributes:
		var_title: Título de la restricción
	"""
	def __init__(self, var_title):
		var_row_title = Div(text=f'{var_title}:')
		self.var_found_value = Div(text='')
		self.low_condition_select = Select(title='Condición1', value='-', options=['<', '≤', '=', '≥', '>', '-'], max_width=80, min_width=80)
		# self.low_inter_text = TextInput(title='Valor1', value='', max_width=80, min_width=80, visible=False)
		# self.high_condition_select = Select(title='Condición2', value='-', options=['<', '≤', '≥', '>', '-'], max_width=80, min_width=80, visible=False)
		# self.high_inter_text = TextInput(title='Valor2', value='', max_width=80, min_width=80, visible=False)
		self.low_inter_text = TextInput(title='Valor1', value='', max_width=80, min_width=80)
		self.high_condition_select = Select(title='Condición2', value='-', options=['<', '≤', '≥', '>', '-'], max_width=80, min_width=80)
		self.high_inter_text = TextInput(title='Valor2', value='', max_width=80, min_width=80)
		target_col = row(children=[var_row_title, self.var_found_value],
							  sizing_mode='stretch_width',
							  max_width=200,
                              min_width=200)
		self.dyn_row = row([target_col,
							self.low_condition_select,
							self.low_inter_text,
							self.high_condition_select,
							self.high_inter_text], sizing_mode='stretch_width')
# 		self.low_condition_select.on_change('value', self.low_select_handler)
# 		self.high_condition_select.on_change('value', self.high_select_handler)
# 	def low_select_handler(self, attr, old, new):
# #             print(f'attr: {attr}, old: {old}, {new}')
# 		if new=='-':
# 			self.low_inter_text.visible=False
# 			self.high_condition_select.value = '-'
# 			self.high_condition_select.visible = False
# 		elif new=='=':
# 			self.low_inter_text.visible=True
# 			self.high_condition_select.value = '-'
# 			self.high_condition_select.visible = False
# 		else:
# 			self.low_inter_text.visible=True
# 			self.high_condition_select.visible = True
# 	def high_select_handler(self, attr, old, new):
# #             print(f'attr: {attr}, old: {old}, {new}')
# 		if new=='-':
# 			self.high_inter_text.visible = False
# 		else:
# 			self.high_inter_text.visible = True

class DynamicOptimWidget:
	"""Clase DynamicOptimWidget para representar widget dinámicos con todas las restricciones para optimizar
	
	Attributes:
		target: Target de optimización
		possible_targets: Lista de posibles clusters/rangos a optimizar
		var_influyentes: Lista variables influyentes que calculadas por el optimizador
	"""
	def __init__(self, target, possible_targets, var_influyentes):
		self.target = target
		# self.possible_targets = possible_targets
		self.var_influyentes = var_influyentes
		target_title = create_div_title(f'Optimización - {self.target}')
		self.objective_select = Select(title='Objetivo', value='min', options=['min', 'max'])
		self.target_select = Select(title='Target', value=possible_targets[-1], options=possible_targets, min_width=110)
		restrict_title = Div(text='<b>Restricciones</b>')
		self.dyn_row_list = OrderedDict([])
		columns = column([], sizing_mode='stretch_width')
		for var in self.var_influyentes:
			self.dyn_row_list.update({var:DynamicOptimRow(var_title=var)})
			columns.children.append(self.dyn_row_list[var].dyn_row)
		button_optimize = Button(label="Optimizar", button_type="primary", max_width=180, min_width=180)
		button_optimize.on_click(self.optimizar)
		self.div_spinner = Div(text="")
		self.wb = widgetbox([target_title,
							row([self.objective_select, self.target_select], sizing_mode='stretch_width'),
							restrict_title,
							columns,
							row([button_optimize, self.div_spinner], sizing_mode='stretch_width')], sizing_mode='stretch_width', max_width=300)
	def show_spinner(self):
		spinner_text = """
					<!-- https://www.w3schools.com/howto/howto_css_loader.asp -->
					<div class="loader">
					<style scoped>
					.loader {
						border: 4px solid #f3f3f3; /* Light grey */
						border-top: 4px solid #3498db; /* Blue */
						border-radius: 50%;
						width: 25px;
						height: 25px;
						animation: spin 2s linear infinite;
					}

					@keyframes spin {
						0% { transform: rotate(0deg); }
						100% { transform: rotate(360deg); }
					} 
					</style>
					</div>
					"""
		# self.div_spinner.visible = True
		self.div_spinner.text = spinner_text
	def hide_spinner(self):
		# self.div_spinner.visible = False
		self.div_spinner.text = ""
	def optimizar(self):
		"""Callback que optimiza y obtiene los valores de las variables influyentes según objetivo fijado
		"""
		start = time.time()
		self.show_spinner()
		restricciones = {}
		for var, drow in self.dyn_row_list.items():
			condicion1 = drow.low_condition_select.value
			condicion2 = drow.high_condition_select.value
			dict_condicion1 = self.create_dict_condicion(num_condicion=1,
															condicion=condicion1,
															val_condicion_raw=drow.low_inter_text.value)
			dict_condicion2 = self.create_dict_condicion(num_condicion=2,
															condicion=condicion2,
															val_condicion_raw=drow.high_inter_text.value)
			if dict_condicion1:
				dict_condicion1.update(dict_condicion2)
				restricciones.update({var: dict_condicion1})
			self.dyn_row_list[var].var_found_value.text = f'<b>{round(random.uniform(0,20),2)}</b>'
		
		arg_target = {'variable':self.target, 'valor':self.target_select.value, 'objetivo': self.objective_select.value}
		self.hide_spinner()
		print(f'Target: {arg_target}')
		print(f'Restricciones: {restricciones}')
		print(f'Total time: {time.time()-start}')
		# TODO json_optim = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Optimizacion_JSON?,
		#				                    username='rapidminer',
		#				                    password='rapidminer',
		# 				                    parameters={'Target': arg_target, 'Restricciones': restricciones},
		# 				                    out_json=True)

	def create_dict_condicion(self, num_condicion, condicion, val_condicion_raw):
		"""Función que crea el diccionario con la restricción especificada

		Parameters:
			num_condicion: Número de la condición (posible 1 o 2)
			condicion: Tipo de condición (<, >, <=, >=, =, -)
			val_condicion_raw: Valor ingresado por el usuario de la condición sin procesar
		
		Returns:
			dict_condicion: Diccionario con la restricción creada
		"""
#             print(f'num_condicion: {num_condicion}, condicion: {condicion}, val_condicion_raw: {val_condicion_raw}')
		if condicion != '-':
			try:
				val_condicion = max(0, float('0'+val_condicion_raw))
			except:
				val_condicion = 0
			dict_condicion = {f'condicion{num_condicion}': condicion,
								f'val_condicion{num_condicion}': val_condicion}
		else:
			dict_condicion = {}
		return dict_condicion

class SimulOptimWidget:
	def __init__(self, target, simul_df, possible_targets, var_influyentes):
		self.simulate_wb = DynamicSimulWidget(target=target, df=simul_df)
		self.optimize_wb = DynamicOptimWidget(target=target, possible_targets=possible_targets, var_influyentes=var_influyentes)
		self.wb = widgetbox([self.simulate_wb.wb], sizing_mode='stretch_width')
		self.rb = RadioButtonGroup(labels=['Simular', 'Optimizar'], height=35, active=0, max_width=390)
		self.rb.on_click(self.select_simul_optim)
		# tab_simulate = Panel(child=simulate_wb.wb, title="Simular")
		# tab_optimize = Panel(child=optimize_wb.wb, title="Optimizar")
		# self.tabs = Tabs(tabs=[ tab_simulate, tab_optimize ], max_width=650, sizing_mode='stretch_width')

	def select_simul_optim(self, new):
		if new == 0:
			self.wb.children = [self.simulate_wb.wb]
		else:
			self.wb.children = [self.optimize_wb.wb]
