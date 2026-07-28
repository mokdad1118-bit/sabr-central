from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify, make_response
import sqlite3
import os
import io
import uuid
import base64
from functools import wraps
from urllib.parse import quote
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import init_db
from datetime import datetime
from certificate_utils import build_certificate_context
import qrcode

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["DATABASE"] = os.path.join(BASE_DIR, "database", "app.db")
DB_NAME = app.config["DATABASE"]

EXAM_RESULTS_UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "exam_results")
ALLOWED_EXAM_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
with app.app_context():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        conn.close()
    init_db()


def allowed_exam_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXAM_IMAGE_EXTENSIONS


def save_exam_result_image(student_id, image_file):
    os.makedirs(EXAM_RESULTS_UPLOAD_FOLDER, exist_ok=True)
    original_name = secure_filename(image_file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    filename = f"{student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    image_file.save(os.path.join(EXAM_RESULTS_UPLOAD_FOLDER, filename))
    return f"uploads/exam_results/{filename}"


OFFICIAL_SETTING_KEYS = ("quranic_halaqah_director", "endowments_director")
def file_to_data_uri(file_path):
    mime = "image/png"
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    elif ext == ".gif":
        mime = "image/gif"

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime};base64,{encoded}"

def get_certificate_officials(conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    officials = {key: "" for key in OFFICIAL_SETTING_KEYS}
    rows = conn.execute(
        f"SELECT key, value FROM system_settings WHERE key IN ({','.join('?' for _ in OFFICIAL_SETTING_KEYS)})",
        OFFICIAL_SETTING_KEYS,
    ).fetchall()
    for row in rows:
        officials[row["key"]] = row["value"]

    if close_conn:
        conn.close()
    return officials
def arabic_number_words(n):
    words = {
        1: "واحد",
        2: "اثنان",
        3: "ثلاثة",
        4: "أربعة",
        5: "الخمسة",
        6: "ستة",
        7: "سبعة",
        8: "ثمانية",
        9: "تسعة",
        10: "العشرة",
        11: "أحد عشر",
        12: "اثنا عشر",
        13: "ثلاثة عشر",
        14: "أربعة عشر",
        15: "الخمسة عشر",
        16: "ستة عشر",
        17: "سبعة عشر",
        18: "ثمانية عشر",
        19: "تسعة عشر",
        20: "العشرون",
        21: "واحد وعشرون",
        22: "اثنان وعشرون",
        23: "ثلاثة وعشرون",
        24: "أربعة وعشرون",
        25: "الخمسة والعشرون",
        26: "ستة وعشرون",
        27: "سبعة وعشرون",
        28: "ثمانية وعشرون",
        29: "تسعة وعشرون",
        30: "الثلاثون",
    }
    try:
        return words.get(int(n), str(n))
    except (ValueError, TypeError):
        return str(n)

def level_to_text(level):
    mapping = {
        "1-5": "الخمسة الأولى",
        "1-10": "العشرة",
        "1-15": "الخمسة عشر",
        "1-20": "العشرون",
        "1-25": "الخمسة والعشرون",
        "26-30": "الخمسة الأخيرة",
        "1-30": "القرآن كامل"
    }
    return mapping.get(level, str(level))
def save_certificate_officials(quranic_halaqah_director, endowments_director):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    values = {
        "quranic_halaqah_director": quranic_halaqah_director.strip(),
        "endowments_director": endowments_director.strip(),
    }
    for key, value in values.items():
        conn.execute(
            """
            INSERT INTO system_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def render_cert_pdf(html):
    from weasyprint import HTML
    return HTML(string=html, base_url=app.root_path).write_pdf()


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper
def admin_or_committee_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["admin", "committee_member"]:
            abort(403)
        return f(*args, **kwargs)
    return wrapper
def committee_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "committee_member":
            abort(403)
        return f(*args, **kwargs)
    return wrapper
def get_logged_committee_member(optional=False):
    user_id = session.get("user_id")

    if not user_id:
        if optional:
            return None
        abort(403)

    conn = get_db_connection()
    try:
        member = conn.execute("""
            SELECT cm.*, c.center_name
            FROM committee_members cm
            JOIN centers c ON cm.center_id = c.id
            WHERE cm.user_id = ?
        """, (user_id,)).fetchone()
        return member
    finally:
        conn.close()
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("الاسم وكلمة المرور مطلوبان", "error")
            return render_template("register.html")

        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()

        if user:
            conn.close()
            flash("اسم المستخدم موجود مسبقًا", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, "committee_member")
        )
        conn.commit()
        conn.close()

        flash("تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username, password, role FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("member_dashboard"))

        flash("بيانات الدخول غير صحيحة", "error")
        return render_template("login.html")

    return render_template("login.html")
import base64
import io

@app.route("/certificate/pdf/<int:student_id>/<int:exam_id>")
def certificate_pdf(student_id, exam_id):
    conn = get_db_connection()
    try:
        student = conn.execute("""
            SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                   cm.full_name AS committee_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            JOIN committee_members cm ON s.committee_member_id = cm.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()

        if not student:
            abort(404)

        exam = conn.execute("""
            SELECT *
            FROM exam_records
            WHERE id = ? AND student_id = ?
        """, (exam_id, student_id)).fetchone()

        if not exam or exam["passed"] != 1:
            abort(403)

        officials = get_certificate_officials(conn)
        if not officials["quranic_halaqah_director"] or not officials["endowments_director"]:
            abort(403)

        ctx = build_certificate_context(student, exam, officials)
        ctx["mark"] = exam["mark"]
        ctx["exam_id"] = exam["id"]
        ctx["student_id"] = student["id"]

        exam_type = str(exam["exam_type"] or "").strip()
        level_raw = str(exam["level"] or "").strip().replace(" ", "")

        exam_type_map = {
            "غيب": "غيباً",
            "غيباً": "غيباً",
            "نظرا": "نظراً",
            "نظراً": "نظراً"
        }
        exam_type = exam_type_map.get(exam_type, exam_type)

        level_map = {
            "5": "1-5",
            "10": "1-10",
            "15": "1-15",
            "20": "1-20",
            "25": "1-25",
            "30": "1-30",
            "1-5": "1-5",
            "1-10": "1-10",
            "1-15": "1-15",
            "1-20": "1-20",
            "1-25": "1-25",
            "26-30": "26-30",
            "1-30": "1-30"
        }
        level = level_map.get(level_raw, level_raw)

        level_labels = {
            "1-5": "الخمسة الأولى",
            "1-10": "العشرة",
            "1-15": "الخمسة عشر",
            "1-20": "العشرون",
            "1-25": "الخمسة والعشرون",
            "26-30": "الخمسة الأخيرة",
            "1-30": "القرآن كامل"
        }

        is_full_quran = level == "1-30"
        is_parts = level in level_labels and not is_full_quran

        ctx["memorized_parts_number"] = "" if is_full_quran else level
        ctx["memorized_parts_number_words"] = level_labels.get(level, level)

        if exam_type == "نظراً":
            if is_full_quran:
                template_name = "certificate_nazar_full.html"
            elif is_parts:
                template_name = "certificate_nazar_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400
        elif exam_type == "غيباً":
            if is_full_quran:
                template_name = "certificate_full.html"
            elif is_parts:
                template_name = "certificate_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400
        else:
            return f"قيمة exam_type غير صحيحة: {exam_type}", 400

        bg_filename = ctx.get("background_image")
        bg_path = os.path.join(app.root_path, "static", bg_filename) if bg_filename else None
        ctx["background_data_uri"] = file_to_data_uri(bg_path) if bg_path and os.path.exists(bg_path) else ""

        qr_verify_url = url_for("verify_certificate", student_id=student_id, exam_id=exam_id, _external=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        ctx["qr_data_uri"] = "data:image/png;base64," + base64.b64encode(qr_buffer.read()).decode("ascii")

        html = render_template(template_name, student=student, exam=exam, ctx=ctx)
        try:
            pdf = render_cert_pdf(html)
        except Exception as exc:
            return f"PDF generation is unavailable: {exc}", 500

        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=certificate.pdf"
        return response

    finally:
        conn.close()

@app.route("/certificate/download/<int:student_id>/<int:exam_id>")
def certificate_download(student_id, exam_id):
    conn = get_db_connection()
    try:
        student = conn.execute("""
            SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                   cm.full_name AS committee_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            JOIN committee_members cm ON s.committee_member_id = cm.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()

        if not student:
            abort(404)

        exam = conn.execute("""
            SELECT *
            FROM exam_records
            WHERE id = ? AND student_id = ?
        """, (exam_id, student_id)).fetchone()

        if not exam or exam["passed"] != 1:
            abort(403)

        officials = get_certificate_officials(conn)
        if not officials["quranic_halaqah_director"] or not officials["endowments_director"]:
            abort(403)

        ctx = build_certificate_context(student, exam, officials)
        ctx["mark"] = exam["mark"]
        ctx["exam_id"] = exam["id"]
        ctx["student_id"] = student["id"]

        exam_type = str(exam["exam_type"] or "").strip()
        level_raw = str(exam["level"] or "").strip().replace(" ", "")

        exam_type_map = {
            "غيب": "غيباً",
            "غيباً": "غيباً",
            "نظرا": "نظراً",
            "نظراً": "نظراً"
        }
        exam_type = exam_type_map.get(exam_type, exam_type)

        level_map = {
            "5": "1-5",
            "10": "1-10",
            "15": "1-15",
            "20": "1-20",
            "25": "1-25",
            "30": "1-30",
            "1-5": "1-5",
            "1-10": "1-10",
            "1-15": "1-15",
            "1-20": "1-20",
            "1-25": "1-25",
            "26-30": "26-30",
            "1-30": "1-30"
        }
        level = level_map.get(level_raw, level_raw)

        level_labels = {
            "1-5": "الخمسة الأولى",
            "1-10": "العشرة",
            "1-15": "الخمسة عشر",
            "1-20": "العشرون",
            "1-25": "الخمسة والعشرون",
            "26-30": "الخمسة الأخيرة",
            "1-30": "القرآن كامل"
        }

        is_full_quran = level == "1-30"
        is_parts = level in level_labels and not is_full_quran

        ctx["memorized_parts_number"] = "" if is_full_quran else level
        ctx["memorized_parts_number_words"] = level_labels.get(level, level)

        if exam_type == "نظراً":
            if is_full_quran:
                template_name = "certificate_nazar_full.html"
            elif is_parts:
                template_name = "certificate_nazar_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400
        elif exam_type == "غيباً":
            if is_full_quran:
                template_name = "certificate_full.html"
            elif is_parts:
                template_name = "certificate_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400
        else:
            return f"قيمة exam_type غير صحيحة: {exam_type}", 400

        bg_filename = ctx.get("background_image")
        bg_path = os.path.join(app.root_path, "static", bg_filename) if bg_filename else None
        ctx["background_data_uri"] = file_to_data_uri(bg_path) if bg_path and os.path.exists(bg_path) else ""

        qr_verify_url = url_for("verify_certificate", student_id=student_id, exam_id=exam_id, _external=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        ctx["qr_data_uri"] = "data:image/png;base64," + base64.b64encode(qr_buffer.read()).decode("ascii")

        html = render_template(template_name, student=student, exam=exam, ctx=ctx)
        try:
            pdf = render_cert_pdf(html)
        except Exception as exc:
            return f"PDF generation is unavailable: {exc}", 500

        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"

        filename = f"{student['full_name']}_{exam['exam_type']}_{exam['level']}.pdf"
        safe_filename = filename.replace("/", "-").replace("\\", "-")
        ascii_fallback = (
            safe_filename.encode("ascii", "ignore").decode("ascii") or "certificate.pdf"
        )
        quoted = quote(safe_filename.encode("utf-8"))
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{quoted}'
        )
        return response

    finally:
        conn.close()

def build_certificate_pdf(student_id, exam_id):
    conn = get_db_connection()

    try:
        if session.get("role") == "admin":
            student = conn.execute("""
                SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                       cm.full_name AS committee_name
                FROM students s
                JOIN centers c ON s.center_id = c.id
                JOIN committee_members cm ON s.committee_member_id = cm.id
                WHERE s.id = ?
            """, (student_id,)).fetchone()
        else:
            member = get_logged_committee_member()
            if not member:
                abort(403)

            student = conn.execute("""
                SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                       cm.full_name AS committee_name
                FROM students s
                JOIN centers c ON s.center_id = c.id
                JOIN committee_members cm ON s.committee_member_id = cm.id
                WHERE s.id = ? AND s.committee_member_id = ?
            """, (student_id, member["id"])).fetchone()

        if not student:
            abort(404)

        exam = conn.execute("""
            SELECT *
            FROM exam_records
            WHERE id = ? AND student_id = ?
        """, (exam_id, student_id)).fetchone()

        if not exam or exam["passed"] != 1:
            abort(403)

        officials = get_certificate_officials(conn)
        if not officials["quranic_halaqah_director"] or not officials["endowments_director"]:
            abort(403)

        ctx = build_certificate_context(student, exam, officials)
        ctx["mark"] = exam["mark"]
        ctx["exam_id"] = exam["id"]
        ctx["student_id"] = student["id"]

        exam_type = str(exam["exam_type"] or "").strip()
        level_raw = str(exam["level"] or "").strip().replace(" ", "")

        exam_type_map = {
            "غيب": "غيباً",
            "غيباً": "غيباً",
            "نظرا": "نظراً",
            "نظراً": "نظراً"
        }
        exam_type = exam_type_map.get(exam_type, exam_type)

        level_map = {
            "5": "1-5",
            "10": "1-10",
            "15": "1-15",
            "20": "1-20",
            "25": "1-25",
            "30": "1-30",
            "1-5": "1-5",
            "1-10": "1-10",
            "1-15": "1-15",
            "1-20": "1-20",
            "1-25": "1-25",
            "26-30": "26-30",
            "1-30": "1-30"
        }
        level = level_map.get(level_raw, level_raw)

        level_labels = {
            "1-5": "الخمسة الأولى",
            "1-10": "العشرة",
            "1-15": "الخمسة عشر",
            "1-20": "العشرون",
            "1-25": "الخمسة والعشرون",
            "26-30": "الخمسة الأخيرة",
            "1-30": "القرآن كامل"
        }

        is_full_quran = level == "1-30"
        is_parts = level in level_labels and not is_full_quran

        ctx["memorized_parts_number"] = "" if is_full_quran else level
        ctx["memorized_parts_number_words"] = level_labels.get(level, level)

        if exam_type == "نظراً":
            if is_full_quran:
                template_name = "certificate_nazar_full.html"
            elif is_parts:
                template_name = "certificate_nazar_parts.html"
            else:
                return None, None, None, "قيمة level غير صحيحة"
        elif exam_type == "غيباً":
            if is_full_quran:
                template_name = "certificate_full.html"
            elif is_parts:
                template_name = "certificate_parts.html"
            else:
                return None, None, None, "قيمة level غير صحيحة"
        else:
            return None, None, None, "قيمة exam_type غير صحيحة"

        bg_filename = ctx.get("background_image")
        bg_path = os.path.join(app.root_path, "static", bg_filename)
        bg_data_uri = file_to_data_uri(bg_path) if bg_filename and os.path.exists(bg_path) else ""

        qr_verify_url = url_for("verify_certificate", student_id=student_id, exam_id=exam_id, _external=True)
        qr_img = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr_img.add_data(qr_verify_url)
        qr_img.make(fit=True)

        qr_pil = qr_img.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_pil.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_b64 = base64.b64encode(qr_buffer.read()).decode("ascii")
        qr_data_uri = f"data:image/png;base64,{qr_b64}"

        ctx["background_data_uri"] = bg_data_uri
        ctx["qr_data_uri"] = qr_data_uri

        html = render_template(template_name, student=student, exam=exam, ctx=ctx)
        try:
            pdf = render_cert_pdf(html)
        except Exception as exc:
            return None, None, None, f"PDF generation is unavailable: {exc}"
        return pdf, student, exam, None

    finally:
        conn.close()


@app.route("/certificate/pdf/<int:student_id>/<int:exam_id>")
def certificate_pdf1(student_id, exam_id):
    pdf, student, exam, error = build_certificate_pdf(student_id, exam_id)
    if error:
        return error, 400

    student_name = str(student["full_name"]).strip()
    exam_type = str(exam["exam_type"] or "").strip()
    level = str(exam["level"] or "").strip()

    raw_filename = f"{student_name}_{exam_type}_{level}_certificate.pdf"
    ascii_filename = secure_filename(raw_filename) or "certificate.pdf"
    encoded_filename = quote(raw_filename)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'inline; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    )
    return response




@app.route("/certificate/qr/<int:student_id>/<int:exam_id>")
def certificate_qr(student_id, exam_id):
    verify_url = url_for("verify_certificate", student_id=student_id, exam_id=exam_id, _external=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")
@app.route("/certificate/verify/<int:student_id>/<int:exam_id>")
def verify_certificate(student_id, exam_id):
    conn = get_db_connection()

    certificate = conn.execute("""
        SELECT
            s.id AS student_id,
            s.full_name,
            s.father_name,
            s.mother_name,
            s.mother_kunya,
            s.birth_date,
            s.national_id,
            s.family_book,
            s.town,
            s.phone_number,
            s.exam_type,
            s.level,
            s.mark,
            s.status,
            s.center_id,
            s.committee_member_id,
            c.center_name,
            c.location,
            c.mosque_name AS student_mosque_name,
            c.sector,
            c.gender_type,
            cm.full_name AS committee_name,
            e.id AS exam_id,
            e.exam_type AS exam_record_type,
            e.level AS exam_record_level,
            e.mark AS exam_record_mark,
            e.passed,
            e.created_at
        FROM students s
        JOIN centers c ON s.center_id = c.id
        JOIN committee_members cm ON s.committee_member_id = cm.id
        JOIN exam_records e ON e.student_id = s.id

        WHERE s.id = ? AND e.id = ?
    """, (student_id, exam_id)).fetchone()

    conn.close()

    if not certificate:
        return render_template("certificate_verify.html", valid=False, certificate=None)

    return render_template("certificate_verify.html", valid=True, certificate=certificate)
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("member_dashboard"))
@app.route("/students")
def students():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    member = conn.execute("""
        SELECT cm.*, c.center_name
        FROM committee_members cm
        JOIN centers c ON cm.center_id = c.id
        WHERE cm.user_id = ?
    """, (session["user_id"],)).fetchone()

    if session.get("role") == "admin":
        rows = conn.execute("""
            SELECT s.*, c.center_name, cm.full_name AS committee_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            JOIN committee_members cm ON s.committee_member_id = cm.id
            ORDER BY s.id DESC
        """).fetchall()
    else:
        if member:
            rows = conn.execute("""
                SELECT s.*, c.center_name, cm.full_name AS committee_name
                FROM students s
                JOIN centers c ON s.center_id = c.id
                JOIN committee_members cm ON s.committee_member_id = cm.id
                WHERE s.center_id = ? AND s.committee_member_id = ?
                ORDER BY s.id DESC
            """, (member["center_id"], member["id"])).fetchall()
        else:
            rows = []

    conn.close()
    return render_template("students.html", students=rows, member=member)

import sqlite3
import os
from flask import redirect, url_for, flash, session

DB_PATH = os.path.join(app.root_path, 'database', 'app.db')

import sqlite3
import os
from flask import redirect, url_for, flash, session

DB_PATH = os.path.join(app.root_path, 'database', 'app.db')

@app.route('/delete_student_exam/<int:exam_id>', methods=['POST'])
def delete_student_exam(exam_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    exam = cur.execute('SELECT * FROM exam_records WHERE id = ?', (exam_id,)).fetchone()
    if exam is None:
        conn.close()
        flash('الاختبار غير موجود', 'error')
        return redirect(url_for('students'))

    student_id = exam['student_id']

    if exam['result_image']:
        image_path = os.path.join(app.root_path, 'static', exam['result_image'])
        if os.path.exists(image_path):
            os.remove(image_path)

    cur.execute('DELETE FROM exam_records WHERE id = ?', (exam_id,))
    conn.commit()
    conn.close()

    flash('تم حذف الاختبار بنجاح', 'success')
    return redirect(url_for('member_student_detail', student_id=student_id))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    student = cur.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    if student is None:
        conn.close()
        flash('الطالب غير موجود', 'error')
        if session.get('role') == 'admin':
            return redirect(url_for('students'))
        return redirect(url_for('member_students'))

    exams = cur.execute('SELECT * FROM exam_records WHERE student_id = ?', (student_id,)).fetchall()

    for exam in exams:
        if exam['result_image']:
            image_path = os.path.join(app.root_path, 'static', exam['result_image'])
            if os.path.exists(image_path):
                os.remove(image_path)

    cur.execute('DELETE FROM certificates WHERE student_id = ?', (student_id,))
    cur.execute('DELETE FROM exam_records WHERE student_id = ?', (student_id,))
    cur.execute('DELETE FROM students WHERE id = ?', (student_id,))

    conn.commit()
    conn.close()

    flash('تم حذف الطالب وجميع البيانات المرتبطة به بنجاح', 'success')

    if session.get('role') == 'admin':
        return redirect(url_for('students'))
    return redirect(url_for('member_students'))
@app.route("/member/dashboard")
@committee_required
def member_dashboard():
    member = get_logged_committee_member()
    conn = get_db_connection()
    students = conn.execute("""
        SELECT s.*, c.center_name
        FROM students s
        JOIN centers c ON s.center_id = c.id
        WHERE s.committee_member_id = ?
        ORDER BY s.id DESC
    """, (member["id"],)).fetchall()
    conn.close()
    return render_template("member_students.html", member=member, students=students)

@app.route("/member/student/search")
@committee_required
def student_search():
    name = request.args.get("q", "").strip()
    member = get_logged_committee_member()

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT *
        FROM students
        WHERE committee_member_id = ?
          AND full_name LIKE ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (member["id"], f"%{name}%")).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

@app.route("/member/students/new", methods=["GET", "POST"])
@committee_required
def student_new():
    member = get_logged_committee_member()
    conn = get_db_connection()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        father_name = request.form.get("father_name")
        mother_name = request.form.get("mother_name")
        mother_kunya = request.form.get("mother_kunya")
        birth_date = request.form.get("birth_date")
        national_id = request.form.get("national_id")
        family_book = request.form.get("family_book")
        town = request.form.get("town")
        mosque_name = request.form.get("mosque_name")
        phone_number = request.form.get("phone_number")

        conn.execute("""
            INSERT INTO students (
                full_name, father_name, mother_name, mother_kunya, birth_date,
                national_id, family_book, town, mosque_name, phone_number,
                center_id, committee_member_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name, father_name, mother_name, mother_kunya, birth_date,
            national_id, family_book, town, mosque_name, phone_number,
            member["center_id"], member["id"]
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("member_dashboard"))

    conn.close()
    return render_template("student_form.html", member=member)
@app.route("/member/students/<int:student_id>/certificate/<int:exam_id>")
@admin_or_committee_required
def student_certificate(student_id, exam_id):
    conn = get_db_connection()

    try:
        if session.get("role") == "admin":
            student = conn.execute("""
                SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                       cm.full_name AS committee_name
                FROM students s
                JOIN centers c ON s.center_id = c.id
                JOIN committee_members cm ON s.committee_member_id = cm.id
                WHERE s.id = ?
            """, (student_id,)).fetchone()
        else:
            member = get_logged_committee_member()
            if not member:
                abort(403)

            student = conn.execute("""
                SELECT s.*, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type,
                       cm.full_name AS committee_name
                FROM students s
                JOIN centers c ON s.center_id = c.id
                JOIN committee_members cm ON s.committee_member_id = cm.id
                WHERE s.id = ? AND s.committee_member_id = ?
            """, (student_id, member["id"])).fetchone()

        if not student:
            abort(404)

        exam = conn.execute("""
            SELECT *
            FROM exam_records
            WHERE id = ? AND student_id = ?
        """, (exam_id, student_id)).fetchone()

        if not exam:
            abort(404)

        if exam["passed"] != 1:
            abort(403)

        officials = get_certificate_officials(conn)

        if not officials["quranic_halaqah_director"] or not officials["endowments_director"]:
            message = "يرجى من الأدمن تعيين اسم رئيس دائرة الحلقات التربوية واسم مدير الأوقاف قبل طباعة الشهادات."
            if session.get("role") == "admin":
                message += " يمكنك تعيينهما من لوحة الأدمن."
            return render_template(
                "certificate_missing_officials.html",
                message=message,
                student_id=student_id,
            )

        ctx = build_certificate_context(student, exam, officials)
        ctx["mark"] = exam["mark"]
        ctx["exam_id"] = exam["id"]
        ctx["student_id"] = student["id"]
        ctx["show_endowments_director"] = True

        exam_type = str(exam["exam_type"] or "").strip()
        level_raw = str(exam["level"] or "").strip().replace(" ", "")
        gender_type = str(student["gender_type"] or "").strip()

        exam_type_map = {
            "غيب": "غيباً",
            "غيباً": "غيباً",
            "نظرا": "نظراً",
            "نظراً": "نظراً"
        }
        exam_type = exam_type_map.get(exam_type, exam_type)

        level_map = {
            "5": "1-5",
            "10": "1-10",
            "15": "1-15",
            "20": "1-20",
            "25": "1-25",
            "30": "1-30",
            "1-5": "1-5",
            "1-10": "1-10",
            "1-15": "1-15",
            "1-20": "1-20",
            "1-25": "1-25",
            "26-30": "26-30",
            "1-30": "1-30"
        }

        level = level_map.get(level_raw, level_raw)

        level_labels = {
            "1-5": "الخمسة الأولى",
            "1-10": "العشرة",
            "1-15": "الخمسة عشر",
            "1-20": "العشرون",
            "1-25": "الخمسة والعشرون",
            "26-30": "الخمسة الأخيرة",
            "1-30": "القرآن كامل"
        }

        is_full_quran = level == "1-30"
        is_parts = level in level_labels and not is_full_quran

        ctx["memorized_parts_number"] = "" if is_full_quran else level
        ctx["memorized_parts_number_words"] = level_labels.get(level, level)

        if exam_type == "نظراً":
            if is_full_quran:
                template_name = "certificate_nazar_full.html"
            elif is_parts:
                template_name = "certificate_nazar_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400

        elif exam_type == "غيباً":
            if is_full_quran:
                template_name = "certificate_full.html"
            elif is_parts:
                template_name = "certificate_parts.html"
            else:
                return f"قيمة level غير صحيحة: {level_raw}", 400

        else:
            return f"قيمة exam_type غير صحيحة: {exam_type}", 400

        bg_filename = ctx.get("background_image")
        bg_path = os.path.join(app.root_path, "static", bg_filename) if bg_filename else None
        ctx["background_data_uri"] = file_to_data_uri(bg_path) if bg_path and os.path.exists(bg_path) else ""

        qr_verify_url = url_for("verify_certificate", student_id=student_id, exam_id=exam_id, _external=True)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        ctx["qr_data_uri"] = "data:image/png;base64," + base64.b64encode(qr_buffer.read()).decode("ascii")
        return render_template(template_name, student=student, exam=exam, ctx=ctx)

    finally:
        conn.close()
@app.route("/member/students/<int:student_id>")
@admin_or_committee_required
def member_student_detail(student_id):
    conn = get_db_connection()

    if session.get("role") == "admin":
        student = conn.execute("""
            SELECT
                s.id,
                s.full_name,
                s.father_name,
                s.mother_name,
                s.mother_kunya,
                s.birth_date,
                s.national_id,
                s.family_book,
                s.town,
                s.phone_number,
                s.exam_type,
                s.level,
                s.mark,
                s.status,
                s.center_id,
                s.committee_member_id,
                s.mosque_name AS student_mosque_name,
                c.center_name,
                c.location,
                c.sector,
                c.gender_type,
                cm.full_name AS committee_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            JOIN committee_members cm ON s.committee_member_id = cm.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()

        back_url = url_for("students")
    else:
        member = get_logged_committee_member()
        student = conn.execute("""
            SELECT
                s.id,
                s.full_name,
                s.father_name,
                s.mother_name,
                s.mother_kunya,
                s.birth_date,
                s.national_id,
                s.family_book,
                s.town,
                s.phone_number,
                s.exam_type,
                s.level,
                s.mark,
                s.status,
                s.center_id,
                s.committee_member_id,
                s.mosque_name AS student_mosque_name,
                c.center_name,
                c.location,
                c.sector,
                c.gender_type,
                cm.full_name AS committee_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            JOIN committee_members cm ON s.committee_member_id = cm.id
            WHERE s.id = ? AND s.committee_member_id = ?
        """, (student_id, member["id"])).fetchone()

        back_url = url_for("member_dashboard")

    if not student:
        conn.close()
        abort(404)

    exams = conn.execute("""
        SELECT *
        FROM exam_records
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (student_id,)).fetchall()

    conn.close()
    return render_template(
        "student_detail.html",
        student=student,
        exams=exams,
        back_url=back_url
    )

@app.route("/admin/centers")
@admin_required
def admin_centers():
    conn = get_db_connection()

    centers = conn.execute("""
        SELECT
            c.id,
            c.center_name,
            c.location,
            c.mosque_name,
            c.sector,
            c.gender_type,
            COUNT(cm.id) AS committee_count
        FROM centers c
        LEFT JOIN committee_members cm ON cm.center_id = c.id
        GROUP BY c.id, c.center_name, c.location, c.mosque_name, c.sector, c.gender_type
        ORDER BY c.id DESC
    """).fetchall()

    committee_members = conn.execute("""
    SELECT
        cm.id,
        cm.full_name,
        cm.national_id,
        cm.center_id,
        c.center_name
    FROM committee_members cm
    JOIN centers c ON cm.center_id = c.id
    ORDER BY c.center_name ASC, cm.full_name ASC
""").fetchall()

    conn.close()
    return render_template(
        "admin_centers.html",
        centers=centers,
        committee_members=committee_members
    )
@app.route("/admin/committee-members")
@admin_required
def admin_committee_members():
    conn = get_db_connection()
    members = conn.execute("""
        SELECT
            cm.id,
            cm.user_id,
            cm.full_name,
            cm.mother_name,
            cm.mother_kunya,
            cm.birth_date,
            cm.national_id,
            cm.family_book,
            cm.town,
            cm.education,
            cm.sharia_education,
            cm.quran_ijazat,
            cm.center_id,
            c.center_name,
            u.username
        FROM committee_members cm
        LEFT JOIN centers c ON cm.center_id = c.id
        LEFT JOIN users u ON cm.user_id = u.id
        ORDER BY cm.id DESC
    """).fetchall()

    conn.close()
    return render_template("admin_committee_members.html", members=members)

@app.route("/admin/committee-members/change-password/<int:member_id>", methods=["GET", "POST"])
@admin_required
def change_committee_member_password(member_id):
    conn = get_db_connection()

    member = conn.execute("""
        SELECT cm.id, cm.full_name, u.username
        FROM committee_members cm
        JOIN users u ON cm.user_id = u.id
        WHERE cm.id = ?
    """, (member_id,)).fetchone()

    if not member:
        conn.close()
        abort(404)

    if request.method == "POST":
        new_password = request.form.get("new_password")

        if not new_password:
            conn.close()
            flash("يرجى إدخال كلمة المرور الجديدة", "error")
            return render_template("change_password.html", member=member)

        hashed_password = generate_password_hash(new_password)

        conn.execute("""
            UPDATE users
            SET password = ?
            WHERE id = (
                SELECT user_id FROM committee_members WHERE id = ?
            )
        """, (hashed_password, member_id))

        conn.commit()
        conn.close()
        flash("تم تغيير كلمة المرور بنجاح", "success")
        return redirect(url_for("admin_committee_members"))

    conn.close()
    return render_template("change_password.html", member=member)

from io import BytesIO
import pandas as pd
from flask import send_file, request

@app.route("/admin/reports/export-excel")
@admin_required
def admin_reports_export_excel():
    year = request.args.get("year", "all")
    month = request.args.get("month", "all")
    center_id = request.args.get("center_id", "all")

    conn = get_db_connection()

    query = """
        SELECT
            s.full_name AS student_name,
            s.father_name AS father_name,
            c.center_name AS center_name,
            e.exam_type AS exam_type,
            e.level AS level_name,
            e.mark,
            e.passed,
            e.exam_datetime
        FROM exam_records e
        JOIN students s ON e.student_id = s.id
        JOIN centers c ON s.center_id = c.id
        WHERE 1=1
    """
    params = []

    if year and year != "all":
        query += " AND strftime('%Y', e.exam_datetime) = ?"
        params.append(str(year))

    if month and month != "all":
        try:
            month_num = int(month)
            query += " AND strftime('%m', e.exam_datetime) = ?"
            params.append(f"{month_num:02d}")
        except ValueError:
            pass

    if center_id and center_id != "all":
        query += " AND c.id = ?"
        params.append(center_id)

    query += " ORDER BY e.id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            "اسم الطالب": r["student_name"],
            "اسم الأب": r["father_name"],
            "المركز": r["center_name"],
            "نوع السبر": r["exam_type"],
            "الفرع": r["level_name"],
            "العلامة": r["mark"],
            "النتيجة": "ناجح" if r["passed"] == 1 else "راسب",
            "تاريخ السبر": r["exam_datetime"]
        })

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reports")

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="reports.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/admin/committee-members/delete/<int:member_id>", methods=["POST"])
@admin_required
def delete_committee_member(member_id):
    conn = get_db_connection()

    member = conn.execute(
        "SELECT * FROM committee_members WHERE id = ?",
        (member_id,)
    ).fetchone()

    if not member:
        conn.close()
        abort(404)

    conn.execute("DELETE FROM students WHERE committee_member_id = ?", (member_id,))
    conn.execute("DELETE FROM exam_records WHERE student_id IN (SELECT id FROM students WHERE committee_member_id = ?)", (member_id,))
    conn.execute("DELETE FROM committee_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()

    flash("تم حذف عضو اللجنة بنجاح", "success")
    return redirect(url_for("admin_committee_members"))



from flask import render_template, Response, request
import pandas as pd
import io

@app.route("/admin/reports")
@admin_required
def admin_reports():
    conn = get_db_connection()

    years = conn.execute("""
        SELECT DISTINCT strftime('%Y', exam_datetime) AS year
        FROM exam_records
        WHERE exam_datetime IS NOT NULL AND TRIM(exam_datetime) != ''
        ORDER BY year
    """).fetchall()

    months = conn.execute("""
        SELECT DISTINCT strftime('%Y-%m', exam_datetime) AS month
        FROM exam_records
        WHERE exam_datetime IS NOT NULL AND TRIM(exam_datetime) != ''
        ORDER BY month
    """).fetchall()

    centers = conn.execute("""
        SELECT id, center_name
        FROM centers
        ORDER BY center_name
    """).fetchall()

    conn.close()

    return render_template(
        "admin_reports.html",
        years=[r["year"] for r in years],
        months=[r["month"] for r in months],
        centers=[{"id": r["id"], "name": r["center_name"]} for r in centers]
    )


@app.route("/admin/reports/data")
@admin_required
def admin_reports_data():
    view = request.args.get("view", "month")
    year = request.args.get("year")
    month = request.args.get("month")
    center_id = request.args.get("center_id")

    conn = get_db_connection()

    where = ["e.exam_datetime IS NOT NULL", "TRIM(e.exam_datetime) != ''"]
    params = []

    if year and year != "all":
        where.append("strftime('%Y', e.exam_datetime) = ?")
        params.append(year)

    if month and month != "all":
        where.append("strftime('%Y-%m', e.exam_datetime) = ?")
        params.append(month)

    if center_id and center_id != "all":
        where.append("s.center_id = ?")
        params.append(center_id)

    if view == "center":
        sql = f"""
            SELECT COALESCE(c.center_name, 'بدون مركز') AS label, COUNT(e.id) AS total
            FROM exam_records e
            LEFT JOIN students s ON e.student_id = s.id
            LEFT JOIN centers c ON s.center_id = c.id
            WHERE {" AND ".join(where)}
            GROUP BY COALESCE(c.center_name, 'بدون مركز')
            ORDER BY total DESC
        """
        title = "الإحصائيات حسب المراكز"
        hint = "عرض كل المراكز"
    elif view == "year":
        sql = f"""
            SELECT strftime('%Y-%m', e.exam_datetime) AS label, COUNT(e.id) AS total
            FROM exam_records e
            LEFT JOIN students s ON e.student_id = s.id
            LEFT JOIN centers c ON s.center_id = c.id
            WHERE {" AND ".join(where)}
            GROUP BY strftime('%Y-%m', e.exam_datetime)
            ORDER BY label
        """
        title = "الإحصائيات حسب الشهور"
        hint = "عرض الشهور داخل السنة المختارة"
    else:
        if year and year != "all" and month and month != "all":
            sql = f"""
                SELECT COALESCE(c.center_name, 'بدون مركز') AS label, COUNT(e.id) AS total
                FROM exam_records e
                LEFT JOIN students s ON e.student_id = s.id
                LEFT JOIN centers c ON s.center_id = c.id
                WHERE {" AND ".join(where)}
                GROUP BY COALESCE(c.center_name, 'بدون مركز')
                ORDER BY total DESC
            """
            title = f"الإحصائيات حسب المراكز - {month}"
            hint = "توزيع السبر بين المراكز داخل الشهر المختار"
        else:
            sql = f"""
                SELECT strftime('%Y-%m', e.exam_datetime) AS label, COUNT(e.id) AS total
                FROM exam_records e
                LEFT JOIN students s ON e.student_id = s.id
                LEFT JOIN centers c ON s.center_id = c.id
                WHERE {" AND ".join(where)}
                GROUP BY strftime('%Y-%m', e.exam_datetime)
                ORDER BY label
            """
            title = "الإحصائيات حسب الشهور"
            hint = "اختر سنة لعرض الشهور"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    labels = [r["label"] for r in rows]
    values = [r["total"] for r in rows]
    total = sum(values)

    return {
        "labels": labels,
        "values": values,
        "total": total,
        "title": title,
        "hint": hint
    }

@app.route("/admin/reports/records")
@admin_required
def admin_reports_records():
    year = request.args.get("year")
    month = request.args.get("month")
    center_id = request.args.get("center_id")

    conn = get_db_connection()

    where = ["e.exam_datetime IS NOT NULL", "TRIM(e.exam_datetime) != ''"]
    params = []

    if year and year != "all":
        where.append("strftime('%Y', e.exam_datetime) = ?")
        params.append(year)

    if month and month != "all":
        where.append("strftime('%Y-%m', e.exam_datetime) = ?")
        params.append(month)

    if center_id and center_id != "all":
        where.append("s.center_id = ?")
        params.append(center_id)

    sql = f"""
        SELECT
            e.id AS record_id,
            e.exam_datetime,
            e.student_id,
            COALESCE(s.full_name, '') AS student_name,
            COALESCE(s.father_name, '') AS father_name,
            COALESCE(c.center_name, '') AS center_name,
            COALESCE(e.exam_type, '') AS exam_type,
            COALESCE(e.level, '') AS level_name,
            COALESCE(e.mark, 0) AS mark,
            CASE
                WHEN COALESCE(e.passed, 0) = 1 THEN 'ناجح'
                ELSE 'راسب'
            END AS status
        FROM exam_records e
        LEFT JOIN students s ON e.student_id = s.id
        LEFT JOIN centers c ON s.center_id = c.id
        WHERE {" AND ".join(where)}
        ORDER BY e.exam_datetime DESC, e.id DESC
    """

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    records = [{
        "id": r["record_id"],
        "exam_datetime": r["exam_datetime"],
        "student_id": r["student_id"],
        "student_name": r["student_name"],
        "father_name": r["father_name"],
        "center_name": r["center_name"],
        "exam_type": r["exam_type"],
        "level_name": r["level_name"],
        "mark": r["mark"],
        "status": r["status"]
    } for r in rows]

    return {"records": records, "count": len(records)}

@app.route("/admin/centers/delete/<int:center_id>", methods=["POST"])
@admin_required
def delete_center(center_id):
    conn = get_db_connection()

    center = conn.execute(
        "SELECT * FROM centers WHERE id = ?",
        (center_id,)
    ).fetchone()

    if not center:
        conn.close()
        abort(404)

    students_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM students WHERE center_id = ?",
        (center_id,)
    ).fetchone()["cnt"]

    if students_count > 0:
        conn.close()
        flash("لا يمكن حذف المركز لأن هناك طلابًا مرتبطين به", "error")
        return redirect(url_for("admin_centers"))

    members = conn.execute(
        "SELECT id FROM committee_members WHERE center_id = ?",
        (center_id,)
    ).fetchall()

    member_ids = [m["id"] for m in members]

    if member_ids:
        placeholders = ",".join("?" for _ in member_ids)
        conn.execute(
            f"DELETE FROM exam_records WHERE student_id IN (SELECT id FROM students WHERE committee_member_id IN ({placeholders}))",
            member_ids
        )
        conn.execute(
            f"DELETE FROM students WHERE committee_member_id IN ({placeholders})",
            member_ids
        )
        conn.execute(
            f"DELETE FROM committee_members WHERE id IN ({placeholders})",
            member_ids
        )

    conn.execute("DELETE FROM centers WHERE id = ?", (center_id,))
    conn.commit()
    conn.close()

    flash("تم حذف المركز بنجاح", "success")
    return redirect(url_for("admin_centers"))

@app.route("/member/students/<int:student_id>/exam/new", methods=["GET", "POST"])
@admin_or_committee_required
def add_student_exam(student_id):
    member = get_logged_committee_member()
    conn = get_db_connection()

    if session.get("role") == "admin":
        student = conn.execute("""
            SELECT s.*, c.center_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()
    else:
        student = conn.execute("""
            SELECT s.*, c.center_name
            FROM students s
            JOIN centers c ON s.center_id = c.id
            WHERE s.id = ? AND s.committee_member_id = ?
        """, (student_id, member["id"])).fetchone()

    if not student:
        conn.close()
        abort(404)

    allowed_levels = {
        "نظراً": ["1-10", "1-20", "1-30"],
        "غيباً": ["1-5", "1-10", "1-15", "1-20", "1-25", "26-30", "1-30"]
    }

    if request.method == "POST":
        exam_type = request.form.get("exam_type")
        level = request.form.get("level")
        mark = request.form.get("mark")
        result_image = request.files.get("result_image")

        if not exam_type:
            conn.close()
            return render_template("exam_form.html", student=student, error="يرجى اختيار نوع السبر")

        if exam_type not in allowed_levels:
            conn.close()
            return render_template("exam_form.html", student=student, error="نوع السبر غير صحيح")

        if not level:
            conn.close()
            return render_template("exam_form.html", student=student, error="يرجى اختيار المستوى")

        if level not in allowed_levels[exam_type]:
            conn.close()
            return render_template("exam_form.html", student=student, error="المستوى غير صحيح لهذا النوع")

        if not mark:
            conn.close()
            return render_template("exam_form.html", student=student, error="يرجى إدخال العلامة")

        try:
            mark_int = int(mark)
        except ValueError:
            conn.close()
            return render_template("exam_form.html", student=student, error="العلامة يجب أن تكون رقمًا")

        if mark_int < 0 or mark_int > 100:
            conn.close()
            return render_template("exam_form.html", student=student, error="العلامة يجب أن تكون بين 0 و 100")

        if not result_image or not result_image.filename:
            conn.close()
            return render_template("exam_form.html", student=student, error="يرجى إرفاق صورة نتيجة الاختبار")

        if not allowed_exam_image(result_image.filename):
            conn.close()
            return render_template(
                "exam_form.html",
                student=student,
                error="نوع الصورة غير مدعوم. استخدم PNG أو JPG أو GIF أو WEBP"
            )

        passed = 0
        status = "راسب"

        if exam_type == "نظراً" and mark_int >= 80:
            passed = 1
            status = "ناجح"
        elif exam_type == "غيباً" and mark_int >= 90:
            passed = 1
            status = "ناجح"

        exam_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result_image_path = save_exam_result_image(student_id, result_image)

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO exam_records
            (student_id, exam_type, level, mark, passed, exam_datetime, result_image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id, exam_type, level, mark_int, passed,
            exam_datetime, result_image_path
        ))

        cur.execute("""
            UPDATE students
            SET exam_type = ?, level = ?, mark = ?, status = ?
            WHERE id = ?
        """, (exam_type, level, mark_int, status, student_id))

        conn.commit()
        conn.close()
        return redirect(url_for("member_student_detail", student_id=student_id))

    conn.close()
    return render_template("exam_form.html", student=student)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/admin/certificate-officials", methods=["GET", "POST"])
@admin_required
def admin_certificate_officials():
    if request.method == "POST":
        quranic_halaqah_director = request.form.get("quranic_halaqah_director", "")
        endowments_director = request.form.get("endowments_director", "")
        if not quranic_halaqah_director.strip() or not endowments_director.strip():
            flash("يرجى إدخال الاسمين معاً", "error")
        else:
            save_certificate_officials(quranic_halaqah_director, endowments_director)
            flash("تم حفظ أسماء المسؤولين بنجاح", "success")
        return redirect(url_for("admin_certificate_officials"))

    officials = get_certificate_officials()
    return render_template("admin_officials.html", officials=officials)

@app.route("/admin/centers/new", methods=["GET", "POST"])
@admin_required
def new_center():
    if request.method == "POST":
        center_name = request.form.get("center_name")
        location = request.form.get("location")
        mosque_name = request.form.get("mosque_name")
        sector = request.form.get("sector")
        gender_type = request.form.get("gender_type")

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO centers (center_name, location, mosque_name, sector, gender_type)
            VALUES (?, ?, ?, ?, ?)
        """, (center_name, location, mosque_name, sector, gender_type))
        conn.commit()
        conn.close()

        flash("تم إنشاء المركز بنجاح", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("center_form.html")
@app.route("/admin/committee/new", methods=["GET", "POST"])
@admin_required
def new_committee_member():
    conn = get_db_connection()
    centers = conn.execute("SELECT id, center_name FROM centers ORDER BY center_name").fetchall()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        full_name = request.form.get("full_name")
        mother_name = request.form.get("mother_name")
        mother_kunya = request.form.get("mother_kunya")
        birth_date = request.form.get("birth_date")
        national_id = request.form.get("national_id")
        family_book = request.form.get("family_book")
        town = request.form.get("town")
        education = request.form.get("education")
        sharia_education = request.form.get("sharia_education")
        quran_ijazat = request.form.get("quran_ijazat")
        center_id = request.form.get("center_id")

        hashed_password = generate_password_hash(password)

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed_password, "committee_member"))
        user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO committee_members
            (user_id, full_name, mother_name, mother_kunya, birth_date,
             national_id, family_book, town, education, sharia_education,
             quran_ijazat, center_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, mother_name, mother_kunya, birth_date,
              national_id, family_book, town, education, sharia_education,
              quran_ijazat, center_id))

        conn.commit()
        conn.close()

        flash("تم إنشاء عضو اللجنة بنجاح", "success")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("committee_form.html", centers=centers)



if __name__ == "__main__":
    app.run(debug=True)