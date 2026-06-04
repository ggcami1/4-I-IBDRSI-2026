# Módulo de autenticación.
# Gestiona el registro de usuarios, inicio y cierre de sesión,
# autenticación en dos pasos (TOTP) y recuperación de contraseña.

import base64
import functools
import io
import secrets
from datetime import datetime

import pyotp
import qrcode
from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Valores permitidos para el campo 'rol' del usuario.
# Se usan tanto en el CHECK de la BD como en el dropdown del formulario de registro,
# de modo que cambiar un rol aquí se refleja automáticamente en ambos lugares.
ROL_OPCIONES = [
    ('docente',         'Docente'),
    ('control_escolar', 'Control Escolar'),
    ('admin',           'Administrador'),
]


# ── Registro de usuarios ──────────────────────────────────────────────────────

@bp.route('/register', methods=('GET', 'POST'))
def register():
    db = get_db()
    user_count = db.execute('SELECT COUNT(*) FROM user').fetchone()[0]

    # Un usuario autenticado que no sea admin ni control_escolar no puede registrar usuarios.
    if user_count > 0 and g.user is not None and g.user['rol'] not in ('admin', 'control_escolar'):
        flash('Solo administradores pueden registrar nuevos usuarios.')
        return redirect(url_for('index'))

    # Solo el admin puede crear cuentas de administrador.
    # control_escolar y el registro público están limitados a docente/control_escolar.
    solo_admin_puede_crear_admin = g.user is not None and g.user['rol'] == 'admin'
    opciones = ROL_OPCIONES if solo_admin_puede_crear_admin else [o for o in ROL_OPCIONES if o[0] != 'admin']

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nombre   = request.form.get('nombre',   '').strip()
        apellido = request.form.get('apellido', '').strip()
        email    = request.form.get('email',    '').strip().lower()
        password = request.form.get('password', '')

        # Determina el rol de forma segura según quién está registrando.
        if user_count == 0:
            rol = 'admin'  # El primer usuario siempre es administrador.
        elif solo_admin_puede_crear_admin:
            rol = request.form.get('rol', 'docente')  # El admin elige libremente.
        else:
            # control_escolar y registro público: solo docente o control_escolar.
            # Se fuerza en el servidor aunque alguien manipule el formulario.
            rol = request.form.get('rol', 'docente')
            if rol not in ('docente', 'control_escolar'):
                rol = 'docente'
        error = None

        # Validaciones de campos obligatorios
        if not nombre:
            error = 'El nombre es requerido.'
        elif not apellido:
            error = 'El apellido es requerido.'
        elif not email:
            error = 'El correo electrónico es requerido.'
        elif not username:
            error = 'El nombre de usuario es requerido.'
        elif not password:
            error = 'La contraseña es requerida.'

        if error is None:
            try:
                # La contraseña se almacena hasheada, nunca en texto plano.
                db.execute(
                    "INSERT INTO user (username, nombre, apellido, email, password, rol)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (username, nombre, apellido, email, generate_password_hash(password), rol),
                )
                db.commit()
            except db.IntegrityError as e:
                # Distingue si el duplicado es el correo o el nombre de usuario.
                if 'user.email' in str(e):
                    error = f"El correo {email} ya está registrado."
                else:
                    error = f"El usuario {username} ya está registrado."
            else:
                flash(f"Usuario {username} registrado como {rol}.")
                # Si hay un admin logueado, regresa al formulario; si no, al login.
                return redirect(url_for('auth.register') if g.user else url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html', first_user=(user_count == 0),
                           rol_opciones=opciones)


# ── Helper de auditoría de accesos ───────────────────────────────────────────

def _log_login(username, evento, user_id=None):
    """Registra un evento de acceso (login / logout) en login_logs."""
    db = get_db()
    db.execute(
        'INSERT INTO login_logs (usuario, user_id, evento, ip) VALUES (?, ?, ?, ?)',
        (username, user_id, evento, request.remote_addr)
    )
    db.commit()


