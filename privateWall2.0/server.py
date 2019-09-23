from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
from datetime import datetime
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = "I am a secret key"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
FN_REGEX = re.compile(r'[a-zA-Z]{2,}')
LN_REGEX = re.compile(r'[a-zA-z]{2,}')
PW_REGEX = re.compile(r'(?=.*\d)(?=.*[A-Z]).{8,15}$')

db = "private_wall_db"


@app.route("/")
def main():
    if not 'loggedin' in session:
        session['loggedin'] = False
    return render_template('index.html')

@app.route("/register", methods=["POST"])
def register():
    isValid = True
    # first name not entered
    if len(request.form['firstName']) < 1:
        flash("This field is required", "firstName")
        isValid = False
    # first name format doesn't match
    elif not(request.form['firstName'].isalpha()) or len(request.form['firstName']) < 2:
        flash("First name must contain at least two letters and contain only letters", "firstName")
        isValid = False
    # last name was not entered
    if len(request.form['lastName']) < 1:
        flash("This field is required", "lastName")
        isValid = False
    # last name format doesn't match
    elif not(request.form['lastName'].isalpha()) or len(request.form['lastName']) < 2:
        flash("Last name must contain at least two letters and contain only letters", "lastName")
        isValid = False
    # email was not entered
    if len(request.form['email']) < 1:
        flash("This field is required", "email")
        isValid = False
    # email does not match format
    elif not EMAIL_REGEX.match(request.form['email']):# test whether a field matches the pattern
        flash("Invalid email address", "email")
        isValid = False
    # email already used
    else:
        mysql = connectToMySQL(db)
        query = "SELECT * FROM users WHERE email = %(email)s;"
        data = {'email': request.form['email']}
        existingUser = mysql.query_db(query, data)
        print(existingUser)
        # email entered already exists in database
        if existingUser:
            flash("The email address you entered has already been taken. Please enter another one.", "email")
            isValid = False
    if len(request.form['password']) < 1:
        flash("This field is required", "password")
        isValid = False
    # password does not contain at least one capital letter or one number
    elif not PW_REGEX.search(request.form['password']):
    # or len(request.form['password']) > 15 or len(request.form['password']) < 8:
        flash("Password must contain a number, a capital letter, and be between 8-15 characters", "password")
        isValid = False
    # no confirm password was entered
    if len(request.form['passwordConfirm']) < 1:
        flash("This field is required", "confirmPW")
        isValid = False
    # password and confirm password fields don't match
    elif request.form['password'] != request.form['passwordConfirm']:
        flash("Passwords must match", "confirmPW")
        isValid = False

    if isValid == False:
        return redirect("/")
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        #run query on our database to insert user
        mysql2 = connectToMySQL(db)
        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s)"
        data = {
            'fn': request.form['firstName'],
            'ln': request.form['lastName'],
            'em': request.form['email'],
            'pw': pw_hash
        }
        newUserId = mysql2.query_db(query,data)
        session['userId'] = newUserId
        session["loggedin"] = True
        session['messages'] = ''
        return redirect("/wall")

@app.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL(db)
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {'email': request.form['email']}
    existingUser = mysql.query_db(query, data)
    print(existingUser)
    if len(existingUser) > 0:
    #     #check if password entered matches password in database
        if bcrypt.check_password_hash(existingUser[0]['password'], request.form['password']):
            session['userId'] = existingUser[0]['id']
            print(session)
            print("password found")
            session['loggedin'] = True
            return redirect('/wall')
        else:
            print("password incorrect")
            flash("Password incorrect. Please try again.", "pw")
            return redirect('/')
    else:
        flash("A user associated with this email could not be found. Please try again.","loginemail")
        return redirect("/")

# def checkTimePassed(messages):
#     now = datetime.now()
#     seconds = datetime.time(0,1,0)
#     print(seconds)
#
#
#     for message in messages:
#         timePassed = now - message['created_at']
#
#         # seconds
#         if timePassed < seconds:
#             message['timePassed'] = datetime.strftime("%#s seconds ago")
#             print(message['timePassed'])
#     return messages

