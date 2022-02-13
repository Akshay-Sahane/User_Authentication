from flask import Flask,render_template,request,redirect,url_for,session
import pymysql
import random
from twilio.rest import Client
import re

con=None
cur=None
app = Flask(__name__)
app.secret_key='super secret key'

# database connection function
def connectToDb():
    global con,cur
    con=pymysql.connect(host='localhost',user='root',password='12345',database='rdemo')
    cur=con.cursor()

# disconnect database function
def disconnectDB():
    cur.close()
    con.close()

# index page/login page
@app.route('/')
def index():
    return render_template('index.html')

# function to add new user i.e.create
@app.route('/newuser',methods=['get','post'])
def registeruser():
    connectToDb()
    query="create table if not exists record(id int auto_increment primary key,email varchar(100) Not Null,phone varchar(100) Not Null,password varchar(100) Not Null);"
    cur.execute(query)
    disconnectDB()
    if request.method=='POST':
        data=request.form
        if(alreadyuser(data['email'])):
            smsg="you have already registered"
            return render_template('login.html',smsg=smsg)
        if(len(data['phone'])==10):
            pass
        else:
            amsg='phone no should be 10 digit'
            return render_template('register.html',amsg=amsg)
        password=data['password']
        if(len(password)<8):
            amsg="password should contain at least 8 characters"
            return render_template('register.html',amsg=amsg)
        elif not re.search('[a-z]',password):
            amsg="password should contain at least one lower case character"
            return render_template('register.html',amsg=amsg)
        elif not re.search('[A-Z]',password):
            amsg="password should contain at least one upper case character"
            return render_template('register.html',amsg=amsg)
        elif not re.search('[0-9]',password):
            amsg="password should contain at least one number"
            return render_template('register.html',amsg=amsg)
        elif not re.search('[_@$#^*]',password):
            amsg="password should contain at least one special character"
            return render_template('register.html',amsg=amsg)
        elif adduser(data['email'],data['phone'],data['password']):
            smsg="registered successfully!"
            return render_template('login.html',smsg=smsg)
        else:
            msg="registration fail"
        return render_template('register.html',msg=msg)
    return render_template('register.html')

def alreadyuser(email):
    try:
        connectToDb()
        query="select * from record where email=%s;"
        cur.execute(query,(email))
        one=cur.fetchone()
        if one:
            disconnectDB()
            return True
        else:
            disconnectDB()
            return False
    except:
        disconnectDB()
        return False
# save new-user data in database
def adduser(email,phone,password):
    try:
        connectToDb()
        query="insert into record(email,phone,password)values(%s,%s,%s);"
        cur.execute(query,(email,phone,password))
        con.commit()
        disconnectDB()
        return True
    except:
        disconnectDB()
        return False

def getpass(email):
    try:
        connectToDb()
        q1="select password from record where email=%s;"
        cur.execute(q1,(email))
        data=cur.fetchone()
        disconnectDB()
        return data
    except:
        return "error"



# user login function i.e.read
@app.route('/login',methods=['GET','POST'])
def login():
    emsg=''
    if request.method=='POST':
        uname=request.form['uname']
        password=request.form['upass']
        connectToDb()
        cur.execute("select * from record where email=%s and password=%s",(uname,password))
        record=cur.fetchone()
        if record:
            session['loggedin']=True
            session['uname']=record[1]
            disconnectDB()
            return redirect(url_for('home1'))
        else:
            disconnectDB()
            emsg='Invalid username or password.Try Again!'
    return render_template('login.html',emsg=emsg)

# page to display after login 
@app.route('/home1')
def home1():
    return render_template('home1.html',uname=session['uname'])

# logout user
@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('uname',None)
    return redirect(url_for('login'))

# delete user account i.e.delete
@app.route('/delete',methods=['get','post'])
def delete():
    if request.method=='POST':
        connectToDb()
        em=request.form['username']
        ps=request.form['upass']
        if(udcheck(em,ps)):
            dq="delete from record where email=%s AND password=%s"
            cur.execute(dq,(em,ps))
            con.commit()
            disconnectDB()
            return redirect(url_for('registeruser'))
        else:
            disconnectDB()
            nf="invalid credentials"
            return render_template('delete.html',nf=nf)
    else:
        return render_template('delete.html')
# before deleting acc. check user is valid or not
def udcheck(em,ps):
    try:
        connectToDb()
        query="select * from record where email=%s AND password=%s;"
        cur.execute(query,(em,ps))
        urec=cur.fetchone()
        if urec:
            return True
        else:
            
            return False
    except:
        return False



# password reset by sending otp i.e.update
@app.route('/pforgot',methods=['get','post'])
def pforgot():
    fmsg=''
    if request.method=='POST':
        data1=request.form['phone']
        if ucheck(data1):   #check user is present or not
            phonemsg(data1)
            return render_template('otp.html')
        else:
            fmsg='user not found'
        return render_template('pforgot.html',fmsg=fmsg)
    return render_template('pforgot.html')
# check user present or not
def ucheck(no):
    try:
        connectToDb()
        query="select * from record where phone=%s;"
        cur.execute(query,(no))
        urec=cur.fetchone()
        if urec:
            disconnectDB()
            return True
        else:
            disconnectDB()
            return False
    except:
        return False

# generate 4-digit random no to send otp
def rand():
    global n
    n=random.randint(1000,9999)
    return n

# send otp as a text msg via twilio
def phonemsg(d1):
    account_sid="enter your twilio account_sid here"
    auth_token="enter your twilio auth_token here"
    client=Client(account_sid,auth_token)
    m="otp for resetting password is:"+str(rand())
    d2='+91'
    d1=d2+d1
    message=client.messages.create(body=m,from_="+16067160394",to=d1)

# if user present then otp will be sent and user will be redirect to verification page to verify otp
@app.route('/otpcheck',methods=['get','post'])
def otpcheck():
    eotp=request.form['otp']
    if n==int(eotp):
        return render_template('preset.html')
    else:
        iotp="invalid otp"
        return render_template('pforgot.html',iotp=iotp)

# after verifying otp user have to set newpassword i.e.update 
@app.route('/preset',methods=['get','post'])
def preset():
    if(request.method=='POST'):
        connectToDb()
        data=request.form['username']
        data1=request.form['newpass']
        if(len(data1)<8):
            amsg="password should contain at least 8 characters"
            return render_template('preset.html',amsg=amsg)
        elif not re.search('[a-z]',data1):
            amsg="password should contain at least one lower case character"
            return render_template('preset.html',amsg=amsg)
        elif not re.search('[A-Z]',data1):
            amsg="password should contain at least one upper case character"
            return render_template('preset.html',amsg=amsg)
        elif not re.search('[0-9]',data1):
            amsg="password should contain at least one number"
            return render_template('preset.html',amsg=amsg)
        elif not re.search('[_@$#^*]',data1):
            amsg="password should contain at least one special character"
            return render_template('preset.html',amsg=amsg)
        else:
            que="update record set password=%s where email=%s"
            cur.execute(que,(data1,data))
            con.commit()
            disconnectDB()
            smsg="password reset successfully!"
        return render_template('login.html',smsg=smsg)
    else:
        disconnectDB()
        return render_template('preset.html')

if __name__=='__main__':
    app.run(debug=True)