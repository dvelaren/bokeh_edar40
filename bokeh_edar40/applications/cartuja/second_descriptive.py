from utils.rapidminer_proxy import call_webservice
from bokeh_edar40.visualizations.decision_tree import Node, Tree
from bokeh_edar40.visualizations.simul_optim_widgets import SimulOptimWidget, create_div_title, Spinner
import utils.bokeh_utils as bokeh_utils
from utils.generate_model_vars import load_or_create_model_vars, load_obj, save_obj

# from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, Div, HoverTool, GraphRenderer, StaticLayoutProvider, Rect, MultiLine, LinearAxis, Legend, Span, Label, BasicTicker, ColorBar, LinearColorMapper, PrintfTickFormatter, MonthsTicker, LinearAxis, Range1d
from bokeh.models.widgets import Select, Button, DataTable, CheckboxButtonGroup
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox, column, row
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tickers import FixedTicker
from bokeh.transform import dodge, transform

import xml.etree.ElementTree as et
import pandas as pd
import numpy as np
import re
from pandas.io.json import json_normalize
from collections import OrderedDict
from datetime import datetime as dt
import time


def create_data_source_from_dataframe(df, group_value_name, group_value):
	"""Crea ColumnDataSource desde DataFrame agrupando los valores de una columna concreta según un valor
	Parameters:
		df (Dataframe): Dataframe de datos
		group_value_name (string): Nombre de columna donde buscar los valores a agrupar
		goup_value (string): Valor para agrupar los datos
	
	Returns:
		ColumnDataSource: ColumnDataSource con los datos correctamente agrupados
	"""
	df = df.loc[df[group_value_name].isin([group_value])]
	source = ColumnDataSource(df)

	return source

def calc_xoffset_corrects_plot(num_vals, bar_width):
    """Calcula el x offset de las barras según su ancho
    Parameters:
        num_vals (int): Número de valores a mostrar en la visualización
        bar_width (float): Ancho de cada barra del gráfico

    Returns:
        list: Valores de coordenadas X donde dibujar las barras del gráfico de aciertos
    """
    x_pos = []
    start_x = 0

    if num_vals % 2 != 0:
        start_x = 0
    else:
        start_x = bar_width

    # Computamos la posición de cada barra en el gráfico dependiendo del número de gráficos a mostrar por grupo de predicción
    for i in range(num_vals):
        if start_x == 0:
            x = start_x + i * (bar_width + bar_width/2) - ((bar_width*num_vals/2) + bar_width/2)
        else:
            x = start_x + i * (bar_width + bar_width/2) - ((2*bar_width*num_vals/2) - bar_width/2)
            if i >= num_vals/2:
                x = x + (bar_width/2)
        x_pos.append(x)

    return x_pos

def create_corrects_plot(df, target):
	"""Crea gráfica de aciertos
	Parameters:
		df: Dataframe con los datos de la matriz de confusión

	Returns:
		DataTable: Tabla de matriz de confusión
	"""
	xlabels = list(df.keys())
	source = ColumnDataSource(df)

	corrects_plot = figure(x_range=xlabels, plot_height=400, toolbar_location=None, sizing_mode='stretch_width', output_backend="webgl")

	bar_width = 0.1
	xloc = calc_xoffset_corrects_plot(num_vals=len(xlabels), bar_width=bar_width)
	for i, label in enumerate(xlabels):
		r = corrects_plot.vbar(x=dodge('Actual', xloc[i], range=corrects_plot.x_range), top=label, width=bar_width, source=source,
				color=bokeh_utils.COLORS_DICT[re.sub(' \[.*?\]','',label)], legend_label=label, name=xlabels[i])
		hover = HoverTool(tooltips=[
			("Predicción", "$name"),
			("Aciertos", "@$name")
		], renderers=[r])
		corrects_plot.add_tools(hover)
	corrects_plot.x_range.range_padding = 0.1
	corrects_plot.xgrid.grid_line_color = None
	corrects_plot.y_range.start = 0
	corrects_plot.legend.location = "top_right"
	corrects_plot.legend.orientation = "vertical"
	corrects_plot.legend.click_policy = 'hide'
	corrects_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	corrects_plot.xaxis.major_label_orientation = np.pi/4
	corrects_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	corrects_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	corrects_plot.title.text = f'Gráfica de aciertos - {target}'
	corrects_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	corrects_plot.title.align = 'left'
	corrects_plot.title.text_font_size = '16px'
	corrects_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	corrects_plot.min_border_right = 15

	return corrects_plot

