# Punto de entrada de la aplicación Flask.
# Contiene la función create_app() que configura la app, registra la base de datos
# y enlaza los blueprints de autenticación y gestión de alumnos.

import os

from flask import Flask


def create_app(test_config=None):
    # Crea la instancia de Flask; instance_relative_config permite leer config.py
    # desde la carpeta 'instance' sin incluirla en el repositorio.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',                                           # Cambiar por clave segura en producción
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'), # Ruta al archivo de base de datos SQLite
    )

    if test_config is None:
        # Carga configuración personalizada desde instance/config.py si existe
        app.config.from_pyfile('config.py', silent=True)
    else:
        # En pruebas, usa la configuración que se pasa directamente
        app.config.from_mapping(test_config)

    # Crea la carpeta 'instance' si aún no existe (necesaria para la BD)
    os.makedirs(app.instance_path, exist_ok=True)

    # Ruta de diagnóstico para verificar que el servidor responde
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    # Registra el módulo de base de datos y expone 'flask init-db'
    from . import db
    db.init_app(app)

    # Blueprint de autenticación: login, registro, 2FA y recuperación de contraseña
    from . import auth
    app.register_blueprint(auth.bp)

    # Blueprint de alumnos: vista principal, APIs de filtrado y gestión administrativa
    from . import student
    app.register_blueprint(student.bp)
    app.add_url_rule('/', endpoint='index')  # La raíz '/' apunta a student.index

    return app
