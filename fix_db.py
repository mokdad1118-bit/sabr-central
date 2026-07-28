import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
import sqlite3

DB_PATH = "database/app.db"  # غيّر المسار حسب قاعدة البيانات عندك

def get_tables(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row["name"] for row in cur.fetchall()]
    conn.close()
    return tables

def get_columns(db_path, table_name):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = cur.fetchall()
    conn.close()
    return columns

if __name__ == "__main__":
    try:
        tables = get_tables(DB_PATH)

        if not tables:
            print("لا توجد جداول في قاعدة البيانات.")
        else:
            print("الجداول الموجودة في قاعدة البيانات:")
            for table in tables:
                print(f"- {table}")

            table_name = input("\nأدخل اسم الجدول الذي تريد معرفة أعمدته: ").strip()

            if table_name not in tables:
                print("اسم الجدول غير موجود.")
            else:
                cols = get_columns(DB_PATH, table_name)
                print(f"\nأعمدة جدول {table_name}:")
                for col in cols:
                    print(f"- {col['name']} ({col['type']})")
    except sqlite3.Error as e:
        print("حدث خطأ في قاعدة البيانات:", e)