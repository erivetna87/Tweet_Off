import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth',  __name__, url_prefix='/auth')

# @bp.route associates the URL /register with the register view function. \
# When Flask receives a request to /auth/register, \
# it will call the register view and use the return value as the response

@bp.route('/register', methods=('GET','POST'))
def register():
    # request.method will be 'POST'. In this case, start validating the input.
   
    # request.form is a special type of dict mapping submitted form keys and values. \
    # The user will input their username and password.
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

    # db. execute takes a SQL query with ? placeholders for any user input,\ 
    # and a tuple of values to replace the placeholders with. \
    # The database library will take care of escaping the values \
    # so you are not vulnerable to a SQL injection attack.

        if not username:
            error = 'Username is Required'
        elif not password:
                error = 'Password is required'
        elif db.execute(
                'SELECT id FROM user WHERE username = ?', (username,)
                ).fetchone() is not None:
                error = 'User {} is already registered.'.format(username)
        
        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))
        
        flash(error)
    
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect Password.'
        
        # session is a dict that stores data across requests. \
        # When validation succeeds, the user’s id is stored in a new session. \
        # The data is stored in a cookie that is sent to the browser, \
        # and the browser then sends it back with subsequent requests. \
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)

    return render_template('auth/login.html')


# bp.before_app_request() registers a function that runs before the view function, \
# no matter what URL is requested. load_logged_in_user checks if a user id is stored in the session and \
# gets that user’s data from the database, storing it on g.user, which lasts for the length of the request. \
# If there is no user id, or if the id doesn’t exist, g.user will be None.

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM USER WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view




