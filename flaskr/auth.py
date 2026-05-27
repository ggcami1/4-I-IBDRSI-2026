import base64
import functools
import io
import secrets

import pyotp
import qrcode
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    db = get_db()
    user_count = db.execute('SELECT COUNT(*) FROM user').fetchone()[0]

    # Allow access only if no users exist yet OR logged-in admin
    if user_count > 0:
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['role'] != 'admin':
            flash('Solo administradores pueden registrar nuevos usuarios.')
            return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # First-ever user is always admin; afterwards respect the form value
        role = 'admin' if user_count == 0 else request.form.get('role', 'teacher')
        error = None

        if not username:
            error = 'El nombre de usuario es requerido.'
        elif not password:
            error = 'La contraseña es requerida.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), role),
                )
                db.commit()
            except db.IntegrityError:
                error = f"El usuario {username} ya está registrado."
            else:
                flash(f"Usuario {username} registrado como {role}.")
                return redirect(url_for('auth.register') if g.user else url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html', first_user=(user_count == 0))


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

        if user is None:
            error = 'Usuario incorrecto.'
        elif not check_password_hash(user['password'], password):
            error = 'Contraseña incorrecta.'

        if error is None:
            session.clear()
            if user['totp_enabled']:
                session['pending_user_id'] = user['id']
                return redirect(url_for('auth.verify_2fa'))
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['role'] != 'admin':
            flash('Se requieren permisos de administrador.')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view


# ── 2FA Login Verification ───────────────────────────────────────────────────

@bp.route('/verify-2fa', methods=('GET', 'POST'))
def verify_2fa():
    pending_id = session.get('pending_user_id')
    if not pending_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form['code'].strip()
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id = ?', (pending_id,)).fetchone()

        if _check_code(db, user, code):
            session.pop('pending_user_id', None)
            session['user_id'] = pending_id
            return redirect(url_for('index'))

        flash('Código inválido.')

    return render_template('auth/verify_2fa.html')


# ── 2FA Setup ────────────────────────────────────────────────────────────────

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

        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            flash('Código inválido. Por favor intenta de nuevo.')
            return redirect(url_for('auth.setup_2fa'))

        db.execute(
            'UPDATE user SET totp_secret=?, totp_enabled=1 WHERE id=?',
            (secret, user['id'])
        )
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
        for raw in backup_codes:
            db.execute(
                'INSERT INTO backup_code (user_id, code) VALUES (?, ?)',
                (user['id'], generate_password_hash(raw))
            )
        db.commit()
        session.pop('totp_setup_secret', None)
        return render_template('auth/backup_codes.html', codes=backup_codes)

    secret = session.get('totp_setup_secret') or pyotp.random_base32()
    session['totp_setup_secret'] = secret

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=user['username'], issuer_name='Sistema de Calificaciones'
    )
    buf = io.BytesIO()
    qrcode.make(uri).save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render_template('auth/setup_2fa.html', qr_b64=qr_b64, secret=secret)


# ── Password Recovery ────────────────────────────────────────────────────────

@bp.route('/recover', methods=('GET', 'POST'))
def recover():
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
            session['recover_user_id'] = user['id']
            return redirect(url_for('auth.reset_password'))

    return render_template('auth/recover.html')


@bp.route('/reset-password', methods=('GET', 'POST'))
def reset_password():
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
            db.execute(
                'UPDATE user SET password=? WHERE id=?',
                (generate_password_hash(password), user_id)
            )
            db.commit()
            session.pop('recover_user_id', None)
            flash('Contraseña actualizada. Por favor inicia sesión.')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


# ── Helper ────────────────────────────────────────────────────────────────────

def _check_code(db, user, code):
    """Verify a TOTP code or an unused backup code. Marks backup codes used."""
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
