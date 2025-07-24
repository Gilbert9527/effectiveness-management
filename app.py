from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import sqlite3
from flask import g
from datetime import datetime
import pandas as pd

app = Flask(__name__)

#添加全局404错误处理
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': '请求的资源不存在'}), 404

# 添加全局500错误处理
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 数据库配置
# 数据库配置
DATABASE = r'd:\Effectiveness Management\effectiveness.db'
# 或者使用双反斜杠
# DATABASE = 'd:\\Effectiveness Management\\effectiveness.db'
# 或者使用正斜杠
# DATABASE = 'd:/Effectiveness Management/effectiveness.db'

# 数据库连接函数
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# 初始化数据库
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # 创建职位表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        ''')
        # 创建项目表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        ''')
        
        # 创建饱和度上传记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saturation_uploads (
            id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            saved_name TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
        ''')
        # 创建饱和度数据表
        # 修改饱和度数据表结构，添加项目和职位字段
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS saturation_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            code_equivalent REAL,
            saturation REAL,
            delivery_count INTEGER,
            scheduled_hours REAL,
            ai_active_days REAL,
            statistical_period TEXT,
            project_name TEXT,
            position_name TEXT,
            FOREIGN KEY (upload_id) REFERENCES saturation_uploads(id) ON DELETE CASCADE
        )
        ''')
        db.commit()

# 关闭数据库连接
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 在应用启动时初始化数据库
init_db()

# 模拟数据库 - 实际项目中应使用真实数据库
# 删除以下全局变量定义
# positions = []
# projects = []
# next_id = 1
upload_records = []
next_id = 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# 添加质量管理页面路由
@app.route('/quality')
def quality():
    return render_template('quality.html')

# 添加AI小助手页面路由
@app.route('/effectiveness-report')
def effectiveness_report():
    return render_template('effectiveness_report.html')

# 删除第95行的app.run()调用
# app.run(host='0.0.0.0', port=5000, debug=True)
# 应用启动配置在文件末尾的if __name__ == '__main__'块中
# 删除以下效能数据大屏路由代码
# @app.route('/dashboard')
# def dashboard():
#     return render_template('dashboard.html')

# 职位管理API
@app.route('/api/positions', methods=['GET'])
def get_positions():
    db = get_db()
    cursor = db.cursor()
    # 返回id和name字段，用于前端操作
    cursor.execute('SELECT id, name FROM positions ORDER BY name')
    positions = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
    return jsonify(positions)

# 项目管理API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    db = get_db()
    cursor = db.cursor()
    # 返回id和name字段，用于前端操作
    cursor.execute('SELECT id, name FROM projects ORDER BY name')
    projects = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
    return jsonify(projects)

