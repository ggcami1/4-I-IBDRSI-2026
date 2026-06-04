# Módulo de acceso a la base de datos.
# Gestiona una conexión SQLite por solicitud HTTP, registra la función UDF
# current_audit_user() usada por los triggers de auditoría, y expone el
# comando CLI 'flask init-db' para inicializar o reiniciar el esquema.

import sqlite3
import threading
from datetime import datetime

import click
from flask import current_app, g

# Almacenamiento local por hilo: cada solicitud concurrente tiene su propio
# nombre de usuario para que los triggers de auditoría lo lean de forma segura.
_audit_tls = threading.local()


def _current_audit_user():
    # Función registrada como UDF en SQLite con el nombre 'current_audit_user'.
    # Los triggers de auditoría la invocan para saber qué usuario provocó el cambio.
    return getattr(_audit_tls, 'username', 'sistema')


def set_audit_user(username: str):
    # Establece el usuario activo en el hilo actual antes de ejecutar
    # cualquier INSERT/UPDATE/DELETE sobre tablas auditadas.
    _audit_tls.username = username


def get_db():
    # Devuelve la conexión a la BD del contexto de la solicitud actual.
    # Si todavía no existe, la crea y registra la UDF de auditoría.
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # Las filas se acceden como diccionarios

        # Registra la función Python como función SQL disponible en esta conexión.
        # Los triggers usan: current_audit_user()
        g.db.create_function('current_audit_user', 0, _current_audit_user)

    return g.db


def close_db(e=None):
    # Cierra la conexión al final de cada solicitud HTTP para liberar recursos.
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    # Lee y ejecuta schema.sql: elimina todas las tablas existentes,
    # recrea el esquema completo y carga los datos semilla.
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    # Comando disponible como: flask --app flaskr init-db
    # Útil para desarrollo y despliegues iniciales.
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


# Conversor para columnas declaradas como TIMESTAMP:
# SQLite las guarda como texto ISO-8601; esto las convierte a datetime de Python.
sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app):
    # Engancha close_db al ciclo de vida de la app y añade el comando init-db al CLI.
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