def create_attribute_weight_plot(df, target):
	"""Crea gráfica de importancia de predictores
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de importancia de predictores
	"""

	df['colors'] = bokeh_utils.BAR_COLORS_PALETTE[:len(df['Attribute'].values)]

	source = ColumnDataSource(df)
	
	hover_tool = HoverTool(
		tooltips = [
			('Peso', '@Weight{(0.00)}')
		]
		)

	weight_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_range=df['Attribute'].values, output_backend="webgl")

	weight_plot.vbar(x='Attribute', top='Weight', source=source, width=0.9, line_color='white', fill_color='colors')

	weight_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	weight_plot.xaxis.major_label_orientation = np.pi/4

	weight_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	weight_plot.y_range.start = 0

	weight_plot.title.text = f'Importancia de los predictores - {target}'
	weight_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	
	weight_plot.title.align = 'left'
	weight_plot.title.text_font_size = '16px'
	weight_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR

	weight_plot.add_tools(hover_tool)

	return weight_plot

def create_confusion_matrix(df):
	"""Crea tabla de matriz de confusión
	Parameters:
		data_dict (dict): Diccionario con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de importancia de predictores
	"""
	# Tranformar el DataFrame en un stack
	data_dict = df.stack().rename("value").reset_index()

	# Paleta de colores
	# colors = ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c','#08306b']
	colors = ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#08519c']

	# Had a specific mapper to map color with value
	mapper = LinearColorMapper(palette=colors, low=data_dict.value.min(), high=data_dict.value.max())

	# Define a figure
	p = figure(
		plot_height=270,
		x_range=list(data_dict.Actual.drop_duplicates()),
		y_range=list(reversed(data_dict.Prediction.drop_duplicates())),
		toolbar_location=None,
		tools="",
		x_axis_location="above",
		x_axis_label="Actual Label",
		y_axis_label="Predicted Label",
		sizing_mode='stretch_width',
		output_backend="webgl")
	p.xaxis.axis_line_color = None
	p.yaxis.axis_line_color = None
	p.xaxis.major_label_orientation = np.pi/4
	
	# Create rectangle for heatmap
	p.rect(
		x="Actual",
		y="Prediction",
		width=1,
		height=1,
		source=ColumnDataSource(data_dict),
		line_color=None,
		fill_color=transform('value', mapper))
	p.text(x="Actual",
		y="Prediction", text='value', text_align="center", text_baseline="middle", source=ColumnDataSource(data_dict))
	
	p.border_fill_color = bokeh_utils.BACKGROUND_COLOR	
	p.background_fill_color = bokeh_utils.BACKGROUND_COLOR

	# Add legend
	color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    ticker=BasicTicker(desired_num_ticks=len(colors)))
	color_bar.background_fill_color = bokeh_utils.BACKGROUND_COLOR

	p.add_layout(color_bar, 'right')

	return p

def create_model_menu(model_variables = []):
	"""Crea menú de selección de variables para modelización del árbol de decisión
	Parameters:
		model_variables: Lista con las variables para modelización

	Returns:
		Button: Botón del menú de selección
		Select: Panel de selección de variable del menú de selección
	"""

	option_values = model_variables
	selected_value = 'Calidad_Agua'
	title = create_div_title('Modelo')
	select = Select(value=selected_value, options=option_values, height=35, min_width=180, max_width=180)
	button = Button(label='Modelizar', button_type='primary', height=35, min_width=390, max_width=390)
	return title, button, select


def create_decision_tree_graph_renderer(plot, tree):
	"""Crea el renderizador del gráfico del árbol de decisión. Para ello se deben especificar configuraciones como: indices o identificadores
	de los nodos, colores de los nodos, tipos de figura de los nodos, tipos de figura de relación entre nodo y las relaciones entre los nodos (inicio y final)
	Parameters:
		plot (Figure): Figura Bokeh donde se muestra el árbol de decisión
		tree (Tree): Estructura del árbol de decisión a mostrar

	Returns:
		GraphRenderer: Renderizador del gráfico del árbol de decisión
	"""
	
	node_indices = [node.id for node in tree.node_list]
	node_colors = [node.color for node in tree.node_list]

	start, end = tree.get_nodes_relations()
	x, y = tree.get_layout_node_positions(plot)
	graph_layout = dict(zip(node_indices, zip(x,y)))

	graph = GraphRenderer()

	graph.node_renderer.data_source.add(node_indices, 'index')
	graph.node_renderer.data_source.add(node_colors, 'color')
	graph.node_renderer.glyph = Rect(height=0.15, width=0.2, fill_color='color')
	graph.edge_renderer.glyph = MultiLine(line_color='#b5b8bc', line_alpha=0.8, line_width=5)

	graph.edge_renderer.data_source.data = dict(
    	start=start,
    	end=end)

	graph.layout_provider = StaticLayoutProvider(graph_layout=graph_layout)

	return graph

