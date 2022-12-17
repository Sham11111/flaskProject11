from flask import Flask, request, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'gjdslgnfwelje124804810'
db = SQLAlchemy(app)

scheduler = BackgroundScheduler()


class DBF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tm = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return 'DBF %r' % self.id

# Осуществление входа на сайт под своим именем
@app.route('/login', methods=['POST', 'GET'])
def login():
        if request.method == 'POST':
            session['username'] = request.form['username']
            return redirect(url_for('disp_ads'))
        else:
            return redirect(url_for('disp_ads'))


@app.route('/')
def redirect_all():
    return redirect(url_for('login'))

# Вызов объявления
@app.route('/all', methods=['POST', 'GET'])
def disp_ads():
    gad = DBF.query.order_by(DBF.tm.desc()).all()
    return render_template("disp_ads.html", gad=gad)

# Подробности объявления
@app.route('/all/<int:id>')
def detail_ads(id):
    gad_detail = DBF.query.get(id)
    return render_template("detail_ads.html", gad_detail=gad_detail)

# Создание объявлений
@app.route('/create_ad', methods=['POST', 'GET'])
def create_ads():
    if request.method == "POST":
        username = session['username']
        title = request.form['title']
        content = request.form['content']

        ad = DBF(title=title, content=content, username=username)

        try:
            db.session.add(ad)
            db.session.commit()
            return redirect('/all')
        except:
            return "Ошибка!"
    else:
        return render_template("create_ads.html")

# Внесение изменений в объявления
@app.route('/all/<int:id>/update', methods=['POST', 'GET'])
def change_ads(id):
    gad_detail = DBF.query.get(id)
    if request.method == "POST":
        gad_detail.username = session['username']
        gad_detail.title = request.form['title']
        gad_detail.content = request.form['content']

        db.session.commit()
        return redirect('/all')

    else:
        if gad_detail.username != session['username']:
            return "Ошибка! Вы можете изменить только свои объявления!"
        else:
            return render_template("change_ads.html", gad_detail=gad_detail)

# Удаление объявлений
@app.route('/all/<int:id>/delete')
def delete_ads(id):
    gad_detail = DBF.query.get(id)
    if request.method == 'GET':
        if gad_detail.username == session['username']:
            db.session.delete(gad_detail)
            db.session.commit()
            return redirect('/all')

        else:
            return "Ошибка! Вы можете удалять только свои объявления!"

# Автоматическое удаление объявлений по времени
def auto_delete():
    with app.app_context():

        tables = DBF.query.all()

        for item_tables in tables:

            if item_tables.tm + timedelta(minutes=5) <= datetime.now():
                db.session.delete(item_tables)
                db.session.commit()


scheduler.add_job(func=auto_delete, trigger="interval", seconds=360)

scheduler.start()

atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.run()