@app.route("/wall")
def displayWall():
    if session['loggedin'] == True:
        # query to get all messages sent to user
        mysql = connectToMySQL(db)
        query = "select messages.id, users.first_name as sender_fn, users.last_name as sender_ln, users.email as sender_em, messages.created_at, messages.content from users JOIN messages ON users.id = messages.sender_id JOIN users as user2 on user2.id = messages.recipient_id WHERE recipient_id ="+ str(session['userId']) +";"
        myMessages = mysql.query_db(query)
        #
        # myMessages = checkTimePassed(myMessages)
        # print(myMessages)
        # now = datetime.now()
        # print("now: ", now)
        # for message in myMessages:
        #     print(message['created_at'])
        #     message['timePassed'] = now - message['created_at']
        #     print(message['timePassed'])

        # query to get all users that messages can be sent to
        mysql = connectToMySQL(db)
        query = "SELECT * FROM users WHERE users.id != " + str(session['userId']) + " ORDER BY users.first_name;"
        myUsers = mysql.query_db(query)

        mysql = connectToMySQL(db)
        query = "select messages.id as messageId, users.first_name as sender_fn, users.last_name as sender_ln, users.email as sender_em, messages.created_at, messages.content from users JOIN messages ON users.id = messages.sender_id JOIN users as user2 on user2.id = messages.recipient_id WHERE sender_id =" + str(session['userId']) + ";"
        messages = mysql.query_db(query)

        mysql = connectToMySQL(db)
        query = "SELECT first_name FROM users where id =" + str(session['userId']) + ";"
        user = mysql.query_db(query)
        firstName = user[0]['first_name']
        return render_template("userWall.html", numSent = len(messages), userName = firstName, myMessages = myMessages, numMessages = len(myMessages), friends = myUsers)
    else:
        return redirect("/")

@app.route("/sendMessage", methods=['POST'])
def sendMessage():
    if len(request.form['message']) >= 2:
        mysql = connectToMySQL(db)
        query = "INSERT INTO messages (sender_id, recipient_id, content) VALUES (%(s_id)s, %(r_id)s, %(content)s);"
        data = {
            "s_id": request.form['user'],
            "r_id": request.form['friend'],
            "content": request.form['message']
        }
        messageId = mysql.query_db(query, data)
        print(messageId)

        mysql = connectToMySQL(db)
        query = "SELECT * FROM users WHERE users.id != " + str(session['userId']) + " ORDER BY users.first_name;"
        myUsers = mysql.query_db(query)

        mysql = connectToMySQL(db)
        query = "select messages.id as messageId, users.first_name as sender_fn, users.last_name as sender_ln, users.email as sender_em, messages.created_at, messages.content from users JOIN messages ON users.id = messages.sender_id JOIN users as user2 on user2.id = messages.recipient_id WHERE sender_id =" + str(session['userId']) + ";"
        messages = mysql.query_db(query)
        print(messages, len(messages))
        return render_template("partials/sendMsg.html", numSent = len(messages), friends = myUsers)
    else:
        flash("Messages must be at least 2 characters long", "message")

        # still need to render_template showing message boxes plus error message
        mysql = connectToMySQL(db)
        query = "SELECT * FROM users WHERE users.id != " + str(session['userId']) + " ORDER BY users.first_name;"
        myUsers = mysql.query_db(query)

        mysql = connectToMySQL(db)
        query = "select messages.id as messageId, users.first_name as sender_fn, users.last_name as sender_ln, users.email as sender_em, messages.created_at, messages.content from users JOIN messages ON users.id = messages.sender_id JOIN users as user2 on user2.id = messages.recipient_id WHERE sender_id =" + str(session['userId']) + ";"
        messages = mysql.query_db(query)
        print(messages, len(messages))
        return render_template("partials/sendMsgError.html", numSent = len(messages), friends = myUsers)

@app.route("/delete/<id>")
def deleteMessage(id):
    mysql = connectToMySQL(db)
    query = "DELETE FROM messages WHERE id = " + id + ";"
    mysql.query_db(query)

    mysql = connectToMySQL(db)
    query = "select messages.id, users.first_name as sender_fn, users.last_name as sender_ln, users.email as sender_em, messages.created_at, messages.content from users JOIN messages ON users.id = messages.sender_id JOIN users as user2 on user2.id = messages.recipient_id WHERE recipient_id ="+ str(session['userId']) +";"
    myMessages = mysql.query_db(query)
    return render_template("partials/myMessages.html", myMessages = myMessages, numMessages = len(myMessages))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