def append_labels_to_decision_tree(plot, graph, tree):
	"""Añade los textos necesarios (nombre del nodo y condición de relación) al gráfico del árbol de visualización
	Parameters:
		plot (Figure): Figura Bokeh donde se muestra el árbol de decisión
		graph (GraphRenderer): Renderizador del gráfico del árbol de decisión
		tree (Tree): Estructura del árbol de decisión a mostrar

	Returns:
		Figure: Gráfica del árbol de decisión
	"""
	plot.renderers = []
	plot.renderers.append(graph)
	
	node_text_x, node_text_y, node_text = tree.get_node_text_positions()
	plot.text(node_text_x, node_text_y, text=node_text, text_font_size={'value': '10pt'}, text_align='center')

	middle_x, middle_y, middle_text = tree.get_line_text_positions()
	plot.text(middle_x, middle_y, text=middle_text, text_font_size={'value': '10pt'}, text_align='center')
	return plot


def create_decision_tree_plot():
	"""Crea la figura para visualizar el árbol de decisión

	Returns:
		Figure: Gráfica del árbol de decisión
	"""
	plot = figure(x_range=(-1.1,1.1), y_range=(0,1.1), toolbar_location=None, plot_height=800, sizing_mode='stretch_width', output_backend="webgl", tools="")

	plot.axis.visible = False
	plot.xgrid.grid_line_color = None
	plot.ygrid.grid_line_color = None
	plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR	
	plot.background_fill_color = bokeh_utils.BACKGROUND_COLOR
	plot.outline_line_color = None

	return plot

def create_outlier_plot(df, tipo_var):
	"""Crea gráfica de outliers
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización
		tipo_var: Tipo de variable usada

	Returns:
		Figure: Gráfica de outliers
	"""

	# hover_tool = HoverTool(
	# 	tooltips = [
	# 		('Fecha', '@Fecha{%F}'),
	# 		('Outlier', '@outlier')
	# 	],
	# 	formatters = {
	# 		'Fecha': 'datetime',
	# 	},
	# 	mode = 'mouse'
	# 	)
	if tipo_var == 'RENDIMIENTOS':
		tools = [
					('Fecha', '@Fecha{%F}'),
					('Outlier', '@outlier'),
					('efluente_rend_elim_DBO5', "Val: @efluente_rend_elim_DBO5, Prom: @{mode(efluente_rend_elim_DBO5)}, Anom: @efluente_rend_elim_DBO5_anomalia"),
					('efluente_rend_elim_DQOt', 'Val: @efluente_rend_elim_DQOt, Prom: @{mode(efluente_rend_elim_DQOt)}, Anom: @efluente_rend_elim_DQOt_anomalia'),
					('efluente_rend_elim_NTK', 'Val: @efluente_rend_elim_NTK, Prom: @{mode(efluente_rend_elim_NTK)}, Anom: @efluente_rend_elim_NTK_anomalia'),
					('efluente_rend_elim_Pt','Val: @efluente_rend_elim_Pt, Prom: @{mode(efluente_rend_elim_Pt)}, Anom: @efluente_rend_elim_Pt_anomalia'),
					('efluente_rend_elim_SST','Val: @efluente_rend_elim_SST, Prom: @{mode(efluente_rend_elim_SST)}, Anom: @efluente_rend_elim_SST_anomalia')
				]
	elif tipo_var == 'ABSOLUTAS':
		tools = [
					('Fecha', '@Fecha{%F}'),
					('Outlier', '@outlier'),
					('efluente_DBO5t_conc', "Val: @efluente_DBO5t_conc, Prom: @{mode(efluente_DBO5t_conc)}, Anom: @efluente_DBO5t_conc_anomalia"),
					('efluente_DQOt_conc', 'Val: @efluente_DQOt_conc, Prom: @{mode(efluente_DQOt_conc)}, Anom: @efluente_DQOt_conc_anomalia'),
					('efluente_Ntk_conc', 'Val: @efluente_Ntk_conc, Prom: @{mode(efluente_Ntk_conc)}, Anom: @efluente_Ntk_conc_anomalia'),
					('efluente_Pt_conc','Val: @efluente_Pt_conc, Prom: @{mode(efluente_Pt_conc)}, Anom: @efluente_Pt_conc_anomalia'),
					('efluente_MES_conc','Val: @efluente_MES_conc, Prom: @{mode(efluente_MES_conc)}, Anom: @efluente_MES_conc_anomalia')
				]
	hover_tool = HoverTool(
			tooltips = tools,
			formatters = {
				'Fecha': 'datetime',
			},
			mode = 'mouse'
			)

	outlier_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime', output_backend="webgl")

	df['Fecha'] = pd.to_datetime(df['Fecha'])
	df['outlier'] = pd.to_numeric(pd.Series(df['outlier'].values))

	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	# outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_0, color=bokeh_utils.LINE_COLORS_PALETTE[0], size=6, legend_label='Cluster 0')
	# outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_1, color=bokeh_utils.LINE_COLORS_PALETTE[1], size=6, legend_label='Cluster 1')
	# outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_2, color=bokeh_utils.LINE_COLORS_PALETTE[2], size=6, legend_label='Cluster 2')
	# outlier_plot.circle(x='timestamp', y='outlier', source=source_cluster_3, color=bokeh_utils.LINE_COLORS_PALETTE[3], size=6, legend_label='Cluster 3')
	size = 5
	alpha = 0.4
	outlier_plot.circle(x='Fecha', y='outlier', source=source_cluster_0, color=bokeh_utils.LINE_COLORS_PALETTE[0], alpha=alpha, size=size, legend_label='Cluster 0')
	outlier_plot.circle(x='Fecha', y='outlier', source=source_cluster_1, color=bokeh_utils.LINE_COLORS_PALETTE[1], alpha=alpha, size=size, legend_label='Cluster 1')
	outlier_plot.circle(x='Fecha', y='outlier', source=source_cluster_2, color=bokeh_utils.LINE_COLORS_PALETTE[2], alpha=alpha, size=size, legend_label='Cluster 2')
	outlier_plot.circle(x='Fecha', y='outlier', source=source_cluster_3, color=bokeh_utils.LINE_COLORS_PALETTE[3], alpha=alpha, size=size, legend_label='Cluster 3')


	outlier_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	outlier_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	outlier_plot.legend.location = 'top_left'
	outlier_plot.legend.orientation = 'horizontal'
	outlier_plot.legend.click_policy = 'hide'
	outlier_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	outlier_plot.xaxis[0].formatter = DatetimeTickFormatter(years=['%Y'])

	outlier_plot.title.text = 'Probabilidad de Outliers'
	outlier_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	outlier_plot.title.align = 'left'
	outlier_plot.title.text_font_size = '16px'
	outlier_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	outlier_plot.add_tools(hover_tool)
	outlier_plot.min_border_right = 15

	return outlier_plot

