import unicodedata

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from flaskr.auth import admin_required, login_required
from flaskr.db import get_db

bp = Blueprint('student', __name__)


def _norm(text):
    """Strip accents and lowercase for email generation."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ── Main view ────────────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    db = get_db()
    periodos = db.execute(
        'SELECT id, name, year FROM periodo ORDER BY year'
    ).fetchall()
    return render_template('student/index.html', periodos=periodos)


# ── Filter APIs ──────────────────────────────────────────────────────────────

@bp.route('/api/semestres')
def api_semestres():
    periodo_id = request.args.get('periodo_id', type=int)
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT semester FROM student WHERE periodo_id = ? ORDER BY semester',
        (periodo_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/turnos')
def api_turnos():
    periodo_id = request.args.get('periodo_id', type=int)
    semester   = request.args.get('semester', type=int)
    db = get_db()
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
def api_grupos():
    periodo_id = request.args.get('periodo_id', type=int)
    semester   = request.args.get('semester', type=int)
    turno_id   = request.args.get('turno_id', type=int)
    db = get_db()
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


@bp.route('/api/clases')
def api_clases():
    semester = request.args.get('semester', type=int)
    db = get_db()
    rows = db.execute(
        'SELECT id, name FROM class WHERE semester = ? ORDER BY name',
        (semester,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route('/api/students')
def api_students():
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
        query = (
            'SELECT DISTINCT st.id, st.name, st.lastname, st.semester,'
            ' sw.name AS turno, g.name AS grupo'
            ' FROM student st'
            ' JOIN "group" g ON st.group_id = g.id'
            ' JOIN swift_group sg ON g.id = sg.group_id'
            ' JOIN swift sw ON sg.swift_id = sw.id'
            ' WHERE st.periodo_id = ? AND st.semester = ?'
        )

    if turno_id:
        query += ' AND sw.id = ?'
        params.append(turno_id)
    if grupo_id:
        query += ' AND g.id = ?'
        params.append(grupo_id)

    query += ' ORDER BY g.name, st.name, st.lastname'
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


# ── Student detail / edit ────────────────────────────────────────────────────

@bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def api_get_student(student_id):
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
    data = request.get_json()
    db = get_db()

    if g.user['role'] == 'admin' and 'group_id' in data:
        db.execute(
            'UPDATE student SET name=?, lastname=?, group_id=? WHERE id=?',
            (data['name'], data['lastname'], data['group_id'], student_id)
        )
    else:
        db.execute(
            'UPDATE student SET name=?, lastname=? WHERE id=?',
            (data['name'], data['lastname'], student_id)
        )

    if data.get('class_id') and data.get('grade') is not None:
        db.execute(
            'UPDATE student_group_class SET grade=? WHERE student_id=? AND class_id=?',
            (data['grade'], student_id, data['class_id'])
        )
    db.commit()
    return jsonify({'ok': True})


# ── Register student ─────────────────────────────────────────────────────────

@bp.route('/register-student', methods=['GET', 'POST'])
@admin_required
def register_student():
    db = get_db()

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        lastname  = request.form.get('lastname', '').strip()
        periodo_id = request.form.get('periodo_id', type=int)
        semester   = request.form.get('semester', type=int)
        group_id   = request.form.get('group_id', type=int)
        error = None

        if not name:
            error = 'El nombre es requerido.'
        elif not lastname:
            error = 'El apellido es requerido.'
        elif not periodo_id or not semester or not group_id:
            error = 'Selecciona periodo, semestre y grupo.'

        if error is None:
            email = f"{_norm(name)}.{_norm(lastname)}"
            db.execute(
                'INSERT INTO student (name, lastname, email, semester, group_id, periodo_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (name, lastname, email, semester, group_id, periodo_id)
            )
            student_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            classes = db.execute(
                'SELECT id FROM class WHERE semester = ?', (semester,)
            ).fetchall()
            for cls in classes:
                grade = request.form.get(f'grade_{cls["id"]}', 5, type=int)
                grade = max(5, min(10, grade))
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


# ── Groups ────────────────────────────────────────────────────────────────────

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
                db.execute('INSERT INTO "group" (name) VALUES (?)', (name,))
                gid = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                db.execute(
                    'INSERT INTO swift_group (swift_id, group_id) VALUES (?, ?)',
                    (swift_id, gid)
                )
                db.commit()
                flash(f'Grupo {name.upper()} registrado.')
            except Exception as e:
                flash(f'Error: {e}')
        return redirect(url_for('student.groups'))

    all_groups = db.execute(
        'SELECT g.id, g.name, s.name AS turno'
        ' FROM "group" g'
        ' JOIN swift_group sg ON g.id = sg.group_id'
        ' JOIN swift s ON sg.swift_id = s.id'
        ' ORDER BY s.name, g.name'
    ).fetchall()
    swifts = db.execute('SELECT id, name FROM swift ORDER BY name').fetchall()
    return render_template('student/groups.html', groups=all_groups, swifts=swifts)


# ── Classes ───────────────────────────────────────────────────────────────────

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

    all_classes = db.execute(
        'SELECT id, name, semester FROM class ORDER BY semester, name'
    ).fetchall()
    return render_template('student/classes.html', classes=all_classes)


# ── Shifts ────────────────────────────────────────────────────────────────────

@bp.route('/shifts', methods=['GET', 'POST'])
@admin_required
def shifts():
    db = get_db()

    if request.method == 'POST':
        name = request.form.get('name', '').strip().upper()
        if not name:
            flash('El nombre del turno es requerido.')
        else:
            db.execute('INSERT INTO swift (name) VALUES (?)', (name,))
            db.commit()
            flash(f'Turno {name} registrado.')
        return redirect(url_for('student.shifts'))

    all_shifts = db.execute('SELECT id, name FROM swift ORDER BY name').fetchall()
    return render_template('student/shifts.html', shifts=all_shifts)
