from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- 修正イメージ ---

# ▼ ローカル用（これをコメントアウトして無効化）
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_inventory.db'

# ▼ 本番AWS用（こちらの # を外して有効化！）
DB_USER = "admin"
DB_PASSWORD = "8108Za10" 
DB_ENDPOINT = "zaiko-1.c9ouqcm6qmdp.ap-northeast-1.rds.amazonaws.com"
DB_NAME = "mydatabase"

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_ENDPOINT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

@app.route('/')
def index():
    try:
        # データが空なら初期データを入れる（テスト用）
        if Stock.query.count() == 0:
            sample1 = Stock(item_name="テスト商品A", quantity=10)
            sample2 = Stock(item_name="テスト商品B", quantity=5)
            db.session.add(sample1)
            db.session.add(sample2)
            db.session.commit()

        stocks = Stock.query.all()
        html = "<h1>📦 ローカル開発中：在庫管理システム</h1>"
        html += "<p>環境: AWS EC2 (MySQL)</p><hr>"
        
        html += "<ul>"
        for stock in stocks:
            html += f"<li>{stock.item_name}: {stock.quantity} 個</li>"
        html += "</ul>"
        
        return html
    except Exception as e:
        return f"<h1>⚠️ エラー</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # ローカル開発用ポート設定（80番ポートで起動）
    app.run(debug=True, host='0.0.0.0', port=80)