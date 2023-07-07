import pandas as pd
from distutils.log import debug
from fileinput import filename
from FDataBase import FDataBase
from flask_login import LoginManager, login_user, logout_user, current_user
from UserLogin import UserLogin
from flask import *
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
DATABASE = '/tmp/useravt.db'
UPLOAD_FOLDER = os.path.join('Files', 'Uploads')
ALLOWED_EXTENSIONS = {'csv'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE'] = DATABASE
app.config.update(dict(DATABASE=os.path.join(app.root_path,'useravt.db')))
app.secret_key = 'This is your secret key to utilize session in Flask'
login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
	print('load user')
	return UserLogin().fromdb(user_id,dbase)
def connect_db():
	conn = sqlite3.connect(app.config['DATABASE'])
	conn.row_factory = sqlite3.Row
	return conn
def create_db():
	db = connect_db()
	with app.open_resource('sq_db.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()
	db.close()
def get_db():
	if not hasattr(g,'link_db'):
		g.link_db = connect_db()
	return g.link_db
dbase = None
@app.before_request
def before_request():
	global dbase
	db = get_db()
	dbase = FDataBase(db)
@app.teardown_appcontext
def close_db(error):
	if hasattr(g,'link_db'):
		g.link_db.close()
@app.route('/login', methods=['POST', 'GET'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('profile'))
	if request.method == 'POST':
		user = dbase.getUserByEmail(request.form['email'])
		if user and check_password_hash(user['psw'], request.form['psw']):
			userlogin = UserLogin().create(user)
			rm = True if request.form.get('remainme') else False
			login_user(userlogin, remember=rm)
			return redirect(url_for('profile'))
		flash('Неверная пара логин/пароль', 'error')
	return render_template('login.html')
@app.route('/register', methods=['POST','GET'])
def register():
	if request.method == 'POST':
		if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
			and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
			hash = generate_password_hash(request.form['psw'])
			res = dbase.addUser(request.form['name'], request.form['email'], hash)
			if res:
				flash('Вы успешно зарегистрированы', 'success')
				return redirect(url_for('login'))
			else:
				flash('Ошибка при добавлении в БД', 'error')
		else:
			flash('Неверно заполены поля', 'error')
	return render_template('register.html')
@app.route('/', methods=['GET', 'POST'])
def uploadFile():
	if request.method == 'POST':
		f = request.files.get('file')
		data_filename = secure_filename(f.filename)
		f.save(os.path.join(app.config['UPLOAD_FOLDER'],
							data_filename))
		session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'],
					data_filename)
		return render_template('index.html')
	return render_template("home.html")
@app.route('/show_data')
def showData():
	data_file_path = session.get('uploaded_data_file_path', None)
	uploaded_df = pd.read_csv(data_file_path,
							encoding='unicode_escape')
	uploaded_df_html = uploaded_df.to_html()
	return render_template('showcsv.html',
						data_var=uploaded_df_html)
@app.route('/show_list')
def lst_column_info():
	files_list = []
	for files in os.listdir('path'):
		if files.endswith('.csv'):
			files_list.append(files)
	columns = {}
	for file in files_list:
		df = pd.read_csv(os.path.join('path', file))
		columns[file] = list(df.columns)
	return render_template('showlist.html', files_list=files_list, columns=columns)
@app.route('/delete', methods=['POST'])
def delete_files():
	path = 'path'
	files = request.form['filename']
	if files.endswith('.csv'):
		os.remove(os.path.join(path, files))
		flash('Файл успешно удален')
	else:
		flash('Файл не найден')
		return render_template('index.html')
	return render_template('index.html')
@app.route('/logout')
def logout():
	logout_user()
	flash('Вы вышли из аккаунта', 'success')
	return render_template('login.html')
@app.route('/profile')
def profile():
	return f"""<p><a href="{url_for('logout')}">Выйти из профиля</a>
                <p>user info: {current_user.get_id()} """
if __name__ == '__main__':
	app.run(host = '0.0.0.0', port=80, debug=True)