def create_prediction_plot(df):
	"""Crea gráfica de predicción a futuro
	Parameters:
		df (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de de predicción a futuro
	"""

	hover_tool = HoverTool(
		tooltips = [
			('Fecha', '$x{%b %Y}'),
			('Predicción', '@Prediction')
		],
		formatters = {
			'$x': 'datetime',
		},
		mode = 'mouse'
		)

	# Estructuración de los tipos de datos del dataframe
	df['añomes'] = pd.to_datetime(df['añomes'], format='%m/%d/%y %I:%M %p')
	df['Prediction'] = pd.to_numeric(pd.Series(df['Prediction'].values))

	prediction_plot = figure(plot_height=400, toolbar_location=None, sizing_mode='stretch_width', x_axis_type='datetime', output_backend="webgl")
	
	source_cluster_0 = create_data_source_from_dataframe(df, 'cluster', 'cluster_0')
	source_cluster_1 = create_data_source_from_dataframe(df, 'cluster', 'cluster_1')
	source_cluster_2 = create_data_source_from_dataframe(df, 'cluster', 'cluster_2')
	source_cluster_3 = create_data_source_from_dataframe(df, 'cluster', 'cluster_3')

	x_axis_tick_vals = source_cluster_0.data['añomes'].astype(int) / 10**6

	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_0, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[0], legend_label='Cluster 0')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_1, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[1], legend_label='Cluster 1')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_2, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[2], legend_label='Cluster 2')
	prediction_plot.line(x='añomes', y='Prediction', source=source_cluster_3, line_width=2, line_color=bokeh_utils.LINE_COLORS_PALETTE[3], legend_label='Cluster 3')

	prediction_plot.xaxis.major_label_orientation = np.pi/4
	prediction_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	prediction_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	prediction_plot.legend.location = 'top_left'
	prediction_plot.legend.orientation = 'horizontal'
	prediction_plot.legend.click_policy = 'hide'
	prediction_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR
	prediction_plot.xaxis[0].formatter = DatetimeTickFormatter(months=['%b %Y'])
	prediction_plot.xaxis[0].ticker = FixedTicker(ticks=list(x_axis_tick_vals))
	# Linea vertical para definir el horizonte de predicción
	prediction_date = time.mktime(dt(2019, 9, 29, 0, 0, 0).timetuple())*1000
	vline = Span(location=prediction_date, dimension='height', line_color='gray', line_alpha=0.6, line_dash='dotted', line_width=2)
	prediction_plot.add_layout(vline)
	# Etiqueta linea horizontal
	vlabel = Label(x=prediction_date, y=40, text='→Predicción', text_color='gray', text_alpha=0.6, text_font_size='14px')
	prediction_plot.add_layout(vlabel)

	prediction_plot.title.text = 'Predicción de los clusters a futuro'
	prediction_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	prediction_plot.title.align = 'left'
	prediction_plot.title.text_font_size = '16px'
	prediction_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	prediction_plot.add_tools(hover_tool)
	prediction_plot.min_border_right = 15

	return prediction_plot