# ── Inicio de sesión ──────────────────────────────────────────────────────────

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        # Verifica que el usuario exista, que la contraseña sea correcta y que esté activo.
        if user is None:
            error = 'Usuario incorrecto.'
        elif not check_password_hash(user['password'], password):
            error = 'Contraseña incorrecta.'
        elif not user['activo']:
            error = 'Tu cuenta está desactivada. Contacta al administrador.'

        if error is None:
            session.clear()
            if user['totp_enabled']:
                # Si el usuario tiene 2FA activo, guarda su ID como pendiente
                # y redirige a la pantalla de verificación del código TOTP.
                session['pending_user_id'] = user['id']
                return redirect(url_for('auth.verify_2fa'))
            # Login exitoso sin 2FA.
            db.execute('UPDATE user SET ultimo_login=? WHERE id=?',
                       (datetime.now().isoformat(timespec='seconds'), user['id']))
            db.commit()
            _log_login(user['username'], 'LOGIN_OK', user['id'])
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        # Registra el intento fallido con el nombre de usuario proporcionado.
        _log_login(username, 'LOGIN_FALLIDO', user['id'] if user else None)
        flash(error)

    return render_template('auth/login.html')


# ── Carga del usuario en cada solicitud ───────────────────────────────────────

@bp.before_app_request
def load_logged_in_user():
    # Se ejecuta antes de cada ruta. Pone el usuario en g.user para que
    # todas las vistas y plantillas puedan acceder a él sin consultar la BD de nuevo.
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


# ── Cierre de sesión ──────────────────────────────────────────────────────────

@bp.route('/logout')
def logout():
    # Registra el cierre de sesión antes de limpiarla.
    if g.user:
        _log_login(g.user['username'], 'LOGOUT', g.user['id'])
    session.clear()
    return redirect(url_for('auth.login'))


# ── Decoradores de control de acceso ─────────────────────────────────────────

def login_required(view):
    # Decorador que protege rutas que requieren sesión activa.
    # Si no hay usuario logueado, redirige al login.
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    # Decorador que restringe el acceso a usuarios con rol 'admin' o 'control_escolar'.
    # Verifica primero que haya sesión y luego que el rol sea correcto.
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['rol'] not in ('admin', 'control_escolar'):
            flash('Se requieren permisos de administrador.')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view


# ── Verificación 2FA al iniciar sesión ────────────────────────────────────────

@bp.route('/verify-2fa', methods=('GET', 'POST'))
def verify_2fa():
    # La sesión contiene 'pending_user_id' mientras el usuario no haya completado el 2FA.
    pending_id = session.get('pending_user_id')
    if not pending_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form['code'].strip()
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id = ?', (pending_id,)).fetchone()

        # Acepta tanto un código TOTP vigente como un código de respaldo sin usar.
        if _check_code(db, user, code):
            db.execute('UPDATE user SET ultimo_login=? WHERE id=?',
                       (datetime.now().isoformat(timespec='seconds'), pending_id))
            db.commit()
            _log_login(user['username'], 'LOGIN_OK', pending_id)
            session.pop('pending_user_id', None)  # Elimina el estado pendiente
            session['user_id'] = pending_id        # Completa el inicio de sesión
            return redirect(url_for('index'))

        flash('Código inválido.')

    return render_template('auth/verify_2fa.html')


# ── Configuración de 2FA ──────────────────────────────────────────────────────

@bp.route('/setup-2fa', methods=('GET', 'POST'))
@login_required
def setup_2fa():
    db = get_db()
    user = g.user

    if request.method == 'POST':
        code = request.form['code'].strip()
        secret = session.get('totp_setup_secret')
        if not secret:
            flash('Sesión expirada. Por favor intenta de nuevo.')
            return redirect(url_for('auth.setup_2fa'))

        # Verifica que el código ingresado coincida con el secreto TOTP generado.
        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            flash('Código inválido. Por favor intenta de nuevo.')
            return redirect(url_for('auth.setup_2fa'))

        # Activa el 2FA guardando el secreto en la BD.
        db.execute(
            'UPDATE user SET totp_secret=?, totp_enabled=1 WHERE id=?',
            (secret, user['id'])
        )
        # Genera 8 códigos de respaldo de un solo uso y los guarda hasheados.
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
        for raw in backup_codes:
            db.execute(
                'INSERT INTO backup_code (user_id, code) VALUES (?, ?)',
                (user['id'], generate_password_hash(raw))
            )
        db.commit()
        session.pop('totp_setup_secret', None)
        # Muestra los códigos de respaldo al usuario; no se mostrarán de nuevo.
        return render_template('auth/backup_codes.html', codes=backup_codes)

    # En GET: genera (o reutiliza de la sesión) un secreto TOTP y produce el QR.
    secret = session.get('totp_setup_secret') or pyotp.random_base32()
    session['totp_setup_secret'] = secret

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=user['username'], issuer_name='Sistema de Control Escolar'
    )
    # Convierte la URI TOTP a imagen PNG codificada en base64 para incrustar en HTML.
    buf = io.BytesIO()
    qrcode.make(uri).save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template('auth/setup_2fa.html', qr_b64=qr_b64, secret=secret)


