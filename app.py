"""
WebFOCUS embedded in a Python Web Application
MVP App to highlight minimal features through WebFOCUS REST calls
"""

# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import requests
import wfrs
import xml.dom.minidom
import xml.etree.ElementTree as ET

# Import sha256 for password hashing - TBC
# import sha256

# Initialize app
app = Flask(__name__)
app.secret_key = "IBI"


# creates and returns a signed in webfocus session object
def wf_login():
    wf_sess = wfrs.Session()
    wf_sess.mr_sign_on()
    return wf_sess

@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('user_name'):
        print(session['user_name'])
        return redirect(url_for('home'))
    return render_template('index.html')


# Authenticates the login
# Just a driver function for now - accepts any user_name and password
@app.route('/login_auth', methods=['GET', 'POST'])
def login_auth():
    if session.get('user_name'):
        return redirect(url_for('index'))
    if request.method == 'GET':
        return redirect(url_for('index'))

    # grabs information from the forms
    user_name = request.form['user_name']
    # password = request.form['password']

    if user_name:
        # creates a session for the the user
        session['user_name'] = user_name

        """
        # driver
        session['wf_sess'] = True
        # sign on url
        url = 'http://localhost:8080/ibi_apps/rs/ibfs'
        # TODO: make sign on + csrf token retrieval use the proper auth channels
        # TODO: store request session variables into Flask session object 
        payload = {
            'IBIRS_action':'signOn',
            'IBIRS_userName':'admin',
            'IBIRS_password':'admin'
        }
        wf_session = requests.Session()
        wf_session.post(url, payload)
        
        # Save IBI_CSRF_Token_Value from response to sign-on request.

        tree = ET.fromstring(response.content)
        token = tree.find('properties/entry[@key="IBI_CSRF_Token_Value"]')
        token_value = token.attrib['value']
        # save CSRF token to user session
        session['IBIWF_SES_AUTH_TOKEN'] = token_value

        print(response.text)
        breakpoint()
        wf_sess_id = False # parse headers
        session['WF-JSessionID'] = wf_sess_id
        """

        return redirect(url_for('home'))
    else:
        # returns an error message
        error = 'Invalid email or password'
        return redirect(url_for('index'))


@app.route('/home')
def home():
    if not session.get('user_name'):
        #  error="You must be logged in to view this page"
        return redirect(url_for('index'))
    return render_template('home.html')


@app.route('/logout')
def logout():
    session['user_name'] = None
    # session['wf_sess'].mr_signoff()
    return redirect('/')


@app.route('/run_report')
def run_report():

    wf_sess = wf_login()
    
    url = 'http://localhost:8080/ibi_apps/rs/'
    folderName = 'IBFS:/WFC/Repository/Public/'
    reportName = 'Report1.fex'
    '''
    payload = dict()
    payload['IBIRS_action'] = 'run'
    payload['IBIRS_clientPath'] = 'http://localhost:5000/run_report'
    payload['IBIRS_htmlPath'] = 'http://localhost:8080/ibi_apps/html'
    payload['IBFS_comp_user'] = 'srvadmin'
    payload['IBFS_comp_pass'] = 'srvadmin'
    payload['IBIRS_path'] = folderName+reportName
    '''

    payload = { 'IBFS_comp_user': 'srvadmin',
        'IBFS_comp_pass': 'srvadmin',
        'doSubmit': 'Sign in',
        'IBIWF_credAutoPrompt': 'false',
        'IBIRS_path': 'IBFS:/WFC/Repository/Public/Report1.fex'
    }
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    response = wf_sess.post(url, payload)
    with open('test.html', 'w') as f:
        f.write(response.text)
    print(response.headers)
    breakpoint()
    print(response.content)
    return str(response.text)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
    app.secret_key="IBI"
