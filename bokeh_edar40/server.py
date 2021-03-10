from bokeh.server.server import Server
from tornado.ioloop import IOLoop
from utils.server_config import SERVER_IP

from bokeh_edar40.applications.cartuja.first_descriptive import \
    modify_first_descriptive
from bokeh_edar40.applications.cartuja.second_descriptive import \
    modify_second_descriptive


# Usamos localhost porque estamos probando la aplicación localmente, una vez ejecutando la aplicación sobre el servidor cambiamos la IP a la adecuada.
def bk_worker():
    # Prefix is very important... It is used for NGINX proxy inverse!
    kws = {'port': 9090, 'prefix': '/bokeh', 'allow_websocket_origin': ['*']}
    server = Server({'/perfil': modify_first_descriptive,
                     '/prediccion': modify_second_descriptive}, io_loop=IOLoop(), **kws)
    server.start()
    server.io_loop.start()
