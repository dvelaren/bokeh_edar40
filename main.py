import json
import logging
import os
import pickle
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import Popen
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from bokeh.embed import server_document
from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from pandas.io.json import json_normalize
from tornado.log import enable_pretty_logging

from bokeh_edar40.server import bk_worker
from parser_edar40.app import parser
from parser_edar40.common.constants import LATEST_DATE_FILE
from utils.rapidminer_proxy import call_webservice
from utils.server_config import *

enable_pretty_logging()


# import pam

# Import Scheduler
sched = BackgroundScheduler(daemon=True)
sched.add_job(parser, 'cron', day_of_week='mon-sun', hour=5, minute=00)
# sched.add_job(parser,'interval',seconds=2000)
sched.start()

app = Flask(__name__)
periodo = '2'
tipo_var = 'rend'
periodo_custom_start = '01-05-2018'
periodo_custom_end = ''


# Configuración de secret key y logging cuando ejecutamos sobre Gunicorn

if __name__ != '__main__':
    # parser() # Ejecutamos cuando se lanza la aplicación el parser
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


@app.route('/recreatedb')
def recreate_db():
    if 'username' in session:
        username = str(session.get('username'))
        if username == 'rapidminer':
            METEO_PERIOD_2_FILE = Path('./data/METEO_PERIOD_2.xlsx')
            if os.path.isfile(METEO_PERIOD_2_FILE):
                os.remove(METEO_PERIOD_2_FILE)
                print(f'Eliminando {METEO_PERIOD_2_FILE}')

            if os.path.isfile(LATEST_DATE_FILE):
                os.remove(LATEST_DATE_FILE)
                print(f'Eliminando {LATEST_DATE_FILE}')

            RESOURCES_FOLDER = Path('./resources')
            CARTUJA_DATOS_FOLDER = Path('./Cartuja_Datos/')

            model_files = ['created_models.pkl', 'total_model_dict.pkl']
            cartuja_datos_files = [
                f.name for f in os.scandir(CARTUJA_DATOS_FOLDER)]

            for file in model_files:
                file_path = os.path.join(RESOURCES_FOLDER, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f'Eliminando {file_path}')

            for file in cartuja_datos_files:
                file_path = os.path.join(CARTUJA_DATOS_FOLDER, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f'Eliminando {file_path}')

            parser(recreate=True)
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
            return redirect(url_for('index'))
        else:
            flash('Login incorrecto, inténtalo otra vez')
    return render_template('login.html', active_page=active_page)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'username' in session:
        global periodo
        global tipo_var
        global periodo_custom_start
        global periodo_custom_end
        active_page = 'perfil'
        if request.method == 'POST':
            periodo = request.form['periodo']
            tipo_var = request.form['tipo_var']
            periodo_custom_start = request.form['hiddenStartDate']
            periodo_custom_end = request.form['hiddenEndDate']

        print(f'periodo_sel: {periodo}, tipo_var_sel: {tipo_var}, custom_start: {periodo_custom_start} ')
        username = str(session.get('username'))
        if username == 'rapidminer':
            current_date = datetime.now().date() - timedelta(days=1)
            try:
                current_date = pickle.load(open(LATEST_DATE_FILE, "rb"))
            except:
                print("Cannot load current date")
            current_date = current_date.strftime("%d/%m/%Y")
            # For Production
            script = server_document(url=r'/bokeh/perfil', relative_urls=True,
                                     arguments={'periodo': periodo, 'tipo_var': tipo_var, 'periodo_custom_start': periodo_custom_start, 'periodo_custom_end': periodo_custom_end})
            # For Development
            # script = server_document(f'http://{SERVER_IP}:9090/bokeh/perfil',
            #                          arguments={'periodo': periodo, 'tipo_var': tipo_var, 'periodo_custom_start': periodo_custom_start, 'periodo_custom_end': periodo_custom_end})
            if tipo_var == 'abs':
                tipo_var_title = 'Absolutas'
            elif tipo_var == 'rend':
                tipo_var_title = 'Rendimientos'
            title = f'Calidad del Agua - Periodo {periodo} [{tipo_var_title}]'

            return render_template('cartuja.html',
                                   script=script,
                                   active_page=active_page,
                                   title=title, periodo=periodo,
                                   tipo_var=tipo_var,
                                   current_date=current_date,
                                   periodo_custom_start=periodo_custom_start,
                                   periodo_custom_end=periodo_custom_end)
    return redirect(url_for('login'))

# Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.


@app.route('/prediccion', methods=['GET', 'POST'])
def cartuja_prediction():
    if 'username' in session:
        global periodo
        global tipo_var
        global periodo_custom_start
        global periodo_custom_end
        active_page = 'prediccion'
        if request.method == 'POST':
            periodo = request.form['periodo']
            tipo_var = request.form['tipo_var']
            periodo_custom_start = request.form['hiddenStartDate']
            periodo_custom_end = request.form['hiddenEndDate']
        print(f'periodo_sel: {periodo}, tipo_var_sel: {tipo_var}, custom_start: {periodo_custom_start} ')
        username = str(session.get('username'))
        if username == 'rapidminer':
            current_date = datetime.now().date() - timedelta(days=1)
            try:
                current_date = pickle.load(open(LATEST_DATE_FILE, "rb"))
            except:
                print("Cannot load current date")
            current_date = current_date.strftime("%d/%m/%Y")
            # For Production
            script = server_document(url=r'/bokeh/prediccion', relative_urls=True,
                                     arguments={'periodo': periodo, 'tipo_var': tipo_var, 'periodo_custom_start': periodo_custom_start, 'periodo_custom_end': periodo_custom_end, 'current_date': current_date})
            # For Development
            # script = server_document(f'http://{SERVER_IP}:9090/bokeh/prediccion',
			# 						 arguments={'periodo': periodo, 'tipo_var': tipo_var, 'periodo_custom_start': periodo_custom_start, 'periodo_custom_end': periodo_custom_end, 'current_date': current_date})
            if tipo_var == 'abs':
                tipo_var_title = 'Absolutas'
            elif tipo_var == 'rend':
                tipo_var_title = 'Rendimientos'
            title = f'Predicción de Calidad del Agua - Periodo {periodo} [{tipo_var_title}]'
            
            return render_template('cartuja.html',
                                   script=script,
                                   active_page=active_page,
                                   title=title, periodo=periodo,
                                   tipo_var=tipo_var,
                                   current_date=current_date,
                                   periodo_custom_start=periodo_custom_start,
                                   periodo_custom_end=periodo_custom_end)
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
        arg_target = {'variable': target,
                      'valor': valores[0], 'objetivo': 'max'}
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
            var_influyentes = OrderedDict(
                {var: var_influyentes[var] for var in var_order})
            arg_target = session['arg_target']
            restricciones = session['restricciones']
            pred = session['pred']
            conf = session['conf']

    if request.method == 'POST':
        target_form = request.form['target']
        vars_form = {}
        vars_form.update({var: {'condicion': request.form[f'Condicion1_{var}'],
                                'valor': request.form[f'Valor1_{var}']} for var in var_influyentes})
        print(f'target: {target_form}')
        print(vars_form)
        arg_target = {'variable': target,
                      'valor': target_form, 'objetivo': 'max'}
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
                                     password='Edar2021*',
                                     parameters={'Target': str(
                                         arg_target), 'Restricciones': str(restricciones)},
                                     out_json=True)
        df_optim = json_normalize(json_optim)
        print(df_optim)
        for var in var_influyentes:
            var_influyentes[var]['result'] = df_optim[var][0]
            session['data']['var_influyentes'][var]['result'] = df_optim[var][0]
            print(f"{var}: {var_influyentes[var]['result']}")
        pred = df_optim[f'prediction({target})'][0]
        conf = round(df_optim[f'confidence({pred})'][0]*100, 3)
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
    return send_from_directory('Cartuja_Datos/', filename)


# Configuración cuando ejecutamos unicamente Flask sin Gunicorn, en modo de prueba
if __name__ == '__main__':
    # parser() # Ejecutamos cuando se lanza la aplicación el parser
    app.secret_key = '[]V\xf0\xed\r\x84L,p\xc59n\x98\xbc\x92'
    app.run(port=9995, debug=False, host='0.0.0.0')
