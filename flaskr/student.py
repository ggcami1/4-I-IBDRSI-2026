from flask import Blueprint, jsonify, render_template, request

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('student', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    periodos = db.execute(
        'SELECT id, name, year FROM periodo ORDER BY year'
    ).fetchall()
    return render_template('student/index.html', periodos=periodos)


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


@bp.route('/api/student/<int:student_id>', methods=['GET'])
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
def api_update_student(student_id):
    data = request.get_json()
    db = get_db()
    db.execute(
        'UPDATE student SET name=?, lastname=?, group_id=? WHERE id=?',
        (data['name'], data['lastname'], data['group_id'], student_id)
    )
    if data.get('class_id') and data.get('grade') is not None:
        db.execute(
            'UPDATE student_group_class SET grade=? WHERE student_id=? AND class_id=?',
            (data['grade'], student_id, data['class_id'])
        )
    db.commit()
    return jsonify({'ok': True})
