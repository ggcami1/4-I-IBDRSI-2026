# Módulo de gestión de alumnos.
# Expone la vista principal con filtros en cascada, las APIs JSON que alimentan
# esos filtros, el detalle y edición de alumnos, y las rutas administrativas
# para registrar alumnos, grupos, clases y turnos.

import unicodedata

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from flaskr.auth import admin_required, login_required
from flaskr.db import get_db, set_audit_user

bp = Blueprint('student', __name__)


def _norm(text):
    # Elimina acentos y convierte a minúsculas para generar el correo del alumno.
    # Ejemplo: "María" → "maria"
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _set_audit_user():
    # Registra el usuario de la sesión actual en el almacenamiento por hilo
    # para que los triggers de auditoría puedan identificar al actor del cambio.
    set_audit_user(g.user['username'])


# ── Vista principal ───────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    # Carga los periodos para el primer dropdown.
    # Para docentes, solo muestra periodos donde tienen alumnos asignados.
    db = get_db()
    if g.user['rol'] == 'docente':
        # Periodos donde el docente tiene planeaciones asignadas.
        periodos = db.execute(
            'SELECT DISTINCT p.id, p.name, p.year FROM periodo p'
            ' JOIN planeaciones pl ON pl.periodo_escolar = p.id'
            ' WHERE pl.id_docente = ? ORDER BY p.year',
            (g.user['id'],)
        ).fetchall()
    else:
        periodos = db.execute(
            'SELECT id, name, year FROM periodo ORDER BY year'
        ).fetchall()
    return render_template('student/index.html', periodos=periodos)


# ── APIs de filtros en cascada ────────────────────────────────────────────────

