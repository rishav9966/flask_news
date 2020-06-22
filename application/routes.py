from application import app
from flask import Response, render_template, redirect, url_for, request, flash, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, SelectField, PasswordField, validators
from wtforms.validators import DataRequired, email_validator
from passlib.hash import sha256_crypt

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskNews'
app.config['MYSQL_UNIX_SOCKET'] = '/opt/lampp/var/mysql/mysql.sock'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)


class NewsForm(Form):
    headline    =   StringField('Headline',validators=[DataRequired(),validators.Length(min=5,max=100)])
    description =   TextAreaField('Description',validators=[DataRequired()])
    category    =   SelectField(u'News Category', choices=[('General', 'General'), ('Lifestyle', 'Lifestyle'), ('Sports', 'Sports'), ('Country', 'Country'), ('Other', 'Other')])
    location    =   StringField('Location', validators=[DataRequired()])

class RegisterForm(Form):
    name    =   StringField('Name', validators=[DataRequired(),validators.Length(min=5,max=20)])
    email   =   StringField('Email', validators=[DataRequired(), validators.Length(min=8,max=40), validators.Email()])
    password=   PasswordField('Password',validators=[DataRequired(), validators.Length(min=3)])

class LoginForm(Form):
    email   =   StringField('Email', validators=[DataRequired(), validators.Length(min=8,max=40), validators.Email()])
    password=   PasswordField('Password',validators=[DataRequired(), validators.Length(min=3)])

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template('index.html', home=True)


@app.route('/news')
def news():
    # create cursor
    cur = mysql.connection.cursor()
    # Retreive news from database
    result = cur.execute("SELECT id, headline, location FROM news ORDER BY date_created")
    news_dict = cur.fetchall()
    if result > 0:
        return render_template('news.html', news=True, news_dict=news_dict)
    msg = "No News Available"
    return render_template('news.html', news=True, msg=msg)

@app.route('/addnews', methods=['GET', 'POST'])
def addnews():
    form = NewsForm(request.form)
    if request.method == 'POST' and form.validate():
        headline    =   form.headline.data
        description =   form.description.data
        category    =   form.category.data
        location    =   form.location.data.upper()
        author      =   session['email']
        # create cursor
        cur = mysql.connection.cursor()
        # execute sql
        cur.execute("INSERT INTO news(headline, description, author, category, location) VALUES(%s, %s, %s, %s, %s)", (headline, description, author, category, location))
        # commit sql
        mysql.connection.commit()
        # close cursor
        cur.close()
        flash('News added successfully', 'success')
        return redirect(url_for('news'))
    return render_template('addnews.html', news=True, form=form)


@app.route('/newsdetails/<string:id>')
def newsdetails(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM news WHERE ID=%s", [id])
    news = cur.fetchone()
    cur1 = mysql.connection.cursor()
    author = cur1.execute("SELECT name FROM account WHERE email=%s", [news['author']])
    author = cur1.fetchone()
    cur.close()
    cur1.close()
    if result > 0:
        return render_template('newsdetails.html', newsdetail=news, author=author)
    else:
        return redirect(url_for('news'))

@app.route('/contact')
def contact():
    return render_template('contact.html', contact=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        flash('You are already logged in !!', 'success')
        return redirect(url_for('dashboard'))
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email       =   form.email.data
        password    =   form.password.data
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM account WHERE email=%s", [email])
        if result > 0:
            data        =   cur.fetchone()
            password_db =   data['password']
            if sha256_crypt.verify(password, password_db):
                session['logged_in'] = True
                session['username'] = data['name']
                session['email'] = email
                flash('You are logged In successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Password didn\'t macthed', 'danger')
        else:
            flash('Email Id doesn\'t exists!', 'danger')
    return render_template('login.html', login=True, form=form)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'logged_in' in session:
        flash('You are logged in. Logout First!!', 'danger')
        return redirect(url_for('dashboard'))
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name    =   form.name.data
        email   =   form.email.data

        cur = mysql.connection.cursor()
        email_exist = cur.execute("SELECT id FROM account WHERE email=%s", [email])
        
        if not email_exist > 0:
            password = sha256_crypt.encrypt(str(form.password.data))
            cur.execute("INSERT INTO account (name, email, password) VALUES(%s, %s, %s)", (name, email, password))
            mysql.connection.commit()
            cur.close()
            flash('You are registered successfully! Login to continue', 'success')
            return redirect(url_for('login'))
        cur.close()
        flash('Email already exists', 'danger')
    return render_template('register.html', register=True, form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not 'logged_in' in session:
        flash('Login to access Dashboard', 'danger')
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM news WHERE author=%s ORDER BY date_created', [session['email']])
    if result > 0:
        author_news = cur.fetchall()
        cur.close()
        return render_template('dashboard.html', author_news=author_news)
    msg = "No news available yet"
    return render_template('dashboard.html', msg=msg)