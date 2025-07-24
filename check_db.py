import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'effectiveness.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看saturation_data表结构
cursor.execute("PRAGMA table_info(saturation_data)")
columns = cursor.fetchall()
print("saturation_data表字段：")
for col in columns:
    print(col[1])

conn.close()