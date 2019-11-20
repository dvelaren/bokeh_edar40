import pandas as pd
import requests
import json

def call_webservice(url, username, password, parameters=None, out_json=False):
	"""Función que llama una URL con el método GET y retorna un JSON con la respuesta de la URL
	Parameters:
		url: endpoint a llamar
		username: Nombre de usuario
		password: Contraseña
		parameters: Parametros en JSON a enviar al endpoint
		out_json: Tipo de respuesta esperada del servidor, si es True el server devuelve un JSON, sinó es un texto
	
	Returns:
		document: Documento en JSON o texto plano con la respuesta del servidor
	"""
	r = requests.get(url, params=parameters, auth=(username, password))
	if out_json:
		document = json.loads(r.text)
	else:
		document = r.text
	return document