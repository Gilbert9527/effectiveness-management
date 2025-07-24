import sqlite3
import os

def clear_saturation_data():
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'effectiveness.db')
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 清空saturation_data表数据
        print("正在清空效能管理列表数据...")
        cursor.execute('''
            DELETE FROM saturation_data
        ''')
        
        # 如果需要同时清除上传记录，可以取消下面两行的注释
        # print("正在清空上传记录...")
        # cursor.execute('''DELETE FROM uploads WHERE type = 'saturation' ''')
        
        # 提交事务
        conn.commit()
        print(f"数据清空成功！共删除 {cursor.rowcount} 条记录")
        
    except sqlite3.Error as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"数据清空失败: {str(e)}")
        raise e
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

if __name__ == '__main__':
    clear_saturation_data()