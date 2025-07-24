import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'effectiveness.db')

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 创建数据表SQL
create_tables_sql = """
CREATE TABLE IF NOT EXISTS uploads (
    id TEXT PRIMARY KEY,
    file_name TEXT,
    upload_date TEXT
);

CREATE TABLE IF NOT EXISTS relationship_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id TEXT,
    person_name TEXT,
    project_name TEXT,
    position_name TEXT,
    FOREIGN KEY (upload_id) REFERENCES uploads(id)
);
"""

try:
    # 执行SQL
    cursor.executescript(create_tables_sql)
    conn.commit()
    print("数据表创建成功!")
except Exception as e:
    print(f"执行失败: {str(e)}")
    conn.rollback()
finally:
    # 关闭连接
    conn.close()