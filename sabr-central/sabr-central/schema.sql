CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'committee_member'
);

CREATE TABLE IF NOT EXISTS centers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_name TEXT NOT NULL,
    location TEXT NOT NULL,
    mosque_name TEXT,
    sector TEXT,
    gender_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS committee_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    mother_name TEXT,
    mother_kunya TEXT,
    birth_date TEXT,
    national_id TEXT,
    family_book TEXT,
    town TEXT,
    education TEXT,
    الشرعي_المؤهل TEXT,
    quran_ijazat TEXT,
    center_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (center_id) REFERENCES centers (id)
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    mother_name TEXT,
    mother_kunya TEXT,
    birth_date TEXT,
    national_id TEXT,
    family_book TEXT,
    town TEXT,
    secondary_type TEXT,
    center_id INTEGER NOT NULL,
    committee_member_id INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    level TEXT,
    quran_ijazat TEXT,
    mark INTEGER,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (center_id) REFERENCES centers (id),
    FOREIGN KEY (committee_member_id) REFERENCES committee_members (id)
);

CREATE TABLE IF NOT EXISTS exam_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    exam_type TEXT NOT NULL,
    level TEXT,
    mark INTEGER NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    exam_datetime TEXT,
    result_image TEXT,
    memorized_parts TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (id)
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    certificate_uuid TEXT UNIQUE NOT NULL,
    certificate_number TEXT UNIQUE NOT NULL,
    file_path TEXT,
    printed_at TEXT,
    verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students (id)
);

CREATE TABLE IF NOT EXISTS verification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_uuid TEXT NOT NULL,
    verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    result TEXT NOT NULL
);