@bp.route('/api/semestres')
@login_required
def api_semestres():
    # Devuelve los semestres que existen para un periodo dado.
    # Para docentes, solo los semestres de sus clases asignadas.
    periodo_id = request.args.get('periodo_id', type=int)
    db = get_db()
    if g.user['rol'] == 'docente':
        # Semestres de las clases que el docente imparte en este periodo.
        rows = db.execute(
            'SELECT DISTINCT c.semester FROM class c'
            ' JOIN planeaciones pl ON pl.id_materia = c.id'
            ' WHERE pl.id_docente = ? AND pl.periodo_escolar = ?'
            ' ORDER BY c.semester',
            (g.user['id'], periodo_id)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT DISTINCT semester FROM student WHERE periodo_id = ? ORDER BY semester',
            (periodo_id,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/turnos')
@login_required
def api_turnos():
    # Devuelve los turnos disponibles para un periodo y semestre.
    # Para docentes, solo los turnos de grupos con sus alumnos asignados.
    periodo_id = request.args.get('periodo_id', type=int)
    semester   = request.args.get('semester', type=int)
    db = get_db()
    if g.user['rol'] == 'docente':
        # Turnos de los grupos en los que el docente tiene clases asignadas.
        rows = db.execute(
            'SELECT DISTINCT s.id, s.name FROM swift s'
            ' JOIN swift_group sg ON s.id = sg.swift_id'
            ' JOIN planeaciones pl ON sg.group_id = pl.id_grupo'
            ' JOIN class c ON pl.id_materia = c.id'
            ' WHERE pl.id_docente = ? AND pl.periodo_escolar = ? AND c.semester = ?'
            ' ORDER BY s.name',
            (g.user['id'], periodo_id, semester)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT DISTINCT s.id, s.name'
            ' FROM swift s'
            ' JOIN swift_group sg ON s.id = sg.swift_id'
            ' JOIN student st ON sg.group_id = st.group_id'
            ' WHERE st.periodo_id = ? AND st.semester = ?'
            ' ORDER BY s.name',
            (periodo_id, semester)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/grupos')
@login_required
def api_grupos():
    # Devuelve los grupos filtrados por periodo, semestre y turno.
    # Para docentes, solo los grupos que contienen sus alumnos asignados.
    periodo_id = request.args.get('periodo_id', type=int)
    semester   = request.args.get('semester', type=int)
    turno_id   = request.args.get('turno_id', type=int)
    db = get_db()
    if g.user['rol'] == 'docente':
        # Grupos en los que el docente imparte clases en este periodo/semestre/turno.
        rows = db.execute(
            'SELECT DISTINCT g.id, g.name FROM "group" g'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN planeaciones pl ON g.id = pl.id_grupo'
            ' JOIN class c ON pl.id_materia = c.id'
            ' WHERE pl.id_docente = ? AND pl.periodo_escolar = ? AND c.semester = ?'
            ' AND sg.swift_id = ? ORDER BY g.name',
            (g.user['id'], periodo_id, semester, turno_id)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT DISTINCT g.id, g.name'
            ' FROM "group" g'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN student st ON g.id = st.group_id'
            ' WHERE st.periodo_id = ? AND st.semester = ? AND sg.swift_id = ?'
            ' ORDER BY g.name',
            (periodo_id, semester, turno_id)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/materias')
@login_required
def api_materias():
    # Devuelve las clases cuyo semestre existe en el periodo solicitado.
    # Así Periodo 2026 (que solo tiene sems 2, 4, 6) solo muestra esas materias.
    periodo_id = request.args.get('periodo_id', type=int)
    if not periodo_id:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        'SELECT c.id, c.name, c.semester FROM class c'
        ' WHERE c.semester IN ('
        '  SELECT DISTINCT semester FROM student WHERE periodo_id = ?'
        ' ) ORDER BY c.semester, c.name',
        (periodo_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/clases')
@login_required
def api_clases():
    # Devuelve las clases de un semestre.
    # Para docentes, filtra solo las clases que imparte según sus planeaciones.
    semester = request.args.get('semester', type=int)
    db = get_db()
    if g.user['rol'] == 'docente':
        rows = db.execute(
            'SELECT DISTINCT c.id, c.name FROM class c'
            ' JOIN planeaciones pl ON c.id = pl.id_materia'
            ' WHERE c.semester = ? AND pl.id_docente = ? ORDER BY c.name',
            (semester, g.user['id'])
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT id, name FROM class WHERE semester = ? ORDER BY name',
            (semester,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/students')
def api_students():
    # Devuelve la lista de alumnos según los filtros activos.
    # Periodo y semestre son obligatorios; turno, grupo y clase son opcionales.
    # Si se incluye clase, también devuelve el nombre de la clase y la calificación.
    periodo_id = request.args.get('periodo_id', type=int)
    semester   = request.args.get('semester', type=int)
    turno_id   = request.args.get('turno_id', type=int)
    grupo_id   = request.args.get('grupo_id', type=int)
    clase_id   = request.args.get('clase_id', type=int)

    if not periodo_id or not semester:
        return jsonify([])

    db = get_db()
    params = [periodo_id, semester]

    if clase_id:
        # Con clase seleccionada: incluye nombre de clase y calificación en el resultado.
        query = (
            'SELECT DISTINCT st.id, st.name, st.lastname, st.semester,'
            ' sw.name AS turno, g.name AS grupo, c.name AS clase, sgc.grade'
            ' FROM student st'
            ' JOIN "group" g ON st.group_id = g.id'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN swift sw ON sg.swift_id = sw.id'
            ' JOIN student_group_class sgc ON st.id = sgc.student_id'
            ' JOIN class c ON sgc.class_id = c.id'
            ' WHERE st.periodo_id = ? AND st.semester = ? AND c.id = ?'
        )
        params.append(clase_id)
    else:
        # Sin clase: listado general de alumnos con turno y grupo.
        query = (
            'SELECT DISTINCT st.id, st.name, st.lastname, st.semester,'
            ' sw.name AS turno, g.name AS grupo'
            ' FROM student st'
            ' JOIN "group" g ON st.group_id = g.id'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN swift sw ON sg.swift_id = sw.id'
            ' WHERE st.periodo_id = ? AND st.semester = ?'
        )

    # Filtros opcionales aplicados dinámicamente según lo que el usuario seleccionó.
    if turno_id:
        query += ' AND sw.id = ?'
        params.append(turno_id)
    if grupo_id:
        query += ' AND g.id = ?'
        params.append(grupo_id)

    # Los docentes solo ven alumnos de los grupos en los que tienen planeaciones.
    if g.user and g.user['rol'] == 'docente':
        query += (
            ' AND st.group_id IN ('
            '  SELECT pl.id_grupo FROM planeaciones pl'
            '  JOIN class c ON pl.id_materia = c.id'
            '  WHERE pl.id_docente = ? AND pl.periodo_escolar = ? AND c.semester = ?'
            ' )'
        )
        params.extend([g.user['id'], periodo_id, semester])

    query += ' ORDER BY g.name, st.name, st.lastname'
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


# ── Detalle y edición de alumno ───────────────────────────────────────────────

@bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def api_get_student(student_id):
    # Devuelve los datos de un alumno para poblar el modal de edición.
    # Si se pasa class_id, también devuelve la calificación en esa clase.
    class_id = request.args.get('class_id', type=int)
    db = get_db()
    if class_id:
        row = db.execute(
            'SELECT st.id, st.name, st.lastname, st.semester, st.group_id,'
            ' st.periodo_id, p.name AS periodo_name,'
            ' g.name AS grupo, sw.id AS turno_id, sw.name AS turno, sgc.grade'
            ' FROM student st'
            ' JOIN periodo p ON st.periodo_id = p.id'
            ' JOIN "group" g ON st.group_id = g.id'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN swift sw ON sg.swift_id = sw.id'
            ' JOIN student_group_class sgc ON st.id = sgc.student_id'
            ' WHERE st.id = ? AND sgc.class_id = ?',
            (student_id, class_id)
        ).fetchone()
    else:
        row = db.execute(
            'SELECT st.id, st.name, st.lastname, st.semester, st.group_id,'
            ' st.periodo_id, p.name AS periodo_name,'
            ' g.name AS grupo, sw.id AS turno_id, sw.name AS turno'
            ' FROM student st'
            ' JOIN periodo p ON st.periodo_id = p.id'
            ' JOIN "group" g ON st.group_id = g.id'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN swift sw ON sg.swift_id = sw.id'
            ' WHERE st.id = ?',
            (student_id,)
        ).fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))


@bp.route('/api/student/<int:student_id>', methods=['POST'])
@login_required
def api_update_student(student_id):
    # Actualiza los datos de un alumno desde el modal de edición.
    # Los administradores pueden cambiar también el grupo; los docentes solo nombre y calificación.
    data = request.get_json()
    db = get_db()

    if g.user['rol'] in ('admin', 'control_escolar') and 'group_id' in data:
        # El admin puede reasignar al alumno a otro grupo.
        db.execute(
            'UPDATE student SET name=?, lastname=?, group_id=? WHERE id=?',
            (data['name'], data['lastname'], data['group_id'], student_id)
        )
    else:
        # El docente solo puede editar el nombre del alumno.
        db.execute(
            'UPDATE student SET name=?, lastname=? WHERE id=?',
            (data['name'], data['lastname'], student_id)
        )

    if data.get('class_id') and data.get('grade') is not None:
        # Actualiza la calificación del alumno en la clase indicada.
        db.execute(
            'UPDATE student_group_class SET grade=? WHERE student_id=? AND class_id=?',
            (data['grade'], student_id, data['class_id'])
        )
    db.commit()
    return jsonify({'ok': True})


# ── Eliminar alumno ──────────────────────────────────────────────────────────

@bp.route('/api/student/<int:student_id>/delete', methods=['POST'])
@admin_required
def api_delete_student(student_id):
    db = get_db()
    # Elimina primero las calificaciones para respetar la clave foránea.
    db.execute('DELETE FROM student_group_class WHERE student_id = ?', (student_id,))
    db.execute('DELETE FROM student WHERE id = ?', (student_id,))
    db.commit()
    return jsonify({'ok': True})


# ── Registro de nuevos alumnos ────────────────────────────────────────────────

@bp.route('/register-student', methods=['GET', 'POST'])
@admin_required
def register_student():
    db = get_db()

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        lastname   = request.form.get('lastname', '').strip()
        periodo_id = request.form.get('periodo_id', type=int)
        semester   = request.form.get('semester', type=int)
        group_id   = request.form.get('group_id', type=int)
        error = None

        # Valida que todos los campos obligatorios estén presentes.
        if not name:
            error = 'El nombre es requerido.'
        elif not lastname:
            error = 'El apellido es requerido.'
        elif not periodo_id or not semester or not group_id:
            error = 'Selecciona periodo, semestre y grupo.'

        if error is None:
            # Genera el correo a partir del nombre normalizado (sin acentos).
            email = f"{_norm(name)}.{_norm(lastname)}"
            db.execute(
                'INSERT INTO student (name, lastname, email, semester, group_id, periodo_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (name, lastname, email, semester, group_id, periodo_id)
            )
            student_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            # Crea un registro de calificación para cada clase del semestre.
            classes = db.execute(
                'SELECT id FROM class WHERE semester = ?', (semester,)
            ).fetchall()
            for cls in classes:
                grade = request.form.get(f'grade_{cls["id"]}', 5, type=int)
                grade = max(5, min(10, grade))  # Calificación válida entre 5 y 10
                db.execute(
                    'INSERT INTO student_group_class (student_id, group_id, class_id, grade)'
                    ' VALUES (?, ?, ?, ?)',
                    (student_id, group_id, cls['id'], grade)
                )
            db.commit()
            flash(f'Alumno {name} {lastname} registrado exitosamente.')
            return redirect(url_for('student.register_student'))

        flash(error)

    periodos = db.execute(
        'SELECT id, name, year FROM periodo ORDER BY year DESC'
    ).fetchall()
    swifts = db.execute('SELECT id, name FROM swift ORDER BY name').fetchall()
    return render_template('student/register_student.html',
                           periodos=periodos, swifts=swifts)


# ── API de edición y eliminación de grupos ───────────────────────────────────

@bp.route('/api/grupo/<int:grupo_id>', methods=['POST'])
@admin_required
def api_update_grupo(grupo_id):
    data = request.get_json()
    db = get_db()
    _set_audit_user()
    db.execute('UPDATE "group" SET name=? WHERE id=?',
               (data['name'].strip().lower(), grupo_id))
    # Actualiza el turno: reemplaza el registro en swift_group.
    db.execute('UPDATE swift_group SET swift_id=? WHERE group_id=?',
               (data['swift_id'], grupo_id))
    db.commit()
    return jsonify({'ok': True})


@bp.route('/api/grupo/<int:grupo_id>/delete', methods=['POST'])
@admin_required
def api_delete_grupo(grupo_id):
    db = get_db()
    # Previene la eliminación si el grupo tiene alumnos asignados.
    count = db.execute('SELECT COUNT(*) FROM student WHERE group_id = ?', (grupo_id,)).fetchone()[0]
    if count:
        return jsonify({'error': f'El grupo tiene {count} alumno(s) asignado(s) y no puede eliminarse.'}), 400
    _set_audit_user()
    db.execute('DELETE FROM swift_group WHERE group_id = ?', (grupo_id,))
    db.execute('DELETE FROM "group" WHERE id = ?', (grupo_id,))
    db.commit()
    return jsonify({'ok': True})


# ── API de edición y eliminación de clases ───────────────────────────────────

@bp.route('/api/clase/<int:clase_id>', methods=['POST'])
@admin_required
def api_update_clase(clase_id):
    data = request.get_json()
    db = get_db()
    db.execute('UPDATE class SET name=?, semester=? WHERE id=?',
               (data['name'], data['semester'], clase_id))
    db.commit()
    return jsonify({'ok': True})


@bp.route('/api/clase/<int:clase_id>/delete', methods=['POST'])
@admin_required
def api_delete_clase(clase_id):
    db = get_db()
    # Elimina primero las calificaciones vinculadas para respetar la clave foránea.
    db.execute('DELETE FROM student_group_class WHERE class_id = ?', (clase_id,))
    db.execute('DELETE FROM class WHERE id = ?', (clase_id,))
    db.commit()
    return jsonify({'ok': True})


# ── Gestión de grupos ─────────────────────────────────────────────────────────

@bp.route('/groups', methods=['GET', 'POST'])
@admin_required
def groups():
    db = get_db()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip().lower()
        swift_id = request.form.get('swift_id', type=int)
        if not name:
            flash('El nombre del grupo es requerido.')
        elif not swift_id:
            flash('Selecciona un turno.')
        else:
            try:
                # Registra el usuario en el hilo antes del INSERT para que el trigger
                # de auditoría pueda capturar quién creó el grupo.
                _set_audit_user()
                db.execute('INSERT INTO "group" (name) VALUES (?)', (name,))
                gid = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                # Asocia el grupo al turno seleccionado en la tabla de relación.
                db.execute(
                    'INSERT INTO swift_group (swift_id, group_id) VALUES (?, ?)',
                    (swift_id, gid)
                )
                db.commit()
                flash(f'Grupo {name.upper()} registrado.')
            except Exception as e:
                flash(f'Error: {e}')
        return redirect(url_for('student.groups'))

    # Carga todos los grupos con su turno asociado (incluyendo swift_id para el modal de edición).
    all_groups = db.execute(
        'SELECT g.id, g.name, s.id AS swift_id, s.name AS turno'
        ' FROM "group" g'
        ' JOIN swift_group sg ON g.id = sg.group_id'
        ' JOIN swift s ON sg.swift_id = s.id'
        ' ORDER BY s.name, g.name'
    ).fetchall()
    swifts = db.execute('SELECT id, name FROM swift ORDER BY name').fetchall()
    return render_template('student/groups.html', groups=all_groups, swifts=swifts)


# ── Gestión de clases ─────────────────────────────────────────────────────────

@bp.route('/classes', methods=['GET', 'POST'])
@admin_required
def classes():
    db = get_db()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        semester = request.form.get('semester', type=int)
        if not name:
            flash('El nombre de la clase es requerido.')
        elif not semester:
            flash('Selecciona un semestre.')
        else:
            db.execute('INSERT INTO class (name, semester) VALUES (?, ?)', (name, semester))
            db.commit()
            flash(f'Clase "{name}" registrada en semestre {semester}.')
        return redirect(url_for('student.classes'))

    # Ordena por semestre y luego por nombre para facilitar la lectura.
    all_classes = db.execute(
        'SELECT id, name, semester FROM class ORDER BY semester, name'
    ).fetchall()
    return render_template('student/classes.html', classes=all_classes)


# ── Gestión de turnos ─────────────────────────────────────────────────────────

@bp.route('/shifts', methods=['GET', 'POST'])
@admin_required
def shifts():
    db = get_db()

    if request.method == 'POST':
        name        = request.form.get('name',        '').strip().upper()
        hora_inicio = request.form.get('hora_inicio', '').strip()
        hora_fin    = request.form.get('hora_fin',    '').strip()
        if not name:
            flash('El nombre del turno es requerido.')
        elif not hora_inicio or not hora_fin:
            flash('Las horas de inicio y fin son requeridas.')
        else:
            db.execute('INSERT INTO swift (name, hora_inicio, hora_fin) VALUES (?, ?, ?)',
                       (name, hora_inicio, hora_fin))
            db.commit()
            flash(f'Turno {name} registrado.')
        return redirect(url_for('student.shifts'))

    all_shifts = db.execute('SELECT id, name, hora_inicio, hora_fin FROM swift ORDER BY name').fetchall()
    return render_template('student/shifts.html', shifts=all_shifts)


# ── API de edición y eliminación de turnos ───────────────────────────────────

@bp.route('/api/turno/<int:turno_id>', methods=['POST'])
@admin_required
def api_update_turno(turno_id):
    data = request.get_json()
    db = get_db()
    db.execute('UPDATE swift SET name=?, hora_inicio=?, hora_fin=? WHERE id=?',
               (data['name'].strip().upper(), data['hora_inicio'], data['hora_fin'], turno_id))
    db.commit()
    return jsonify({'ok': True})


@bp.route('/api/turno/<int:turno_id>/delete', methods=['POST'])
@admin_required
def api_delete_turno(turno_id):
    db = get_db()
    # Previene la eliminación si hay grupos asignados a este turno.
    count = db.execute('SELECT COUNT(*) FROM swift_group WHERE swift_id = ?', (turno_id,)).fetchone()[0]
    if count:
        return jsonify({'error': f'El turno tiene {count} grupo(s) asignado(s) y no puede eliminarse.'}), 400
    db.execute('DELETE FROM swift WHERE id = ?', (turno_id,))
    db.commit()
    return jsonify({'ok': True})


# ── Planeaciones ──────────────────────────────────────────────────────────────

@bp.route('/planeaciones')
@admin_required
def planeaciones():
    db = get_db()
    periodo_id = request.args.get('periodo_id', type=int)

    # Consulta base: trae todos los datos necesarios para mostrar en la tabla.
    base_query = (
        'SELECT pl.id, pr.name AS periodo, g.name AS grupo,'
        ' c.name AS materia, u.nombre || " " || u.apellido AS docente,'
        ' pl.dia_semana, pl.hora_inicio, pl.hora_fin, pl.aula, pl.observaciones,'
        ' pl.id_grupo, pl.id_materia, pl.id_docente, pl.periodo_escolar'
        ' FROM planeaciones pl'
        ' JOIN "group" g  ON pl.id_grupo        = g.id'
        ' JOIN class c    ON pl.id_materia       = c.id'
        ' JOIN user u     ON pl.id_docente       = u.id'
        ' JOIN periodo pr ON pl.periodo_escolar  = pr.id'
    )
    if periodo_id:
        rows = db.execute(base_query + ' WHERE pl.periodo_escolar = ?'
                          ' ORDER BY g.name, pl.dia_semana, pl.hora_inicio',
                          (periodo_id,)).fetchall()
    else:
        rows = db.execute(base_query +
                          ' ORDER BY pr.year DESC, g.name, pl.dia_semana, pl.hora_inicio').fetchall()

    grupos   = db.execute('SELECT g.id, g.name, s.name AS turno, s.hora_inicio, s.hora_fin'
                          ' FROM "group" g'
                          ' JOIN swift_group sg ON g.id = sg.group_id'
                          ' JOIN swift s ON sg.swift_id = s.id'
                          ' ORDER BY s.name, g.name').fetchall()
    docentes = db.execute(
        'SELECT id, nombre, apellido FROM user WHERE rol = ? ORDER BY nombre, apellido',
        ('docente',)
    ).fetchall()
    periodos = db.execute('SELECT id, name FROM periodo ORDER BY year DESC').fetchall()

    # Materias se cargan dinámicamente vía /api/materias según el periodo seleccionado.
    return render_template('student/planeaciones.html',
                           planeaciones=rows, grupos=grupos,
                           docentes=docentes, periodos=periodos,
                           periodo_id=periodo_id)


@bp.route('/api/planeacion/<int:plan_id>', methods=['GET'])
@login_required
def api_get_planeacion(plan_id):
    db = get_db()
    row = db.execute('SELECT * FROM planeaciones WHERE id = ?', (plan_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'No encontrado'}), 404
    return jsonify(dict(row))


@bp.route('/api/planeacion', methods=['POST'])
@admin_required
def api_create_planeacion():
    data = request.get_json()
    db = get_db()
    db.execute(
        'INSERT INTO planeaciones'
        ' (id_grupo, id_materia, id_docente, dia_semana,'
        '  hora_inicio, hora_fin, aula, periodo_escolar, observaciones)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (data['id_grupo'], data['id_materia'], data['id_docente'], data['dia_semana'],
         data['hora_inicio'], data['hora_fin'], data.get('aula', ''),
         data['periodo_escolar'], data.get('observaciones', ''))
    )
    db.commit()
    return jsonify({'ok': True})


@bp.route('/api/planeacion/<int:plan_id>', methods=['POST'])
@admin_required
def api_update_planeacion(plan_id):
    data = request.get_json()
    db = get_db()
    db.execute(
        'UPDATE planeaciones SET id_grupo=?, id_materia=?, id_docente=?,'
        ' dia_semana=?, hora_inicio=?, hora_fin=?, aula=?,'
        ' periodo_escolar=?, observaciones=? WHERE id=?',
        (data['id_grupo'], data['id_materia'], data['id_docente'], data['dia_semana'],
         data['hora_inicio'], data['hora_fin'], data.get('aula', ''),
         data['periodo_escolar'], data.get('observaciones', ''), plan_id)
    )
    db.commit()
    return jsonify({'ok': True})


@bp.route('/api/planeacion/<int:plan_id>/delete', methods=['POST'])
@admin_required
def api_delete_planeacion(plan_id):
    db = get_db()
    db.execute('DELETE FROM planeaciones WHERE id = ?', (plan_id,))
    db.commit()
    return jsonify({'ok': True})


# ── Mi Horario (vista exclusiva del docente) ──────────────────────────────────

@bp.route('/mi-horario')
@login_required
def mi_horario():
    # Los docentes solo pueden ver sus propias planeaciones.
    # Otros roles son redirigidos a la vista general de planeaciones.
    if g.user['rol'] != 'docente':
        return redirect(url_for('student.planeaciones'))

    db = get_db()
    # Orden canónico de días para mostrar el horario de lunes a sábado.
    DIA_ORDEN = {'lunes': 0, 'martes': 1, 'miercoles': 2,
                 'jueves': 3, 'viernes': 4, 'sabado': 5}

    rows = db.execute(
        'SELECT pl.id, pr.name AS periodo, g.name AS grupo,'
        ' c.name AS materia, pl.dia_semana, pl.hora_inicio, pl.hora_fin,'
        ' pl.aula, pl.observaciones'
        ' FROM planeaciones pl'
        ' JOIN "group" g  ON pl.id_grupo       = g.id'
        ' JOIN class c    ON pl.id_materia      = c.id'
        ' JOIN periodo pr ON pl.periodo_escolar = pr.id'
        ' WHERE pl.id_docente = ?'
        ' ORDER BY pr.year DESC, pl.hora_inicio',
        (g.user['id'],)
    ).fetchall()

    # Agrupa las planeaciones por día en el orden correcto de la semana.
    from collections import defaultdict
    por_dia = defaultdict(list)
    for r in rows:
        por_dia[r['dia_semana']].append(r)
    horario = sorted(por_dia.items(), key=lambda x: DIA_ORDEN.get(x[0], 9))

    return render_template('student/mi_horario.html', horario=horario)