@app.route('/api/positions', methods=['POST'])
def add_position():
    data = request.json
    name = data['name'].strip()
    if not name:
        return jsonify({'status': 'error', 'message': '职位名称不能为空'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('INSERT INTO positions (name) VALUES (?)', (name,))
        db.commit()
        return jsonify({'status': 'success', 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({'status': 'error', 'message': '职位名称已存在'}), 400

@app.route('/api/positions/<int:id>', methods=['DELETE'])
def delete_position(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM positions WHERE id = ?', (id,))
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    name = data['name'].strip()
    if not name:
        return jsonify({'status': 'error', 'message': '项目名称不能为空'}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
        db.commit()
        return jsonify({'status': 'success', 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({'status': 'error', 'message': '项目名称已存在'}), 400

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM projects WHERE id = ?', (id,))
    db.commit()
    return jsonify({'status': 'success'})

# 文件上传API
# 修改上传处理代码
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 保存文件
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    filename = f'{file_id}_{file.filename}'
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # 解析Excel并验证字段
    try:
        # 使用pandas读取Excel文件
        df = pd.read_excel(file_path)
        # 修复：添加项目名称和职位名称到必填字段验证
        required_columns = ['用户名称', '代码当量', '饱和度', '交付需求数', '排期工时', 'AI活跃天数', '统计周期', '项目名称', '职位名称']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            os.remove(file_path)  # 删除无效文件
            return jsonify({
                'message': f'Excel格式错误，缺少必要字段: {missing}'
            }), 400

        # 提取数据并保存（这里可以根据实际需求存入数据库）
        records = df[required_columns].to_dict('records')
        # 为演示，这里使用全局变量存储，实际项目中应使用数据库
        global upload_records
        upload_records = records

        # 记录上传信息
        upload_info = {
            'id': file_id,
            'file_name': file.filename,
            'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': records
        }
        # 保存上传记录（实际项目中应存入数据库）
        if not hasattr(app, 'upload_history'):
            app.upload_history = []
        app.upload_history.append(upload_info)

        # 替换全局变量存储，改为数据库存储
        db = get_db()
        cursor = db.cursor()
        try:
            # 插入上传记录
            cursor.execute(
                'INSERT INTO uploads (id, file_name, upload_date) VALUES (?, ?, ?)',
                (file_id, file.filename, upload_info['upload_date'])
            )
            # 插入关联关系数据
            for record in records:
                # 插入关联关系
                cursor.execute(
                    'INSERT INTO relationship_data (upload_id, person_name, project_name, position_name) VALUES (?, ?, ?, ?)',
                    (file_id, record['用户名称'], record['项目名称'], record['职位名称'])
                )
                # 新增：插入效能数据到saturation_data表
                cursor.execute(
                    '''INSERT INTO saturation_data (user_name, project_name, saturation, delivery_count, code_equivalent, statistical_period)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (record['用户名称'], record['项目名称'], record['饱和度'], record['交付需求数'], record['代码当量'], record['统计周期'])
                )
            db.commit()
            return jsonify({'message': '上传成功'}), 200
        except Exception as e:
            db.rollback()
            return jsonify({'message': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        os.remove(file_path)  # 删除错误文件
        return jsonify({'message': f'文件解析失败: {str(e)}'}), 400

@app.route('/api/saturation-upload', methods=['POST'])
def upload_saturation_file():
    if 'file' not in request.files:
        return jsonify({'message': '未找到文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '未选择文件'}), 400

    # 保存文件
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    saved_name = f'{file_id}_{secure_filename(file.filename)}'
    file_path = os.path.join(upload_dir, saved_name)
    file.save(file_path)

    # 解析Excel并验证字段
    try:
        # 使用pandas读取Excel文件
        df = pd.read_excel(file_path)
        # 检查必要字段
        required_columns = ['用户名称', '代码当量', '饱和度', '交付需求数', '排期工时', 'AI活跃天数', '统计周期', '项目名称', '职位名称']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            os.remove(file_path)  # 删除无效文件
            return jsonify({
                'message': f'Excel格式错误，缺少必要字段: {missing_columns}'
            }), 400

        # 检查数据类型
        try:
            # 处理百分比格式并转换数值列为数值类型
            # 处理饱和度字段（可能包含百分号或为空）
            if '饱和度' in df.columns:
                # 先处理空值，将空值填充为'0%'
                df['饱和度'] = df['饱和度'].fillna('0%')
                # 将空字符串也替换为'0%'
                df['饱和度'] = df['饱和度'].replace('', '0%')
                # 移除百分号并转换为数值
                df['饱和度'] = df['饱和度'].astype(str).str.replace('%', '').str.replace('％', '')
                df['饱和度'] = pd.to_numeric(df['饱和度'], errors='coerce')
                # 如果转换后仍有NaN值，填充为0
                df['饱和度'] = df['饱和度'].fillna(0)
            
            # 处理其他数值字段
            numeric_columns = ['代码当量', '交付需求数', '排期工时', 'AI活跃天数']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # 对于其他数值字段，空值保持为NaN，让后续验证处理
            
            # 检查是否有无法转换的数据（饱和度除外，因为已经处理了空值）
            numeric_check_columns = ['代码当量', '交付需求数', '排期工时', 'AI活跃天数']
            for col in numeric_check_columns:
                if col in df.columns and df[col].isna().any():
                    invalid_rows = df[df[col].isna()].index.tolist()
                    raise ValueError(f'字段"{col}"中第{[r+2 for r in invalid_rows]}行包含无效数据')
                    
        except Exception as type_error:
            os.remove(file_path)  # 删除无效文件
            return jsonify({
                'message': f'Excel数据类型错误: {str(type_error)}'
            }), 400

        # 记录上传信息到数据库
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                'INSERT INTO saturation_uploads (id, file_name, saved_name, upload_date) VALUES (?, ?, ?, ?)',
                (file_id, file.filename, saved_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )

            # 插入饱和度数据
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT INTO saturation_data (upload_id, user_name, code_equivalent, saturation, 
                        delivery_count, scheduled_hours, ai_active_days, statistical_period, project_name, position_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (file_id, row['用户名称'], row['代码当量'], row['饱和度'],
                          row['交付需求数'], row['排期工时'], row['AI活跃天数'],
                          row['统计周期'], row['项目名称'], row['职位名称']))
                except Exception as row_error:
                    print(f"行数据插入错误: {str(row_error)}, 数据: {row}")
                    raise row_error

            db.commit()
            return jsonify({'message': '上传成功'}), 200
        except Exception as db_error:
            db.rollback()
            os.remove(file_path)  # 删除错误文件
            print(f"数据库操作错误: {str(db_error)}")
            return jsonify({'message': f'数据库操作失败: {str(db_error)}'}), 400
    except Exception as e:
        os.remove(file_path)  # 删除错误文件
        print(f"文件解析错误: {str(e)}")
        return jsonify({'message': f'文件解析失败: {str(e)}'}), 400

@app.route('/api/saturation-uploads', methods=['GET'])
def get_saturation_uploads():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM saturation_uploads ORDER BY upload_date DESC')
    uploads = [{
        'id': row['id'],
        'file_name': row['file_name'],
        'upload_date': row['upload_date']
    } for row in cursor.fetchall()]
    return jsonify(uploads)

@app.route('/api/saturation-download/<string:id>')
def download_saturation_file(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM saturation_uploads WHERE id = ?', (id,))
    row = cursor.fetchone()
    if row:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            row['saved_name'],
            as_attachment=True,
            download_name=row['file_name']
        )
    return jsonify({'status': 'error', 'message': '文件不存在'}), 404

@app.route('/api/saturation-delete/<string:id>', methods=['DELETE'])
def delete_saturation_file(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT saved_name FROM saturation_uploads WHERE id = ?', (id,))
    row = cursor.fetchone()
    if row:
        # 删除文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['saved_name'])
        if os.path.exists(file_path):
            os.remove(file_path)
        # 删除数据库记录
        cursor.execute('DELETE FROM saturation_uploads WHERE id = ?', (id,))
        db.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '文件不存在'}), 404

@app.route('/api/saturation-data')
def get_saturation_data():
    # 获取前端参数
    position_ids = request.args.getlist('position_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    person_name = request.args.get('person_name')
    project_name = request.args.get('project_name')
    
    # 构建查询条件
    query = '''SELECT user_name, position_name, project_name, statistical_period, 
                      saturation, code_equivalent, delivery_count, scheduled_hours, ai_active_days 
               FROM saturation_data WHERE 1=1'''
    params = []
    
    # 添加职位筛选
    if position_ids:
        query += f" AND position_name IN ({','.join(['?']*len(position_ids))})"
        params.extend(position_ids)
    
    # 添加时间筛选
    if start_date:
        query += " AND statistical_period >= ?"
        params.append(start_date)
    if end_date:
        query += " AND statistical_period <= ?"
        params.append(end_date)
    
    # 添加人员和项目筛选
    if person_name:
        query += " AND user_name LIKE ?"
        params.append(f'%{person_name}%')
    if project_name and project_name != 'all':
        query += " AND project_name = ?"
        params.append(project_name)
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        
        # 转换为字典列表并返回所有字段
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"查询错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'数据库查询失败: {str(e)}', 'type': str(type(e))}), 500
    try:
        db = get_db()
        cursor = db.cursor()
        # 直接查询saturation_data表，不再关联relationship_data
        cursor.execute('''
            SELECT * FROM saturation_data
            ORDER BY statistical_period DESC
        ''')
        data = [{key: row[key] for key in row.keys()} for row in cursor.fetchall()]
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"查询错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'数据库查询失败: {str(e)}', 'type': str(type(e))}), 500
    try:
        db = get_db()
        cursor = db.cursor()
        # 添加调试信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        app.logger.debug(f"数据库表: {tables}")
         
        cursor.execute('''
            SELECT s.*, r.project_name, r.position_name 
            FROM saturation_data s
            LEFT JOIN relationship_data r ON s.person_name = r.person_name
            ORDER BY s.statistical_period DESC
        ''')
        data = [{key: row[key] for key in row.keys()} for row in cursor.fetchall()]
        return jsonify(data)
    except Exception as e:
        # 记录详细错误日志
        app.logger.error(f"查询错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'数据库查询失败: {str(e)}', 'type': str(type(e))}), 500

@app.route('/api/effectiveness-analysis', methods=['GET'])
def get_effectiveness_analysis():
    # 获取查询参数
    upload_id = request.args.get('upload_id')
    if not upload_id:
        return jsonify({'error': '缺少必要参数: upload_id'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        # 查询上传文件信息
        cursor.execute('SELECT * FROM saturation_uploads WHERE id = ?', (upload_id,))
        upload = cursor.fetchone()
        if not upload:
            return jsonify({'error': '上传记录不存在'}), 404

        # 查询分析数据
        cursor.execute('''
            SELECT user_name, saturation, delivery_count, code_equivalent 
            FROM saturation_data WHERE upload_id = ?
        ''', (upload_id,))
        
        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify({
            'status': 'success',
            'upload_info': upload,
            'analysis_data': data
        })
    except Exception as e:
        app.logger.error(f"效能分析查询失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/analyze-excel', methods=['POST'])
def analyze_excel():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': '文件格式不支持，请上传.xlsx或.xls文件'}), 400
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 验证必要的列
        required_columns = ['用户名称', '代码当量', '饱和度', '交付需求数', '排期工时', 'AI活跃天数']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Excel文件缺少必要的列: {", ".join(missing_columns)}'}), 400
        
        # 处理数据类型
        # 处理饱和度百分比
        if '饱和度' in df.columns:
            df['饱和度'] = df['饱和度'].astype(str).str.replace('%', '').replace('', '0')
            df['饱和度'] = pd.to_numeric(df['饱和度'], errors='coerce').fillna(0)
        
        # 处理其他数值列
        numeric_columns = ['代码当量', '交付需求数', '排期工时', 'AI活跃天数']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算分析结果 - 转换为Python原生类型
        user_names = [str(name) for name in df['用户名称'].tolist()]
        saturation = [float(val) for val in df['饱和度'].tolist()]
        delivery_count = [int(val) for val in df['交付需求数'].tolist()]
        code_equivalent = [float(val) for val in df['代码当量'].tolist()]
        
        # 找出最高值
        max_saturation_idx = df['饱和度'].idxmax()
        max_delivery_idx = df['交付需求数'].idxmax()
        max_code_idx = df['代码当量'].idxmax()
        
        analysis_result = {
            'filename': file.filename,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'record_count': int(len(df)),
            'user_names': user_names,
            'saturation': saturation,
            'delivery_count': delivery_count,
            'code_equivalent': code_equivalent,
            'top_saturation': {
                'person': str(df.loc[max_saturation_idx, '用户名称']),
                'value': float(df.loc[max_saturation_idx, '饱和度'])
            },
            'top_delivery': {
                'person': str(df.loc[max_delivery_idx, '用户名称']),
                'value': int(df.loc[max_delivery_idx, '交付需求数'])
            },
            'top_code': {
                'person': str(df.loc[max_code_idx, '用户名称']),
                'value': float(df.loc[max_code_idx, '代码当量'])
            }
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        return jsonify({'error': f'文件分析失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')