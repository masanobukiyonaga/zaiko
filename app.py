from flask import Flask, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
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

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), nullable=False) # 品番
    item_name = db.Column(db.String(80), nullable=False)
    lot_number = db.Column(db.String(50), nullable=False) # 数量の代わりにロットNo.

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

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        # フォームからデータが送られてきたら保存する
        if request.method == 'POST':
            action = request.form.get('action')
            item_code = request.form['item_code']
            
            if action == 'add':
                item_name = request.form['item_name']
                lot_number = request.form['lot_number']
                new_stock = Stock(item_code=item_code, item_name=item_name, lot_number=lot_number)
                db.session.add(new_stock)
                db.session.commit()
            elif action == 'delete':
                stock = Stock.query.filter_by(item_code=item_code).first()
                if stock:
                    db.session.delete(stock)
                    db.session.commit()
            
            return redirect(url_for('index'))

        # データが空なら初期データを入れる（テスト用）
        if Stock.query.first() is None:
            sample1 = Stock(item_code="A001", item_name="テスト商品A", lot_number="LOT001")
            sample2 = Stock(item_code="B002", item_name="テスト商品B", lot_number="LOT002")
            db.session.add(sample1)
            db.session.add(sample2)
            db.session.commit()

        stocks = Stock.query.all()
        html = "<h1>📦 在庫管理システム</h1>"
        html += "<p>環境: AWS EC2 (MySQL)</p><hr>"
        
        # 入力フォーム
        html += """
        <h3>新規登録 / 削除</h3>
        <form method="POST">
            品番: <input type="text" name="item_code" id="item_code" required>
            <button type="button" onclick="fetchItemName()">品番検索</button><br>
            品名: <input type="text" name="item_name" id="item_name">
            <button type="button" onclick="fetchItemCode()">品名検索</button><br>
            ロットNo.: <input type="text" name="lot_number" id="lot_number" required>
            <button type="button" onclick="fetchItemByLot()">ロット検索</button><br>
            <br>
            <button type="submit" name="action" value="add">追加</button>
            <button type="submit" name="action" value="delete" style="background-color: #ff4d4d; color: white;" onclick="return confirm('本当に削除しますか？');">削除</button>
        </form>
        <script>
        function fetchItemName() {
            const code = document.getElementById('item_code').value;
            if (!code) return;
            fetch('/api/item/' + code)
                .then(response => response.json())
                .then(data => {
                    if (data.item_name) {
                        document.getElementById('item_name').value = data.item_name;
                        if(data.lot_number) document.getElementById('lot_number').value = data.lot_number;
                    } else {
                        alert('商品が見つかりませんでした');
                        document.getElementById('item_name').value = '';
                    }
                })
                .catch(err => console.error(err));
        }
        function fetchItemCode() {
            const name = document.getElementById('item_name').value;
            if (!name) return;
            fetch('/api/code/' + name)
                .then(response => response.json())
                .then(data => {
                    if (data.item_code) {
                        document.getElementById('item_code').value = data.item_code;
                        if(data.lot_number) document.getElementById('lot_number').value = data.lot_number;
                    } else {
                        alert('商品が見つかりませんでした');
                        document.getElementById('item_code').value = '';
                    }
                })
                .catch(err => console.error(err));
        }
        function fetchItemByLot() {
            const lot = document.getElementById('lot_number').value;
            if (!lot) return;
            fetch('/api/lot/' + lot)
                .then(response => response.json())
                .then(data => {
                    if (data.item_code) {
                        document.getElementById('item_code').value = data.item_code;
                        document.getElementById('item_name').value = data.item_name;
                    } else {
                        alert('商品が見つかりませんでした');
                    }
                })
                .catch(err => console.error(err));
        }
        </script>
        <hr>
        """
        
        html += "<h3>在庫一覧</h3><ul>"
        for stock in stocks:
            html += f"<li>【{stock.item_code}】 {stock.item_name} (LOT: {stock.lot_number})</li>"
        html += "</ul>"
        
        return html
    except Exception as e:
        return f"<h1>⚠️ エラー</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # ローカル開発用ポート設定（80番ポートで起動）
    app.run(debug=True, host='127.0.0.1', port=5000)