# ── Recuperación de contraseña ────────────────────────────────────────────────

@bp.route('/recover', methods=('GET', 'POST'))
def recover():
    # El usuario debe proporcionar su nombre de usuario y un código TOTP válido
    # para demostrar identidad sin necesitar la contraseña olvidada.
    if request.method == 'POST':
        username = request.form['username']
        code = request.form['code'].strip()
        db = get_db()
        user = db.execute(
            'SELECT * FROM user WHERE username=?', (username,)
        ).fetchone()

        error = None
        if user is None:
            error = 'Usuario no encontrado.'
        elif not user['totp_enabled']:
            error = 'Esta cuenta no tiene 2FA activado.'
        elif not _check_code(db, user, code):
            error = 'Código de autenticación inválido.'

        if error:
            flash(error)
        else:
            # Guarda el ID en sesión para que reset_password lo consuma.
            session['recover_user_id'] = user['id']
            return redirect(url_for('auth.reset_password'))

    return render_template('auth/recover.html')


@bp.route('/reset-password', methods=('GET', 'POST'))
def reset_password():
    # Solo accesible si recover() colocó 'recover_user_id' en la sesión.
    user_id = session.get('recover_user_id')
    if not user_id:
        return redirect(url_for('auth.recover'))

    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm']
        error = None

        if not password:
            error = 'La contraseña es requerida.'
        elif password != confirm:
            error = 'Las contraseñas no coinciden.'

        if error:
            flash(error)
        else:
            db = get_db()
            # Actualiza la contraseña hasheada y limpia el token de recuperación.
            db.execute(
                'UPDATE user SET password=? WHERE id=?',
                (generate_password_hash(password), user_id)
            )
            db.commit()
            session.pop('recover_user_id', None)
            flash('Contraseña actualizada. Por favor inicia sesión.')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


# ── Reporte de auditoría (solo admin) ────────────────────────────────────────

@bp.route('/auditoria')
@login_required
def auditoria():
    if g.user['rol'] != 'admin':
        flash('Se requieren permisos de administrador.')
        return redirect(url_for('index'))

    db       = get_db()
    tab      = request.args.get('tab', 'accesos')
    page     = max(1, request.args.get('page', 1, type=int))
    PER_PAGE = 15
    offset   = (page - 1) * PER_PAGE

    # Columnas permitidas por sección para evitar inyección SQL en ORDER BY.
    if tab == 'cambios':
        ALLOWED  = {'fecha', 'usuario', 'tabla_afectada', 'registro_id', 'accion'}
        col_def  = 'fecha'
        table    = 'audit_logs'
    else:
        ALLOWED  = {'fecha', 'usuario', 'evento', 'ip'}
        col_def  = 'fecha'
        table    = 'login_logs'

    sort_col   = request.args.get('sort', col_def)
    if sort_col not in ALLOWED:
        sort_col = col_def
    sort_order = request.args.get('order', 'desc')
    if sort_order not in ('asc', 'desc'):
        sort_order = 'desc'

    total = db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    rows  = db.execute(
        f'SELECT * FROM {table} ORDER BY {sort_col} {sort_order} LIMIT ? OFFSET ?',
        (PER_PAGE, offset)
    ).fetchall()

    return render_template('auth/auditoria.html',
                           tab=tab, rows=rows, total=total, page=page, per_page=PER_PAGE,
                           sort_col=sort_col, sort_order=sort_order)


# ── Diagramas ────────────────────────────────────────────────────────────────

@bp.route('/arquitectura')
@admin_required
def arquitectura():
    return render_template('auth/arquitectura.html')


# ── Gestión de usuarios ───────────────────────────────────────────────────────