def create_df_confusion(df_original):
	"""Crea el dataframe para la matriz de confusion
	Parameters:
		df_original: Dataframe con los datos sin organizar de la matriz de confusión
	
	Returns:
		df: Dataframe con los datos convertidos para la matriz de confusion
	"""
	
	# Slicing dataframe for confussion matrix and removing redundant text
	df = df_original
	df['predicted'].replace(regex="pred ", value="", inplace=True)
	
	df = df.set_index("predicted")
	df.columns.name = 'Actual'
	df.index.name = 'Prediction'
	df.columns = df.columns.str.replace(r"true ", "")
	df = df.transpose()

	# Converting dataframe to right format
	df = df.apply(pd.to_numeric)
	return df

def append_count(df):
	"""Agrega columna con información de contadores
	Parameters:
		df: Dataframe con los datos del arbol
	Returns:
		df: Dataframe con la nueva columna

	"""
	col_sorted_text = []
	for row in range(len(df.index)):
		test_df = df.loc[row, df.columns.str.contains('range|cluster')].sort_values(ascending=False)
		sorted_text = []
		for key, value in test_df.items():
			new_key = re.sub("count_| \[.*?\]", '', key)
			sorted_text.append(f"{new_key}: {value}")
		col_sorted_text.append('\n'.join(sorted_text))
	df['Prediction_desc'] = col_sorted_text
	return df

def create_decision_tree_data(df, target='Calidad_Agua'):
	"""Crea el Tree del decision tree
	Parameters:
		df: Dataframe con los datos sin organizar del arbol de decision
	
	Returns:
		tree: Arbol listo para graficar con sus nodos
	"""

	tree = Tree()
	count = 0
	for j, elements in enumerate(df['Condition']):
		leaf = elements.split(' & ')
		# print(leaf)
		for i in range(len(leaf)+1):
			if i < len(leaf):
				node = leaf[i].split(' ', 1)
	#             print(node)
				node_name = node[0]
				tree_node = Node(count+1, node_name, i, '#c2e8e0')
	#             print(f"tree_node = Node({count+1}, '{node_name}', {i}, '#c2e8e0')")
				tree.order_nodes(tree_node, node[1])
	#             print(f"tree.order_nodes(tree_node, '{node[1]}')")
			else:
				if target == 'Calidad_Agua':
					node_name = df['Prediction_desc'][j]
					color = bokeh_utils.COLORS_DICT[df['Prediction'][j]]
				else:
					range_split = df['Prediction'][j].split(' ', 1)
					node_name = df['Prediction_desc'][j]
					color = bokeh_utils.COLORS_DICT[range_split[0]]
	#             print(f"tree_node = Node({count+1}, '{node_name}', {i}, '{color}')")
				tree_node = Node(count+1, node_name, i, color)
				tree.order_nodes(tree_node, node[1])
	#             print(f"tree.order_nodes(tree_node, '{node[1]}')")
			count = count + 1

	return tree


