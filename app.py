"""
WebFOCUS embedded in a Python Web Application
MVP highlighting most important WebFOCUS REST calls
Created by Hamza Qureshi
Hamza_Qureshi@ic.ibi.com
"""

# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
# import flask_cors
import requests
# wfrs is an API wrapper for WebFOCUS Rest calls, currently in development
import wfrs
import xml.etree.ElementTree as ET

# sha256 hashing for password encryption - TBC
# import sha256


# Initialize app
app = Flask(__name__)
app.secret_key = "IBI"


# creates and returns a signed in webfocus session object
def wf_login():
    wf_sess = wfrs.Session()
    wf_sess.mr_sign_on()
    return wf_sess


# dummy login page
@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('user_name'):
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

@app.route('/run_reports')
def run_reports():
    if not session.get('user_name'):
        return redirect(url_for('index'))
    return render_template('run_reports.html')


# TODO: Test CORS policy for reports using css/js from ibi_apps
@app.route('/run_report', methods=['GET', 'POST'])
#@flask_cors.cross_origin(origins='localhost', headers=['Content-Type', 'Authorization'])
def run_report():
    report_name = request.form.get('report_name')
    if not report_name:
        report_name = "Report1"
    wf_sess = wf_login()
    
    url = 'http://localhost:8080/ibi_apps/rs/'
    folderName = 'IBFS:/WFC/Repository/Public/'
    folderName2 = 'Public'
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

    IBIRS_clientPath = 'http://localhost:5000/client_app_redirect',
    IBIRS_htmlPath = 'http://localhost:8080/ibi_apps/ibi_html'    
    #IBIRS_clientPath='http://wwww.google.com'
    #IBIRS_htmlPath='http://www.bing.com'

    payload = { 
        'IBFS_service': 'ibfs',
        'IBFS_comp_user': 'srvadmin',
        'IBFS_comp_pass': 'srvadmin',
        'doSubmit': '',
        'IBIWF_credAutoPrompt': 'false',
        'IBIRS_path': 'IBFS:/WFC/Repository/Public/Report1.fex',
        'IBIRS_clientPath': IBIRS_clientPath,
        'IBIRS_htmlPath': IBIRS_htmlPath,
    }
    payload2 = { 
        'IBIRS_action':'run',

    }
    
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN
        payload2['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN


    response = wf_sess.post(f'http://localhost:8080/ibi_apps/rs/ibfs/WFC/Repository/Public/{report_name}.fex',
                            data = payload2 )
    # response = wf_sess.mr_run_report(folderName2, reportName, 'IBIRS_clientPath=%s' % IBIRS_clientPath)
    #breakpoint()
    #with open('test.html', 'w') as f:
    #    f.write(response.text)
    # print(response.headers)
    # breakpoint()
    # breakpoint()
    print(response)
    # print(response.content)
    return response.content
'''
# used to receive webfocus report html local files from proper destination
@app.route('/ibi_apps/<path:page>', methods=['GET', 'POST'])
@flask_cors.cross_origin(origins='localhost', headers=['Content-Type', 'Authorization'])
def client_app_redirect(page):
    # return redirect('http://localhost:8080/ibi_apps/'+page)
    #headers = request.headers
    
    #url = 'http://localhost:8080/ibi_apps/' + page

    #response = requests.get(url, data=request.data, headers=headers)
    #print(response)
    # breakpoint()
    wf_sess=wf_login()
    wf_sess.headers['Accept']=request.headers['Accept']
    print(request.headers, request.url)
    response = wf_sess.get('http://localhost:8080/ibi_apps/'+page)
    # breakpoint()
    print(response.headers, response.url)
    return response.content
    #return response.content
'''

@app.route('/schedules')
def schedules():
    if not session.get('user_name'):
        return redirect(url_for('index'))
    return render_template('schedules.html')

@app.route('/schedule_item', methods=['POST'])
def schedule_item():
    schedule_name = request.form.get('schedule_name')
    if not schedule_name:
        schedule_name = "TestSchedule"
    wf_sess = wf_login()
    
    payload = { 
        'IBIRS_action':'run',
    }
    
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    response = wf_sess.post(f'http://localhost:8080/ibi_apps/rs/ibfs/WFC/Repository/Public/{schedule_name}.sch',
                            data = payload )
    # print(response)
    # print(response.content)
    return response.content

@app.route('/defer_reports')
def defer_reports():
    print(session.get('deferred_items'))
    if not session.get('user_name'):
        return redirect(url_for('index'))
    return render_template('defer_reports.html')

@app.route('/defer_report', methods=['POST'])
def defer_report():
    report_name = request.form.get('report_name')
    tDesc = request.form.get('IBIRS_tDesc')
    if not report_name:
        report_name = "Report1"
    wf_sess = wf_login()
    
    payload = { 'IBIRS_action':'runDeferred' }
    payload['IBIRS_tDesc'] = tDesc
    payload['IBIRS_path'] = f"IBFS:/WFC/Repository/Public/{report_name}.fex"
    payload['IBIRS_parameters'] = "__null"
    payload['IBIRS_args'] = "__null"
    payload['IBIRS_service'] = "ibfs"

    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    response = wf_sess.post(f'http://localhost:8080/ibi_apps/rs',
                            data = payload )
    print(response)
    # print(response.content)

    # WIP:  Parse XML for ticket id, store in session['deferred_items'] dict 
    #       with key=ticket_name, value=report_name
    if response.status_code!=200:
        print("error status code != 200")
        return "Error: Could not defer report."
    root = ET.fromstring(response.content)
    if root.attrib['returncode'] != "10000":
        print("error retcode != 10k")
        return "Error: Could not defer report."
    for child in root:
        if child.tag == 'rootObject':
            rootObject = child
    ticket_name = rootObject.attrib['name']
    print(ticket_name)

    if 'deferred_items' not in session:
        session['deferred_items'] = {}
    session['deferred_items'][ticket_name] = report_name
    session.modified=True 
    # breakpoint()
    print(session)
    return redirect(url_for('defer_reports'))


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
    app.secret_key="IBI"
