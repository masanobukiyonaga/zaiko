from flask import Flask, request, redirect, url_for, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

app = Flask(__name__)

# --- 修正イメージ ---

# ▼ ローカル用（これをコメントアウトして無効化）
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'local_inventory_v2.db')

# ▼ 本番AWS用（こちらの # を外して有効化！）
DB_USER = "admin"
DB_PASSWORD = os.getenv("DB_PASSWORD") 
DB_ENDPOINT = "zaiko-1.c9ouqcm6qmdp.ap-northeast-1.rds.amazonaws.com"
DB_NAME = "mydatabase"

if DB_PASSWORD is None:
    # 環境変数が無い場合のフォールバック（またはエラーにする）
    # 今回はわかりやすくエラーにします
    raise ValueError("DB_PASSWORD environment variable is not set")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_ENDPOINT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- モデル定義 ---

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), nullable=False) # 品番
    item_name = db.Column(db.String(80), nullable=False)
    lot_number = db.Column(db.String(50), nullable=False) # ロットNo.
    quantity = db.Column(db.Integer, nullable=False, default=0) # 数量 (初期値0)

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), nullable=False)
    item_name = db.Column(db.String(80), nullable=False)
    lot_number = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0) # 変動数量
    action = db.Column(db.String(20), nullable=False) # "新規登録", "入庫", "出庫", "削除"
    timestamp = db.Column(db.DateTime, default=datetime.now)

# --- API ---

@app.route('/api/item/<item_code>', methods=['GET'])
def get_item_name(item_code):
    stock = Stock.query.filter_by(item_code=item_code).first()
    if stock:
        return jsonify({"item_name": stock.item_name, "lot_number": stock.lot_number})
    else:
        return jsonify({"error": "Not found"}), 404

@app.route('/api/code/<item_name>', methods=['GET'])
def get_item_code(item_name):
    stock = Stock.query.filter_by(item_name=item_name).first()
    if stock:
        return jsonify({"item_code": stock.item_code, "lot_number": stock.lot_number})
    else:
        return jsonify({"error": "Not found"}), 404

@app.route('/api/lot/<lot_number>', methods=['GET'])
def get_item_by_lot(lot_number):
    stock = Stock.query.filter_by(lot_number=lot_number).first()
    if stock:
        return jsonify({"item_code": stock.item_code, "item_name": stock.item_name})
    else:
        return jsonify({"error": "Not found"}), 404

# --- ページ ---

@app.route('/')
def index():
    return redirect(url_for('inventory_page'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    message = ""
    if request.method == 'POST':
        action = request.form.get('action')
        item_code = request.form['item_code']
        lot_number = request.form['lot_number']
        
        if action == 'add':
            item_name = request.form['item_name']
            # 数量は0で登録
            new_stock = Stock(item_code=item_code, item_name=item_name, lot_number=lot_number, quantity=0)
            db.session.add(new_stock)
            
            # ログ記録
            log = InventoryLog(item_code=item_code, item_name=item_name, lot_number=lot_number, quantity=0, action="新規登録")
            db.session.add(log)
            
            db.session.commit()
            message = f"<p style='color: green;'>【新規登録】{item_name} (LOT: {lot_number}) を登録しました（数量: 0）。</p>"
            
        elif action == 'delete':
            stock = Stock.query.filter_by(item_code=item_code, lot_number=lot_number).first()
            if stock:
                # ログ記録
                log = InventoryLog(item_code=stock.item_code, item_name=stock.item_name, lot_number=stock.lot_number, quantity=stock.quantity, action="削除")
                db.session.add(log)
                
                db.session.delete(stock)
                db.session.commit()
                message = f"<p style='color: red;'>【削除】{stock.item_name} (LOT: {stock.lot_number}) を削除しました。</p>"
            else:
                message = "<p style='color: red;'>エラー: 該当する商品が見つかりませんでした。</p>"

    return render_template('register.html', message=message)

@app.route('/logs')
def logs_page():
    query = InventoryLog.query
    
    # 検索パラメータ
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (InventoryLog.item_code.contains(search)) | 
            (InventoryLog.item_name.contains(search)) | 
            (InventoryLog.lot_number.contains(search))
        )
    
    logs = query.order_by(InventoryLog.timestamp.desc()).all()
    
    return render_template('logs.html', logs=logs, search=search)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory_page():
    # 在庫更新処理
    if request.method == 'POST':
        stock_id = request.form.get('stock_id')
        amount = int(request.form.get('amount'))
        action_type = request.form.get('action_type') # "in" or "out"
        
        stock = Stock.query.get(stock_id)
        if stock:
            if action_type == 'in':
                stock.quantity += amount
                log_action = "入庫"
            elif action_type == 'out':
                stock.quantity -= amount
                log_action = "出庫"
            
            # ログ記録
            log = InventoryLog(item_code=stock.item_code, item_name=stock.item_name, lot_number=stock.lot_number, quantity=amount, action=log_action)
            db.session.add(log)
            db.session.commit()
        
        return redirect(url_for('inventory_page'))

    # 表示処理
    query = Stock.query
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (Stock.item_code.contains(search)) | 
            (Stock.item_name.contains(search)) | 
            (Stock.lot_number.contains(search))
        )

    stocks = query.all()
    
    return render_template('inventory.html', stocks=stocks, search=search)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # ローカル開発用ポート設定
    app.run(debug=True, host='127.0.0.1', port=5000)