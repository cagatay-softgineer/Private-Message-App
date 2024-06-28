from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from cryptography.fernet import Fernet
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cagat233'
socketio = SocketIO(app)

if not os.path.isfile('secret.key'):
    # Generate a key for encryption
    key = Fernet.generate_key()

    # Save the key to a file for persistence
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)
else:
    # Load the existing key from file
    with open('secret.key', 'rb') as key_file:
        key = key_file.read()

# Initialize Fernet cipher suite
cipher_suite = Fernet(key)

# Paths to Excel files
users_file = 'database/users.xlsx'
messages_file = 'database/messages.xlsx'

# Ensure the Excel files exist
if not os.path.exists(users_file):
    pd.DataFrame(columns=['username', 'password']).to_excel(users_file, index=False, engine='openpyxl')

if not os.path.exists(messages_file):
    pd.DataFrame(columns=['user_id', 'message']).to_excel(messages_file, index=False, engine='openpyxl')

def read_users():
    return pd.read_excel(users_file, engine='openpyxl')

def write_users(df):
    df.to_excel(users_file, index=False, engine='openpyxl')

def read_messages():
    return pd.read_excel(messages_file, engine='openpyxl')

def write_messages(df):
    df.to_excel(messages_file, index=False, engine='openpyxl')

@app.route('/')
def index():
    return redirect(url_for('chat'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    return render_template('chat.html', username=username)

@socketio.on('message')
def handle_message(msg):
    if 'username' not in session:
        return emit('message', {'user': 'System', 'message': 'User not authenticated.'}, broadcast=True)

    username = session['username']
    users = read_users()
    user_row = users[users['username'] == username]

    if user_row.empty:
        return emit('message', {'user': 'System', 'message': 'User not found.'}, broadcast=True)

    user = user_row.iloc[0]
    messages = read_messages()
    new_message = pd.DataFrame({'user_id': [user.name], 'message': [cipher_suite.encrypt(msg.encode()).decode()]})
    messages = pd.concat([messages, new_message], ignore_index=True)
    write_messages(messages)
    emit('message', {'user': username, 'message': msg}, broadcast=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_users()
        user_row = users[users['username'] == username]

        if user_row.empty or cipher_suite.decrypt(user_row.iloc[0]['password'].encode()).decode() != password:
            return redirect(url_for('login'))  # Redirect to login page on failed login

        session['username'] = username
        return redirect(url_for('chat'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_users()

        if not users[users['username'] == username].empty:
            return redirect(url_for('signup'))  # Redirect to signup page if username already exists

        encrypted_password = cipher_suite.encrypt(password.encode()).decode()
        new_user = pd.DataFrame({'username': [username], 'password': [encrypted_password]})
        users = pd.concat([users, new_user], ignore_index=True)
        write_users(users)

        session['username'] = username
        return redirect(url_for('chat'))

    return render_template('signup.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
