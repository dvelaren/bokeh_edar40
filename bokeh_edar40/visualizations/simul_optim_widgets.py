
import utils.bokeh_utils as bokeh_utils
import time
import random
from collections import OrderedDict
from pandas.io.json import json_normalize

from utils.rapidminer_proxy import call_webservice
from bokeh.models import Div, Panel, Tabs
from bokeh.models.widgets import Select, Button, Slider, TextInput, RadioButtonGroup
from bokeh.layouts import widgetbox, column, row

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

class Spinner:
	def __init__(self, size=25):
		self.size = size	
		self.spinner = Div(text="", min_width=self.size, min_height=self.size, sizing_mode='scale_both')
	def show_spinner(self):
		begin_text = """
					<!-- https://www.w3schools.com/howto/howto_css_loader.asp -->
					<div class="loader">
					<style scoped>
					.loader {
						border: 4px solid #f3f3f3; /* Light grey */
						border-top: 4px solid #3498db; /* Blue */
						border-radius: 50%;
					"""
		mod_text = f"width: {self.size}px;height: {self.size}px;"
		end_text =	"""
					animation: spin 2s linear infinite;
					}

					@keyframes spin {
						0% { transform: rotate(0deg); }
						100% { transform: rotate(360deg); }
					} 
					</style>
					</div>
					"""
		spinner_text = begin_text + mod_text + end_text
		self.spinner.text = spinner_text
	def hide_spinner(self):
		self.spinner.text = ""

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
		self.slider = Slider(start=self.start, end=self.end,
							value=self.value, step=0.1,
							title=self.title, min_width=580)
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
	def __init__(self, target, df, periodo):
		self.target = target
		self.df = df
		self.periodo = periodo
		self.new_rows = OrderedDict([])
		columns = column([])
		target_title = create_div_title(f'Simulación - {self.target}')
		target_title.min_width = 400
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
		self.div_spinner = Spinner()
		self.wb = widgetbox([target_title,
							var_title,
							columns,
							self.sim_target,
							row([button_simulate, self.div_spinner.spinner], sizing_mode='stretch_width')],
							min_width=390,
							max_width=450,
							sizing_mode='stretch_width')
	def simulate(self, new):
		"""Callback que simula y obtiene una predicción con los valores fijados por el usuario en los sliders
		"""
		self.div_spinner.show_spinner()
		vars_influyentes = {var: round(drow.slider.value,2) for (var, drow) in self.new_rows.items()}
		json_simul = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Simulacion_JSON_v1?',
									username='rapidminer',
									password='rapidminer',
									parameters={'Modelo': self.target, 'Variables_influyentes': str(vars_influyentes), 'Ruta_periodo':f'/home/admin/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_{self.periodo}.csv'},
									out_json=True)
		print(f'Modelo: {self.target}')
		print(f'Ruta_periodo: /home/admin/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_{self.periodo}.csv')
		print(vars_influyentes)
		simul_result = json_normalize(json_simul)
		print(simul_result[f'prediction({self.target})'][0])
		# self.sim_target.text = f'<b>{self.target}</b>: cluster_{random.randint(0,4)}'
		self.sim_target.text = f"<b>{self.target}</b>: {simul_result[f'prediction({self.target})'][0]}"
		self.div_spinner.hide_spinner()

class DynamicOptimRow:
	"""Clase DynamicOptimRow para representar una fila dinámica con cada variable influyente y sus respectivos combobox para las restricciones
	
	Attributes:
		var_title: Título de la restricción
	"""
	def __init__(self, var_title, ranges):
		var_row_title = Div(text=f'{var_title}:', width=360, sizing_mode='fixed')
		self.var_found_value = Div(text='', width=360, sizing_mode='fixed')
		self.low_condition_select = Select(title='Condición1', value='-', options=['=', '-'], width=160, sizing_mode='fixed')
		self.low_inter_text = Select(title='Valor1', value=ranges[0], options=ranges, width=160, sizing_mode='fixed')
		target_col = column(children=[var_row_title, self.var_found_value],
							  sizing_mode='fixed',
							  width=360)
		self.dyn_row = row([target_col,
							self.low_condition_select,
							self.low_inter_text], sizing_mode='fixed', width=700)

