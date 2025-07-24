import sqlite3
import os

def update_database():    
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'effectiveness.db')
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 向saturation_data表添加project_name和position_name字段
        print("正在更新saturation_data表结构...")
        cursor.execute('''
            ALTER TABLE saturation_data
            ADD COLUMN project_name TEXT
        ''')
        cursor.execute('''
            ALTER TABLE saturation_data
            ADD COLUMN position_name TEXT
        ''')
        
        # 2. 删除relationship_data表
        print("正在删除relationship_data表...")
        cursor.execute('''
            DROP TABLE IF EXISTS relationship_data
        ''')
        
        # 3. 如果存在关联关系相关的上传记录路由表，也一并删除
        cursor.execute('''
            DROP TABLE IF EXISTS relationship_uploads
        ''')
        
        # 提交事务
        conn.commit()
        print("数据库表结构更新成功！")
        
    except sqlite3.Error as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"数据库更新失败: {str(e)}")
        raise e
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

if __name__ == '__main__':
    update_database()