@bp.route('/usuarios')
@admin_required
def usuarios():
    # Admin ve todos los usuarios; control_escolar solo ve docentes y control_escolar.
    db = get_db()
    if g.user['rol'] == 'admin':
        rows = db.execute(
            'SELECT id, username, nombre, apellido, email, rol, activo, ultimo_login'
            ' FROM user ORDER BY nombre, apellido'
        ).fetchall()
        opciones = ROL_OPCIONES
    else:
        rows = db.execute(
            'SELECT id, username, nombre, apellido, email, rol, activo, ultimo_login'
            ' FROM user WHERE rol != "admin" ORDER BY nombre, apellido'
        ).fetchall()
        opciones = [o for o in ROL_OPCIONES if o[0] != 'admin']
    return render_template('auth/usuarios.html', users=rows, rol_opciones=opciones)


@bp.route('/api/usuario/<int:user_id>', methods=['GET'])
@admin_required
def api_get_usuario(user_id):
    db = get_db()
    row = db.execute(
        'SELECT id, username, nombre, apellido, email, rol, activo FROM user WHERE id = ?',
        (user_id,)
    ).fetchone()
    if row is None:
        return jsonify({'error': 'No encontrado'}), 404
    # control_escolar no puede ver ni editar usuarios admin.
    if g.user['rol'] != 'admin' and row['rol'] == 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify(dict(row))


@bp.route('/api/usuario/<int:user_id>', methods=['POST'])
@admin_required
def api_update_usuario(user_id):
    # Actualiza los datos de un usuario desde el modal de edición.
    # El rol de un admin nunca puede cambiarse; control_escolar no puede asignar rol admin.
    data = request.get_json()
    db = get_db()
    row = db.execute('SELECT rol FROM user WHERE id = ?', (user_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'No encontrado'}), 404
    if g.user['rol'] != 'admin' and row['rol'] == 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    # El rol de un usuario admin nunca puede cambiarse.
    # control_escolar tampoco puede asignar el rol admin aunque manipule el JSON.
    if row['rol'] == 'admin':
        rol = 'admin'
    elif g.user['rol'] != 'admin':
        rol = data.get('rol', row['rol'])
        if rol == 'admin':
            rol = row['rol']
    else:
        rol = data.get('rol', row['rol'])

    try:
        db.execute(
            'UPDATE user SET nombre=?, apellido=?, email=?, username=?, rol=? WHERE id=?',
            (data['nombre'], data['apellido'], data['email'], data['username'], rol, user_id)
        )
        db.commit()
    except db.IntegrityError as e:
        if 'user.email' in str(e):
            return jsonify({'error': f"El correo {data['email']} ya está registrado."}), 400
        return jsonify({'error': f"El usuario {data['username']} ya está registrado."}), 400
    return jsonify({'ok': True})


@bp.route('/api/usuario/<int:user_id>/toggle', methods=['POST'])
@login_required
def api_toggle_usuario(user_id):
    # Solo el admin puede activar/desactivar cuentas.
    if g.user['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == g.user['id']:
        return jsonify({'error': 'No puedes desactivar tu propia cuenta.'}), 400
    db = get_db()
    # Invierte el valor de activo (0 → 1 ó 1 → 0) en una sola operación.
    db.execute('UPDATE user SET activo = 1 - activo WHERE id = ?', (user_id,))
    db.commit()
    nuevo = db.execute('SELECT activo FROM user WHERE id = ?', (user_id,)).fetchone()['activo']
    return jsonify({'ok': True, 'activo': nuevo})


@bp.route('/api/usuario/<int:user_id>/delete', methods=['POST'])
@login_required
def api_delete_usuario(user_id):
    # Solo el admin puede eliminar cuentas.
    if g.user['rol'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == g.user['id']:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta.'}), 400
    db = get_db()
    # Elimina primero los códigos de respaldo para respetar la clave foránea.
    db.execute('DELETE FROM backup_code WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM user WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'ok': True})


# ── Función auxiliar ──────────────────────────────────────────────────────────

def _check_code(db, user, code):
    # Verifica si el código es un TOTP vigente.
    # Si no, busca entre los códigos de respaldo sin usar del usuario.
    # Al usar un código de respaldo lo marca como consumido.
    if pyotp.TOTP(user['totp_secret']).verify(code, valid_window=1):
        return True
    for b in db.execute(
        'SELECT * FROM backup_code WHERE user_id=? AND used=0', (user['id'],)
    ).fetchall():
        if check_password_hash(b['code'], code):
            db.execute('UPDATE backup_code SET used=1 WHERE id=?', (b['id'],))
            db.commit()
            flash('Código de respaldo usado. Genera nuevos códigos pronto.')
            return True
    return False
