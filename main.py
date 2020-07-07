from flask import Flask, render_template, session, redirect, url_for, request, flash, send_from_directory
from utils.server_config import *
from utils.rapidminer_proxy import call_webservice
import json
from pandas.io.json import json_normalize
from collections import OrderedDict

import logging
from tornado.log import enable_pretty_logging
enable_pretty_logging()

from bokeh_edar40.server import bk_worker

from bokeh.embed import server_document

from threading import Thread

# import pam
from subprocess import Popen

# Import Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from parser_edar40.app import parser
sched = BackgroundScheduler(daemon=True)
sched.add_job(parser, 'cron', day_of_week='mon-sun', hour=5, minute=00)
# sched.add_job(parser,'interval',seconds=2000)
sched.start()

app = Flask(__name__)
periodo = '2'
tipo_var = 'rend'

#Configuración de secret key y logging cuando ejecutamos sobre Gunicorn

if __name__ != '__main__':
	formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	gunicorn_logger = logging.getLogger('gunicorn.error')
	gunicorn_logger.setLevel(logging.INFO)
	
	tornado_access_logger = logging.getLogger('tornado.access')
	tornado_access_logger.setLevel(logging.INFO)
	tornado_access_handler = logging.FileHandler('logs/error_log.log')
	tornado_access_handler.setFormatter(formatter)
	tornado_access_logger.addHandler(tornado_access_handler)

	tornado_application_logger = logging.getLogger('tornado.application')
	tornado_application_logger.setLevel(logging.INFO)
	tornado_application_handler = logging.FileHandler('logs/error_log.log')
	tornado_application_handler.setFormatter(formatter)
	tornado_application_logger.addHandler(tornado_application_handler)

	app.logger.addHandler(gunicorn_logger.handlers)
	app.logger.addHandler(tornado_access_logger.handlers)
	app.logger.addHandler(tornado_application_logger.handlers)
	app.logger.setLevel(logging.INFO)
	app.jinja_env.cache = {}

Thread(target=bk_worker).start()

@app.route('/', methods=['GET'])
def index():
	if 'username' in session:
		username = str(session.get('username'))
		if username == 'rapidminer':
			return redirect(url_for('perfil'))
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	active_page = 'login'
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		if str(username) == def_user and str(password) == def_pass:
			session['username'] = request.form['username']
			# next_page = request.args.get('next')
			# print(next_page)
			# return redirect(next_page) if next_page else redirect(url_for('index'))
			return redirect(url_for('index'))
		else:
			flash('Login incorrecto, inténtalo otra vez')
	return render_template('login.html', active_page=active_page)

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/perfil', methods=['GET', 'POST'])
# @app.route('/perfil/periodo1', methods=['GET', 'POST'])
def perfil():
	if 'username' in session:
		global periodo
		global tipo_var
		active_page = 'perfil'
		if request.method == 'POST':
			periodo = request.form['periodo']
			tipo_var = request.form['tipo_var']
		print(f'periodo_sel: {periodo}, tipo_var_sel: {tipo_var}')
		username = str(session.get('username'))
		if username == 'rapidminer':
			script = server_document(url=r'/bokeh/perfil', relative_urls=True, arguments={'periodo':periodo, 'tipo_var':tipo_var})
			# script = server_document(f'http://{SERVER_IP}:9090/bokeh/perfil', arguments={'periodo':periodo, 'tipo_var':tipo_var})
			if tipo_var == 'abs':
				tipo_var_title = 'Absolutas'
			elif tipo_var == 'rend':
				tipo_var_title = 'Rendimientos'
			title = f'Calidad del Agua - Periodo {periodo} [{tipo_var_title}]'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title, periodo=periodo, tipo_var=tipo_var)
	return redirect(url_for('login'))

#Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
@app.route('/prediccion', methods=['GET', 'POST'])
def cartuja_prediction():
	if 'username' in session:
		global periodo
		global tipo_var
		active_page = 'prediccion'
		if request.method == 'POST':
			periodo = request.form['periodo']
			tipo_var = request.form['tipo_var']
		print(f'periodo_sel: {periodo}, tipo_var_sel: {tipo_var}')
		username = str(session.get('username'))
		if username == 'rapidminer':
			script = server_document(url=r'/bokeh/prediccion', relative_urls=True, arguments={'periodo':periodo, 'tipo_var':tipo_var})
			# script = server_document(f'http://{SERVER_IP}:9090/bokeh/prediccion', arguments={'periodo':periodo, 'tipo_var':tipo_var})
			if tipo_var == 'abs':
				tipo_var_title = 'Absolutas'
			elif tipo_var == 'rend':
				tipo_var_title = 'Rendimientos'
			title = f'Predicción de Calidad del Agua - Periodo {periodo} [{tipo_var_title}]'
			return render_template('cartuja.html', script=script, active_page=active_page, title = title, periodo=periodo, tipo_var=tipo_var)
	return redirect(url_for('login'))

@app.route('/optimizacion', methods=['GET', 'POST'])
def optimizacion():
	try:
		data = json.loads(request.args['data'].replace("'", '"'))
		# print(f'rcv_data: {data}')
		target = data['target']
		valores = data['valores']
		var_influyentes = data['var_influyentes']
		session['data'] = data
		session['var_order'] = list(var_influyentes.keys())
		arg_target = {'variable':target, 'valor':valores[0], 'objetivo': 'max'}
		restricciones = {}
		session['arg_target'] = arg_target
		session['restricciones'] = restricciones
		pred = ''
		conf = ''
		session['pred'] = pred
		session['conf'] = conf
	except:
		if 'data' in session:
			target = session['data']['target']
			valores = session['data']['valores']
			var_influyentes = session['data']['var_influyentes']
			var_order = session['var_order']
			var_influyentes = OrderedDict({var:var_influyentes[var] for var in var_order})
			arg_target = session['arg_target']
			restricciones = session['restricciones']
			pred = session['pred']
			conf = session['conf']
		
	if request.method == 'POST':
		target_form = request.form['target']
		vars_form = {}
		vars_form.update({var:{'condicion':request.form[f'Condicion1_{var}'],'valor':request.form[f'Valor1_{var}']} for var in var_influyentes})
		print(f'target: {target_form}')
		print(vars_form)
		arg_target = {'variable':target, 'valor':target_form, 'objetivo': 'max'}
		restricciones = {}
		for var, obj in vars_form.items():
			if obj['condicion'] != '-':
				restricciones.update({var: obj['valor']})
		session['arg_target'] = arg_target
		session['restricciones'] = restricciones
		print(f'Target: {arg_target}')
		print(f'Restricciones: {restricciones}')
		json_optim = call_webservice(url='http://rapidminer.vicomtech.org/api/rest/process/EDAR_Cartuja_Optimizacion_v1?',
										username='rapidminer',
										password='rapidminer',
										parameters={'Target': str(arg_target), 'Restricciones': str(restricciones)},
										out_json=True)
		df_optim = json_normalize(json_optim)
		print(df_optim)
		for var in var_influyentes:
			var_influyentes[var]['result'] = df_optim[var][0]
			session['data']['var_influyentes'][var]['result'] = df_optim[var][0]
			print(f"{var}: {var_influyentes[var]['result']}")
		pred = df_optim[f'prediction({target})'][0]
		conf = round(df_optim[f'confidence({pred})'][0]*100,3)
		session['pred'] = pred
		session['conf'] = conf
	return render_template('optimizacion.html',
							target=target,
							valores=valores,
							var_influyentes=var_influyentes,
							arg_target=arg_target['valor'],
							restricciones=restricciones,
							pred=pred,
							conf=conf)

@app.route('/archivos/<path:filename>')
def send_js(filename):
    return send_from_directory('static/Cartuja_Datos/', filename)

#Configuración cuando ejecutamos unicamente Flask sin Gunicorn, en modo de prueba
if __name__ == '__main__':
	app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
	app.run(port=9995, debug=False, host='0.0.0.0')