def create_daily_pred_plot(df_original, target='Calidad_Agua'):
	"""Crea gráfica de predicciones contra valores reales
	Parameters:
		df_original (Dataframe): Dataframe con los datos a mostrar en la visualización

	Returns:
		Figure: Gráfica de predicciones contra valores reales
	"""
	df = df_original
	df = df.rename(columns={target: 'real', f'prediction({target})': 'prediction'})
	bins = list(df['real'].unique())
	df['Fecha'] = pd.to_datetime(df['Fecha'], format='%m/%d/%y').sort_values()
	df = df.set_index('Fecha')
	df = df.groupby(df.index).first()
	# df = df['2018-01-01':'2019-01-31']

	if target=='Calidad_Agua':
		df.replace(regex=['cluster_'], value='', inplace=True)
	else:
		df.replace(regex=[r'\[.*\]', 'range'], value='', inplace=True)
	
	df[['real','prediction']] = df[['real','prediction']].astype(int)
	df['error'] = abs(df['real']-df['prediction'])

	TOOLTIPS = [
		('Fecha', "@Fecha{%F}"),
		('Real', '@real'),
		("Predicho", "@prediction")
	]
	hover_tool = HoverTool(tooltips = TOOLTIPS, formatters={'Fecha': 'datetime'})

	source = ColumnDataSource(df)

	daily_pred_plot = figure(plot_height=200, toolbar_location='right', sizing_mode='stretch_width', x_axis_type='datetime',
							tools='pan, box_zoom, reset', output_backend="webgl")
	daily_pred_plot.toolbar.logo = None
	# Se añade un nuevo eje Y para el error
	# daily_pred_plot.extra_y_ranges = {'y_error': Range1d(start=0, end=df['real'].max()-df['real'].min())}
	daily_pred_plot.extra_y_ranges = {'y_error': Range1d(start=0, end=len(bins))}
	daily_pred_plot.add_layout(LinearAxis(y_range_name='y_error', axis_label='Error', ticker=list(range(len(bins)))), 'right')

	daily_pred_plot.line(x='Fecha', y='real', source=source, line_width=2, line_color='#392FCC', line_alpha=0.8, legend_label='Real')
	daily_pred_plot.line(x='Fecha', y='prediction', source=source, line_width=2, line_color='#CA574D', line_alpha=0.8, line_dash='dashed', legend_label='Predicción')
	daily_pred_plot.line(x='Fecha', y='error', source=source, line_width=2, line_color='green', line_alpha=0.4, legend_label='Error', y_range_name='y_error')


	daily_pred_plot.xaxis.major_label_orientation = np.pi/4
	daily_pred_plot.xaxis.formatter = DatetimeTickFormatter(months=['%b %Y'])
	daily_pred_plot.xaxis.ticker = MonthsTicker(months=list(range(1,13)))
	
	if target == 'Calidad_Agua':
		daily_pred_plot.yaxis[0].ticker =  list(range(len(bins)))
		daily_pred_plot.yaxis[0].formatter = PrintfTickFormatter(format="Cluster %u")
	else:
		daily_pred_plot.yaxis[0].ticker =  list(range(1,1+len(bins)))
		daily_pred_plot.y_range=Range1d(0, len(bins)+1) # Manipulates y_range
		daily_pred_plot.yaxis[0].formatter = PrintfTickFormatter(format="Range %u")
	
	daily_pred_plot.ygrid.minor_grid_line_color = None
	daily_pred_plot.xaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR
	daily_pred_plot.yaxis.major_label_text_color = bokeh_utils.LABEL_FONT_COLOR

	daily_pred_plot.legend.location = 'top_left'
	daily_pred_plot.legend.orientation = 'horizontal'
	daily_pred_plot.legend.click_policy = 'hide'
	daily_pred_plot.legend.label_text_color = bokeh_utils.LABEL_FONT_COLOR

	daily_pred_plot.title.text = f'Predicciones diarias - {target}'
	daily_pred_plot.title.text_color = bokeh_utils.TITLE_FONT_COLOR
	daily_pred_plot.title.align = 'left'
	daily_pred_plot.title.text_font_size = '16px'
	daily_pred_plot.border_fill_color = bokeh_utils.BACKGROUND_COLOR
	daily_pred_plot.add_tools(hover_tool)
	daily_pred_plot.min_border_right = 15

	return daily_pred_plot

def create_df_sliders(weight_df, pred_df):
	"""Crea el dataframe que contiene los valores estadisticos para crear los sliders
	Parameters:
		weight_df: Dataframe con las variables influyentes
		pred_df: Dataframe con las predicciones diarias
	Returns:
		slider_df: Dataframe con los valores minimo, medio y máximo para la creación de sliders
	"""

	var_influyentes = list(weight_df['Attribute'])
	pred_df_stats=pred_df[var_influyentes].describe()
	df_sliders = pred_df_stats.loc[['min', 'mean', 'max']]

	return df_sliders

def create_div_text(text):
	"""Crea un texto dentro de un Div
	Parameters:
		text: Texto a escribir
	
	Returns:
		div_text: Div con el texto formateado
	"""
	div_text = Div(
				text=text,
				style={
					'font-weight': 'bold',
					'font-size': '14px',
					'color': bokeh_utils.LABEL_FONT_COLOR,
					'margin-top': '2px',
					'font-family': 'inherit'},
				height=20,
				sizing_mode='stretch_width')
	
	return div_text

def create_ranges_description(df, target='Calidad_Agua'):
	"""Crea los rangos posibles para el target
	Parameters:
		df: Dataframe con los datos del arbol de desicion
	
	Returns:
		col: Columna con todos los rangos posibles
	"""
	title = create_div_title(f'Listado de rangos posibles para {target}')
	rows = row([])
	for ran in list(df['Prediction'].unique()):
		rows.children.append(create_div_text(ran))
	col = column(row([title, rows]))

	return col