class DynamicOptimWidget:
	"""Clase DynamicOptimWidget para representar widget dinámicos con todas las restricciones para optimizar
	
	Attributes:
		target: Target de optimización
		possible_targets: Lista de posibles clusters/rangos a optimizar
		var_influyentes: Lista variables influyentes que calculadas por el optimizador
	"""
	def __init__(self, target, possible_targets, var_influyentes, ranges):
		self.target = target
		self.ranges = ranges
		self.var_influyentes = var_influyentes
		target_title = create_div_title(f'Optimización - {self.target}')
		target_title.width=700
		target_title.sizing_mode='fixed'
		self.objective_select = Select(title='Objetivo', value='max', options=['max'], width=110, sizing_mode='fixed')
		self.target_select = Select(title='Target', value=possible_targets[-1], options=possible_targets, width=110, sizing_mode='fixed')
		restrict_title = Div(text='<b>Restricciones</b>', width= 360, sizing_mode='fixed')
		self.dyn_row_list = OrderedDict([])
		columns = column([], width=360, sizing_mode='fixed')
		self.div_prediccion = Div(text=f'<b>Predicción: </b>NA, <b>Confianza: </b>NA', width=360, sizing_mode='fixed')
		for var in self.var_influyentes:
			self.dyn_row_list.update({var:DynamicOptimRow(var_title=var,ranges=self.ranges['Values'][var].split(', '))})
			columns.children.append(self.dyn_row_list[var].dyn_row)
		button_optimize = Button(label="Optimizar", button_type="primary", width=180, sizing_mode='fixed')
		button_optimize.on_click(self.optimizar)
		self.div_spinner = Spinner()
		self.wb = widgetbox([target_title,
							row([self.objective_select, self.target_select], sizing_mode='fixed'),
							restrict_title,
							columns,
							self.div_prediccion,
							row([button_optimize, self.div_spinner.spinner], width=360, sizing_mode='fixed')], sizing_mode='fixed', width=700)
	def optimizar(self):
		"""Callback que optimiza y obtiene los valores de las variables influyentes según objetivo fijado
		"""
		start = time.time()
		self.div_spinner.show_spinner()
		restricciones = {}
		for var, drow in self.dyn_row_list.items():
			condicion1 = drow.low_condition_select.value
			val_condicion_raw = drow.low_inter_text.value
			dict_condicion1 = self.create_dict_condicion(num_condicion=1,
														condicion=condicion1,
														val_condicion_raw=val_condicion_raw)
			if dict_condicion1:
				restricciones.update({var: dict_condicion1})
			# self.dyn_row_list[var].var_found_value.text = f'<b>{round(random.uniform(0,20),2)}</b>'		
		arg_target = {'variable':self.target, 'valor':self.target_select.value, 'objetivo': self.objective_select.value}
		json_optim = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Optimizacion_v0?',
										username='rapidminer',
										password='rapidminer',
										parameters={'Target': arg_target, 'Restricciones': restricciones},
										out_json=True)
		df_optim = json_normalize(json_optim)
		print(df_optim)
		for var in self.dyn_row_list:
			self.dyn_row_list[var].var_found_value.text = f'<b>{df_optim[var][0]}</b>'
		pred = df_optim[f'prediction({self.target})'][0]
		conf = round(df_optim[f'confidence({pred})'][0]*100,3)
		self.div_prediccion.text=f'<b>Predicción: </b>{pred}, <b>Confianza: </b>{conf}%'
		print(f'pred: {pred}, conf: {conf}')
		self.div_spinner.hide_spinner()
		print(f'Target: {arg_target}')
		print(f'Restricciones: {restricciones}')
		print(f'Total time: {time.time()-start}')
	def create_dict_condicion(self, num_condicion, condicion, val_condicion_raw):
		"""Función que crea el diccionario con la restricción especificada

		Parameters:
			num_condicion: Número de la condición (posible 1 o 2)
			condicion: Tipo de condición (<, >, <=, >=, =, -)
			val_condicion_raw: Valor ingresado por el usuario de la condición sin procesar
		
		Returns:
			dict_condicion: Diccionario con la restricción creada
		"""
		print(f'val_condicion_raw:{val_condicion_raw}')
		if condicion != '-':
			try:
				# val_condicion = max(0, float('0'+val_condicion_raw))
				val_condicion = val_condicion_raw
			except:
				val_condicion = 0
			dict_condicion = val_condicion
		else:
			dict_condicion = ''
		return dict_condicion

class SimulOptimWidget:
	def __init__(self, target, simul_df, possible_targets, var_influyentes, periodo, ranges):
		self.simulate_wb = DynamicSimulWidget(target=target, df=simul_df, periodo=periodo)
		self.optimize_wb = DynamicOptimWidget(target=target, possible_targets=possible_targets, var_influyentes=var_influyentes, ranges=ranges)
		self.wb = widgetbox([self.simulate_wb.wb], sizing_mode='stretch_width')
		self.rb = RadioButtonGroup(labels=['Simular', 'Optimizar'], height=35, active=0, max_width=690)
		self.rb.on_click(self.select_simul_optim)
	def select_simul_optim(self, new):
		if new == 0:
			self.wb.children = [self.simulate_wb.wb]
		else:
			self.wb.children = [self.optimize_wb.wb]
