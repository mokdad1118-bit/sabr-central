from datetime import datetime

CERTIFICATE_IMAGE_NAMES = {
    ("غيباً", True, "ذكور"): "hifz-kamel-dhakar.png",
    ("غيباً", True, "إناث"): "hifz-kamel-untha.png",
    ("غيباً", False, "ذكور"): "hifz-ajza-dhakar.png",
    ("غيباً", False, "إناث"): "hifz-ajza-untha.png",
    ("نظراً", True, "ذكور"): "nathari-kamel-dhakar.png",
    ("نظراً", True, "إناث"): "nathari-kamel-untha.png",
    ("نظراً", False, "ذكور"): "nathari-ajza-dhakar.png",
    ("نظراً", False, "إناث"): "nathari-ajza-untha.png",
}

def is_full_certificate(exam_type, level):
    level = str(level).strip().replace(" ", "")
    return level in ("30", "1-30", "1/30")


def get_certificate_image_name(exam_type, level, gender_type):
    is_full = is_full_certificate(exam_type, level)
    gender = gender_type if gender_type in ("ذكور", "إناث") else "ذكور"
    return CERTIFICATE_IMAGE_NAMES.get((exam_type, is_full, gender), "hifz-kamel-dhakar.png")


def get_certificate_image_path(exam_type, level, gender_type):
    return f"images/certificates/{get_certificate_image_name(exam_type, level, gender_type)}"


def extract_birth_year(birth_date):
    if not birth_date:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return str(datetime.strptime(str(birth_date)[:10], fmt).year)
        except ValueError:
            continue
    digits = "".join(ch for ch in str(birth_date) if ch.isdigit())
    return digits[:4] if len(digits) >= 4 else str(birth_date)


def get_grade_from_mark(mark):
    if mark is None:
        return ""
    mark = int(float(mark))
    if mark >= 98:
        return "امتياز"
    if mark >= 95:
        return "ممتاز"
    if mark >= 90:
        return "جيد جداً"
    if mark >= 85:
        return "جيد"
    return "مقبول"


def gregorian_to_hijri(year, month, day):
    year = int(year)
    month = int(month)
    day = int(day)

    if month < 3:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    l = jd - 1948440 + 10632
    n = int((l - 1) / 10631)
    l = l - 10631 * n + 354
    j = (
        (int((10985 - l) / 5316)) * (int((50 * l) / 17719))
        + (int(l / 5670)) * (int((43 * l) / 15238))
    )
    l = (
        l
        - (int((30 - j) / 15)) * (int((17719 * j) / 50))
        - (int(j / 16)) * (int((15238 * j) / 43))
        + 29
    )
    m = int((24 * l) / 709)
    d = l - int((709 * m) / 24)
    y = 30 * n + j - 30
    return int(y), int(m), int(d)


def get_hijri_parts(exam_dt):
    if isinstance(exam_dt, str):
        exam_dt = parse_exam_datetime(exam_dt)
    return gregorian_to_hijri(exam_dt.year, exam_dt.month, exam_dt.day)


def format_hijri_date(exam_dt):
    hy, hm, hd = get_hijri_parts(exam_dt)
    hd = int(hd)
    hm = int(hm)
    hy = int(hy)
    return f"{hd:02d}/{hm:02d}/{hy:04d}"


def format_gregorian_date(dt):
    return dt.strftime("%d/%m/%Y")


def parse_exam_datetime(value):
    if not value:
        return datetime.now()
    value = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return datetime.now()


def build_memorized_parts_text(exam_type, level, memorized_parts):
    if is_full_certificate(exam_type, level):
        return "القرآن الكريم كاملاً"
    if memorized_parts:
        return memorized_parts
    return f"حفظ {level} أجزاء"


def build_certificate_context(student, exam, officials):
    exam_dt = parse_exam_datetime(exam["exam_datetime"] or exam["created_at"])
    show_parts = not is_full_certificate(exam["exam_type"], exam["level"])

    if "memorized_parts" in exam.keys():
        memorized_parts = exam["memorized_parts"]
    else:
        memorized_parts = ""

    return {
        "student_name": student["full_name"] or "",
        "father_name": student["father_name"] or "",
        "birth_town": student["town"] or "",
        "birth_year": extract_birth_year(student["birth_date"]),
        "mosque_name": student["mosque_name"] or student["center_name"] or "",
        "grade": get_grade_from_mark(exam["mark"]),
        "hijri_date": format_hijri_date(exam_dt),
        "gregorian_date": format_gregorian_date(exam_dt),
        "halaqah_director": officials.get("quranic_halaqah_director", ""),
        "endowments_director": officials.get("endowments_director", ""),
        "memorized_parts": build_memorized_parts_text(
            exam["exam_type"], exam["level"], memorized_parts
        ),
        "show_parts": show_parts,
        "exam_type": exam["exam_type"],
        "level": exam["level"],
        "gender_type": student["gender_type"],
        "background_image": get_certificate_image_path(
            exam["exam_type"], exam["level"], student["gender_type"]
        ),
    }