def modify_second_descriptive(doc):
	# Captura de los argumentos pasados desde flask
	args = doc.session_context.request.arguments
	try:
		periodo = int(args.get('periodo')[0])
		tipo_var = args.get('tipo_var')[0].decode('ascii')
	except:
		periodo = 0
		tipo_var = ''
	if tipo_var == 'abs':
		tipo_var = 'ABSOLUTAS'
	elif tipo_var == 'rend':
		tipo_var = 'RENDIMIENTOS'
	print(f'periodo: {periodo}, tipo_var: {tipo_var}')

	# Creación/Carga en RAM del diccionario con las variables a modelizar
	total_model_dict = load_or_create_model_vars(model_vars_file = 'resources/total_model_dict.pkl', 
												mask_file = 'resources/model_variables_mask.xlsx',
												sheets = ['ID_INFLUENTE',
															'ID_BIOS',
															'ID_FANGOS',
															'ID_HORNO',
															'ID_EFLUENTE',
															'ID_ELECTRICIDAD',
															'YOKO',
															'ANALITICA',
															'METEO'],
												cols = ['OUT', 'IN', 'MANIPULABLES', 'PROCESOS_IN'],
												force_create=False)

	# Inicialización del diccionario ordenado para almacenar los modelos creados
	models = OrderedDict([])
	try:
		created_models = load_obj(name='resources/created_models.pkl')
	except:
		created_models = ['Calidad_Agua']
	
	# Llamada al webservice de RapidMiner
	json_perfil_document = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Perfil_Out_JSON_v5?',
											username='rapidminer',
											password='rapidminer',
											parameters={'Ruta_periodo': f'https://edar.vicomtech.org/archivos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_{periodo}.csv',
														'Ruta_tipo_variable': f'https://edar.vicomtech.org/archivos/EDAR4.0_EDAR_Cartuja_VARIABLES_{tipo_var}.csv',
														'Normalizacion': 1},
											out_json=True)
	
	# Extracción de los datos web
	df_perfil = [json_normalize(data) for data in json_perfil_document]
	
	# Asignación de los datos web a su variable correspondiente
	prediction_df = df_perfil[3]
	outlier_df = df_perfil[4]

	# Creación de los gráficos y widgets permanentes en la interfaz
	prediction_plot = create_prediction_plot(prediction_df)
	outlier_plot = create_outlier_plot(outlier_df, tipo_var)
	simulation_title = create_div_title('Creación, Simulación y Optimización de modelos')
	model_title, add_model_button, model_select_menu = create_model_menu(model_variables=list(total_model_dict.keys()))
	create_model_spinner = Spinner(size=16)
	recreate_button = Button(label='Recrear', button_type='success', height=35, max_width=200, min_width=200)
	model_select_wb = widgetbox(
		[
		row([model_title, create_model_spinner.spinner], sizing_mode='stretch_width', max_width=400),
		row([model_select_menu, recreate_button], sizing_mode='stretch_width', max_width=400),
		add_model_button
		], max_width=400, sizing_mode='stretch_width')
	created_models_title = create_div_title('Modelos creados')
	created_models_checkbox = CheckboxButtonGroup(labels=list(models.keys()), height=35)
	created_models_checkbox.active = [0]
	delete_model_button = Button(label='Eliminar', button_type='danger', height=35, max_width=200)
	created_models_wb = widgetbox([created_models_title, created_models_checkbox], max_width=900, sizing_mode='stretch_width')

	# Callback para crear nuevamente el listado de variables de la mascara
	def recreate_callback():
		print('Recreando lista de variables para modelizar')
		nonlocal total_model_dict
		total_model_dict = load_or_create_model_vars(model_vars_file = 'resources/total_model_dict.pkl', 
												mask_file = 'resources/model_variables_mask.xlsx',
												sheets = ['ID_INFLUENTE',
															'ID_BIOS',
															'ID_FANGOS',
															'ID_HORNO',
															'ID_EFLUENTE',
															'ID_ELECTRICIDAD',
															'YOKO',
															'ANALITICA',
															'METEO'],
												cols = ['OUT', 'IN', 'MANIPULABLES', 'PROCESOS_IN'],
												force_create=True)
		model_select_menu.options = list(total_model_dict.keys())
		model_select_menu.value = 'Calidad_Agua'
	recreate_button.on_click(recreate_callback)

	# Callbacks para los widgets de la interfaz
	def prediction_callback(model='Calidad_Agua'):
		create_model_spinner.show_spinner()
		if initialize == False:
			model_objective = model_select_menu.value
		else:
			model_objective = model
		model_discretise = 5
		
		# Verificar que el modelo no ha sido creado antes
		if model_objective not in models:		
			# print(f'Objetivo: {model_objective}')
			# print(f'Discretizacion: {model_discretise}')
			# print(f'Ruta_periodo: /home/admin/Cartuja_Datos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_{periodo}.csv')
			# print(f'IN_MODELO: {total_model_dict[model_objective]}')
			# Llamar al servicio web EDAR_Cartuja_Prediccion con los nuevos parámetros
			json_prediction_document = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Prediccion_JSON_v5?',
														username='rapidminer',
														password='rapidminer',
														parameters={'Objetivo': model_objective,
																	'Discretizacion': model_discretise,
																	'Numero_Atributos': 4,
																	'Ruta_periodo': f'https://edar.vicomtech.org/archivos/EDAR4.0_EDAR_Cartuja_ID_PERIOD_{periodo}.csv',
																	'IN_MODELO': str(total_model_dict[model_objective])
																	},
														out_json=True)	
			
			# Obtener datos
			df_prediction = [json_normalize(data) for data in json_prediction_document]

			decision_tree_df = df_prediction[0]
			decision_tree_df = append_count(decision_tree_df)
			confusion_df_raw = df_prediction[1].reindex(columns=list(json_prediction_document[1][0].keys()))
			confusion_df = create_df_confusion(confusion_df_raw)
			weight_df = df_prediction[2]
			pred_df = df_prediction[3]
			ranges_df = df_prediction[4]
			ranges_df.set_index('Name', inplace=True)
			# ranges_df['Values']=ranges_df['Values'].replace(regex=r'\(.*\)',value='')
			slider_df = create_df_sliders(weight_df, pred_df)
			daily_pred_df = pred_df[['Fecha', model_objective, f'prediction({model_objective})']]
			possible_targets = sorted(list(pred_df[model_objective].unique()))
			var_influyentes = list(weight_df['Attribute'])
			decision_tree_data = create_decision_tree_data(decision_tree_df, model_objective)
			
			# Crear nuevos gráficos
			simul_or_optim_wb = SimulOptimWidget(target=model_objective, simul_df=slider_df, possible_targets=possible_targets, var_influyentes=var_influyentes, periodo=periodo, ranges=ranges_df)
			daily_pred_plot = create_daily_pred_plot(daily_pred_df, model_objective)
			decision_tree_plot = create_decision_tree_plot()
			decision_tree_graph = create_decision_tree_graph_renderer(decision_tree_plot, decision_tree_data)
			decision_tree_plot = append_labels_to_decision_tree(decision_tree_plot, decision_tree_graph, decision_tree_data)
			confusion_matrix = create_confusion_matrix(confusion_df)
			weight_plot = create_attribute_weight_plot(weight_df, model_objective)
			corrects_plot = create_corrects_plot(confusion_df, model_objective)
			model_title = create_div_title(f'Modelo - {model_objective}')
			confusion_title = create_div_title(f'Matriz de confusión - {model_objective}')
			decision_tree_title = create_div_title(f'Arbol de decisión - {model_objective}')
			ranges_description = create_ranges_description(decision_tree_df, model_objective)
			new_plots = layout([
				[model_title],
				[simul_or_optim_wb.rb],
				[simul_or_optim_wb.wb, ranges_description],
				[daily_pred_plot],
				[column([confusion_title, confusion_matrix], sizing_mode='stretch_width'), weight_plot, corrects_plot],
				[decision_tree_title],
				[decision_tree_plot]
			], name=model_objective, sizing_mode='stretch_width')

			# Almacenar en RAM y algunos gráficos y en ROM algunos modelos creados
			model_plots.children.append(new_plots)
			if model_objective not in created_models:
				created_models.append(model_objective)
			save_obj(created_models, 'resources/created_models.pkl')
			models.update({model_objective: new_plots})
			models.move_to_end(model_objective, last=False)
			created_models_checkbox.labels = list(models.keys())
			created_models_checkbox.active = list(range(len(models.keys())))
		create_model_spinner.hide_spinner()
	add_model_button.on_click(prediction_callback)

	# Callback para eliminar algunos modelos seleccionados
	def remove_model_handler(new):
		selected_labels = [created_models_checkbox.labels[elements] for elements in created_models_checkbox.active]
		try:
			for element in selected_labels:
				models.pop(element)
				model_plots.children.remove(doc.get_model_by_name(element))
				created_models.remove(element)
			save_obj(created_models, 'resources/created_models.pkl')
		except:
			for element in selected_labels:
				print(f"El modelo {element} no existe")
		created_models_checkbox.labels = list(models.keys())
		created_models_checkbox.active = list(range(len(models.keys())))
	delete_model_button.on_click(remove_model_handler)

	# Callback para mostrar u ocultar los gráficos de los modelos creados
	def show_hide_plots(new):
		selected_labels = [created_models_checkbox.labels[elements] for elements in new]
		children = []
		for element in selected_labels:
			children.append(models[element])
		model_plots.children = children
	created_models_checkbox.on_click(show_hide_plots)

	# Creación del layout inicial de la interfaz
	model_plots = column([])
	initialize = True
	for model in created_models:
		prediction_callback(model=model)
	initialize = False
	# Creación del layout estático de la interfaz
	l = layout([
		[prediction_plot],
		[outlier_plot],
		[simulation_title],
		[model_select_wb, column(created_models_wb, delete_model_button, sizing_mode='stretch_width')],		
		[model_plots]
	], sizing_mode='stretch_both')

	doc.add_root(l)
