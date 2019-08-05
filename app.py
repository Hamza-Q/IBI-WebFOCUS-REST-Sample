"""
WebFOCUS embedded in a Python Web Application
MVP highlighting most important WebFOCUS REST calls
TODO: Structure app into a proper directory format
Created by Hamza Qureshi
Hamza_Qureshi@ic.ibi.com
"""


# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash, g
import requests
# wfrs is an API wrapper for WebFOCUS REST calls, currently in development
import wfrs
import xml.etree.ElementTree as ET
import pprint
import datetime

# sha256 hashing for password encryption - TBC
# import sha256


# Initialize app
app = Flask(__name__)
# Put these in config file or env vars?
ibi_client_protocol = "http"
ibi_client_host = "localhost"
ibi_client_port = "8080"
ibi_rest_url =  \
    f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/rs'
ibi_default_folder_path = "WFC/Repository/Public"

# creates and returns a signed in webfocus session object
# TODO: Add proper security, maybe add current user to a list in WF
def wf_login():
    # g is the application context; objects in g are created and destroyed 
    # with the same lifetime as the current request to the server
    # By creating the WF Session within g, we can use one connection per request
    # and sign out at the end, rather than sign in/out for every action

    # Create a WF Session if one does not already exist
    if 'wf_sess' not in g:
        g.wf_sess = wfrs.Session()
        g.wf_sess.mr_sign_on(
            protocol = ibi_client_protocol, 
            host = ibi_client_host, 
            port = ibi_client_port
        )
    return g.wf_sess


# gets xml ET object of response
def list_files_in_path_xml(path=ibi_default_folder_path, file_type=""):
    wf_sess = wf_login()
    
    params = {'IBIRS_action':'list'}
    payload = {}
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    # TODO: Remove hardcoded path URL
    response = wf_sess.get(
        f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/rs/ibfs/{path}',
        params = params, data = payload 
    )
    # print(response)
    with open("_path.xml", "w") as f:
        print(response.text, file=f)
    
    files_xml_response = ET.fromstring(response.text)
    files_xml = files_xml_response.find('rootObject')
    # breakpoint()
    # if requested a certain file type
    if file_type:
        invalid_children = []


        # check children and find those without proper return type

        # TODO: refactor based on https://stackoverflow.com/questions/22817530/elementtree-element-remove-jumping-iteration
        # Note: removing from files_xml within first for loops leads to errors;
        # for loops does not iterate over every child
        for child in files_xml:
            # print(child)
            if child.get("type") != file_type:
                # print("not equals", child.get("type"))
                invalid_children.append(child)
        for child in invalid_children:
            files_xml.remove(child)
    # breakpoint()
    return files_xml

def files_xml_to_list(files_xml):
    item_list = []
    for item in files_xml:
        item_name = item.attrib.get("name")
        item_list.append(item_name)
    return item_list
  

# signs out of WF after request if it exists (closes connection)
@app.teardown_appcontext
def teardown_wf_sess(e=None):
    wf_sess = g.pop('wf_sess', None)
    if wf_sess is not None:
        wf_sess.mr_signoff()


# login page
@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('user_name'):
        return redirect(url_for('home'))
    return render_template('index.html')


# Authenticates the login
# Driver function - accepts any user_name and password
@app.route('/login_auth', methods=['GET', 'POST'])
def login_auth():
    if session.get('user_name'):
        return redirect(url_for('index'))
    if request.method == 'GET':
        return redirect(url_for('index'))

    # grabs information from the forms
    user_name = request.form['user_name']
    # password = request.form['password']

    # authenticate user and password here

    # if acceptable credentials:
    if user_name:
        # creates a session for the the user
        session['user_name'] = user_name

        # Not making any WF requests for now so no need to sign in
        """
        # TODO: make sign on + csrf token retrieval use the proper auth channels
        # Potential TODO: store request session variables into Flask session object 
        
        # Save IBI_CSRF_Token_Value from response to sign-on request.

        session['WF-JSessionID'] = wf_sess_id
        """

        return redirect(url_for('home'))
    else:
        # returns an error message
        # error = 'Invalid email or password'
        return redirect(url_for('index'))


@app.route('/home')
def home():
    if not session.get('user_name'):
        #  error = "You must be logged in to view this page"
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

    files_xml = list_files_in_path_xml(file_type="FexFile")
    # reports is a list of report names
    reports = files_xml_to_list(files_xml)
    return render_template('run_reports.html', reports=reports)


# TODO: Test CORS policy for reports using css/js from ibi_apps via /client_app_redirect
@app.route('/run_report', methods=['GET', 'POST'])
def run_report():
    report_name = request.form.get('report_name')
    # print(report_name)
    if not report_name:
        report_name = "Report1"
    wf_sess = wf_login()
    
    '''
    url = 'http://localhost:8080/ibi_apps/rs/'
    folderName = 'IBFS:/WFC/Repository/Public/'
    folderName2 = 'Public'
    reportName = 'Report1.fex'
    
    payload = dict()
    payload['IBIRS_action'] = 'run'
    payload['IBIRS_clientPath'] = 'http://localhost:5000/run_report'
    payload['IBIRS_htmlPath'] = 'http://localhost:8080/ibi_apps/html'
    payload['IBFS_comp_user'] = 'srvadmin'
    payload['IBFS_comp_pass'] = 'srvadmin'
    payload['IBIRS_path'] = folderName+reportName
    '''
    # Doesn't seem to change anything
    IBIRS_clientPath = 'http://localhost:5000',
    IBIRS_htmlPath = 'http://localhost:8080/ibi_apps/ibi_html'    
    # IBIRS_clientPath='http://wwww.google.com'
    # IBIRS_htmlPath='http://www.bing.com'

    payload = { 
        'IBIRS_action': 'run',
        'IBIRS_clientPath': IBIRS_clientPath,
        'IBIRS_htmlPath': IBIRS_htmlPath,
    }
    
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    # TODO: Remove hardcoded URL
    response = wf_sess.post(f'http://localhost:8080/ibi_apps/rs/ibfs/WFC/Repository/Public/{report_name}',
                            data = payload )
    # response = wf_sess.mr_run_report(folderName2, reportName, 'IBIRS_clientPath=%s' % IBIRS_clientPath)
    #breakpoint()
    #with open('test.html', 'w') as f:
    #    f.write(response.text)
    # print(response.headers)
    # breakpoint()
    # breakpoint()
    # print(response)
    # print(response.content)
    return response.content

# Used to receive webfocus report local files (js/css) from proper source
# Currently always sends response header as {'Content-Type': 'text/html'} even for .js/.css files
# TODO: Look into a better way to do this
@app.route('/ibi_apps/<path:page>', methods=['GET', 'POST'])
def client_app_redirect(page):
    #headers = request.headers
    base_url = f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/'
    wf_sess = wf_login()
    response = wf_sess.get(base_url+page, stream=True)

    # Note: Python requests automatically decodes gzip response so set stream=True for raw bytes
    # My knowledge of compression/encoding is limited so need to verify correct method for this;
    # Should I be returning this gzip compressed response as it currently is coded
    # or should I return the decoded response.content with 'Content-Encoding' header removed?
    # Should any other response headers be changed/removed?
    
    # print(response.headers)   
    # return response.content, response.status_code, response.headers.items()
    return response.raw.read(), response.status_code, response.headers.items()


# Schedules home page: get dropdown of schedules in the Public Repository
@app.route('/schedules')
def schedules():
    if not session.get('user_name'):
        return redirect(url_for('index'))
    # folder = "WFC/Repository/Public"
    
    files_xml = list_files_in_path_xml(file_type="CasterSchedule")
    # schedules is a list of schedule names
    schedules = files_xml_to_list(files_xml)
    
    return render_template('schedules.html', schedules=schedules)

@app.route('/run_schedule', methods=['POST'])
def run_schedule():
    schedule_name = request.form.get('schedule_name')
    if not schedule_name:
        
        schedule_name = "TestSchedule.sch"
    wf_sess = wf_login()
    
    payload = { 
        'IBIRS_action':'run',
    }
    
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    # TODO: Remove hardcoded URL
    response = wf_sess.post(f'http://localhost:8080/ibi_apps/rs/ibfs/WFC/Repository/Public/{schedule_name}',
                            data = payload )
    # print(response)
    # print(response.content)
    return response.content


@app.route('/schedule_report', methods=['POST'])
def schedule_report():
    return "WIP", "404"


# IN DEVELOPMENT
@app.route('/view_schedule_log', methods=['GET'])
def view_schedule_log():
    schedule_name = request.args.get('schedule_name')

    if not schedule_name:
        files_xml = list_files_in_path_xml(file_type="CasterSchedule")
        # schedules is a list of schedule names
        schedules = []
        for item in files_xml:
            schedule_name = item.attrib.get("name")
            schedules.append(schedule_name)
        return render_template("schedule_log_info.html", schedule=None, schedules=schedules)
    wf_sess = wf_login()

    # Get schedule xml object    
    params = { 
        'IBIRS_action':'get',
    }
    
    payload=dict()

    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN


    response = wf_sess.get(f'{ibi_rest_url}/ibfs/WFC/Repository/Public/{schedule_name}',
                            params=params, data=payload )

    # Parse xml for schedule id
    if response.status_code!=200:
        print("error status code != 200")
        return "Error: Could not retrieve schedule."
    root = ET.fromstring(response.content)
    if root.attrib['returncode'] != "10000":
        print("error retcode != 10k")
        return "Error: Could not retrieve schedule."
    for child in root:
        if child.tag == 'rootObject':
            rootObject = child
    schedule_id = rootObject.attrib['handle'] # handle = external id?

    # Parse xml for more schedule information
    for child in rootObject:
        if child.tag == 'casterObject':
            casterObject = child
    lastTimeExecuted_unix = casterObject.attrib.get('lastTimeExecuted')
    if lastTimeExecuted_unix:
        lastTimeExecuted = unixtime_ms_to_datetime(int(lastTimeExecuted_unix))
    nextRunTime = casterObject.attrib.get('nextRunTime')
    if not nextRunTime:
        nextRunTime = "None Scheduled"
    schedule = {
        'name': schedule_name,
        'owner':    casterObject.attrib['owner'],
        'id':   schedule_id,
        'description':  casterObject.attrib.get('description'),
        'summary':      casterObject.attrib.get('summary'),
        'sendMethod':   casterObject.attrib.get('sendMethod'),
        'destinationAddress':   casterObject.attrib.get('destinationAddress'),
        'lastTimeExecuted':     lastTimeExecuted,
        'statusLastExecuted':   casterObject.attrib.get('statusLastExecuted'),
        'nextRunTime':  nextRunTime,
        'procedures':   []
    }
    # Parse xml for procedure information

    for child in casterObject:
        if child.tag =='taskList':
            taskList = child

    # taskList can have multiple items
    for item in taskList:
        procedureName = item.attrib['procedureName']
        schedule['procedures'].append(procedureName)

    # Have schedule id, now use it to retrieve log list 
    url =   f"{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}" + \
            "/ibi_apps/services/LogServiceREST/getLogInfoListByScheduleId"
    
    params = dict()
    params['scheduleId'] = schedule_id

    # re=use payload with csrf token from before
    response = wf_sess.get(url, params=params, data=payload) 
    if response.status_code != 200:
        print("Error: Could not receive log data")
        return "error"

    # log xml response is very messy and unintuitive

    log_root = ET.fromstring(response.content)

    # log_data is a list of log_item attribute dictionaries
    log_data = list()

    # tags are of the form "{url}tag" in the xml; parse out the actual tag
    format_tag = lambda x:x.split('}')[1]

    # timestamps are of the form "yyyy-mm-ddThh:mm:ss.xxx-xx:xx; 
    # omit anything after seconds; split will return tuple as (date_string, time_string)
    # so join these as a string separated by a space
    def format_time(time_string):
        date_str, time_str = time_string.split('T')
        time_str = time_str[:8] # first 8 digits are hh:mm:ss
        return f"{date_str} {time_str}"

    # errorType will be a string of a 1-digit code, mapped in this dictionary:
    error_code_values = {
        "0":"No Error",
        '1':'Error',
        '2':'Warning',
        '6':'Running',
        '7':'Running With Error'
    }
    format_error = lambda error_code:error_code_values.get(error_code)

    # relevant xml data for table column headers as keys.
    # text formattor function as value
    log_formatter = {
        'startTime': format_time,
        'endTime': format_time, 
        'errorType': format_error, 
        'owner': None, 
    }

    for log_item in log_root:
        # log item exists for each time schedule was run

        # attributes is a dictionary of each log item's data
        attributes = dict()

        for attribute in log_item:  # attributes are children of the log items in xml tree
            if attribute.text:      # only care for attributes with text
                key = format_tag(attribute.tag)
                if key in log_formatter:
                    # function from log_formatter that will format the xml text
                    format_func = log_formatter[key] 
                    # if key is 'owner', nothing to format
                    attributes[key] = format_func(attribute.text) if format_func else attribute.text
                    # print(key, attributes[key])
        log_data.append(attributes)

    with open("_f.xml", 'w') as f:
        print(response.text, file=f)

    # sort data by start time, most recent to least recent
    log_data.sort(key = lambda x:x['startTime'], reverse=True)
    # breakpoint()

    return render_template('schedule_log_info.html', schedule=schedule, log_data=log_data)


# TODO
@app.route('/update_schedule')
def update_schedule():
    return render_template("update_schedule.html")



@app.route('/defer_reports')
def defer_reports():
    # print(session.get('deferred_items'))
    if not session.get('user_name'):
        return redirect(url_for('index'))

    files_xml = list_files_in_path_xml(file_type="FexFile")
    # reports is a list of report names
    reports = []
    for item in files_xml:
        report_name = item.attrib.get("name")
        reports.append(report_name)

    return render_template('defer_reports.html', reports=reports)


# Run report deferred and store id info in session
@app.route('/defer_report', methods=['POST'])
def defer_report():
    report_name = request.form.get('report_name')
    tDesc = request.form.get('IBIRS_tDesc')
    if not report_name:
        report_name = "Report1"
    wf_sess = wf_login()
    
    payload = { 'IBIRS_action':'runDeferred' }
    payload['IBIRS_tDesc'] = tDesc
    payload['IBIRS_path'] = f"IBFS:/WFC/Repository/Public/{report_name}"
    payload['IBIRS_parameters'] = "__null"
    payload['IBIRS_args'] = "__null"
    payload['IBIRS_service'] = "ibfs"

    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN
    base_url = f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/rs'

    response = wf_sess.post(base_url,
                            data = payload )
    # print(response)
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
    # print(ticket_name)

    if 'deferred_items' not in session:
        session['deferred_items'] = {}
    session['deferred_items'][ticket_name] = report_name
    session.modified=True 
    # breakpoint()
    # print(session)
    return redirect(url_for('defer_reports'))

# Retrieves deferred report data
@app.route('/get_deferred_report', methods=['GET', 'POST'])
def get_deferred_report():
    ticket_name = request.form.get('ticket_name')
    # print(ticket_name)
    if not ticket_name:
        return "Error: No ticket selected"
    
    wf_sess = wf_login()

    payload = { 
        'IBIRS_action': 'getReport',
        'IBIRS_service': 'defer',
        'IBIRS_htmlPath': 'http://localhost:8080/ibi_apps/ibi_html/'
    }
    payload['IBIRS_ticketName'] = ticket_name

    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    # works with post request but not get
    response = wf_sess.post('http://localhost:8080/ibi_apps/rs',
                            data = payload )
    # print(response)
    # print(response.content)
    return response.content
    

@app.route('/deferred_reports_table', methods=['GET'])
def deferred_reports_table():
    if "user_name" not in session:
        return redirect('/')
    wf_sess = wf_login()

    # retrieve list of deferred tickets
    payload = {"IBIRS_action":"listTickets"}
    payload['IBIRS_service'] = 'defer'
    payload['IBIRS_filters'] = payload['IBIRS_args'] = '__null'
    payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN
    response = wf_sess.get(ibi_rest_url, params=payload) # will be xml


    # convert xml response to minimal dict for easy access
    # TODO: perform xml parsing in new function?
    # breakpoint()
    tree = ET.fromstring(response.text)
    root = tree.find('rootObject')

    deferred_tickets = dict()

    for item in root:
        item_dict = {}
        item_name = item.attrib['name']
        item_dict['desc'] = item.attrib['description']
        # 13 digit unix epoch time in ms listed in xml
        # Convert to 10 digit secs unixtime then format as datetime string
        unixtime_created_ms = int(item.attrib['createdOn'])
        unixtime_created = unixtime_created_ms/1000
        datetime_created = datetime.datetime.fromtimestamp(unixtime_created)
        item_dict['creation_time'] = datetime_created.strftime("%Y-%m-%d %H:%M:%S")
        
        # status and properties are a child of item in xml
        for node in item:
            # Create sub elements
            if node.tag=='status':
                item_dict['status'] = node.attrib['name']

            # parse property tagged entries; reportname is an attribute
            if node.tag =='properties':
                for property_node in node:
                    if property_node.attrib['key'] == 'IBIMR_fex_name':
                        item_dict['report_name'] = property_node.attrib['value']
            

        deferred_tickets[item_name] = item_dict
        # print(item.attrib)
    # tickets_print = pprint.pformat(deferred_tickets)

    # Creates a list of 2-tuples (item_name, item_dict) sorted by datecreated, most to least recent
    deferred_tickets = sorted(deferred_tickets.items(), key= lambda x: x[1]['creation_time'], reverse=True)

    return render_template("deferred_reports_table.html", deferred_items = deferred_tickets)


# IN DEVELOPMENT - will potentially abandon feature
def create_schedule_xml(desc = 'test', notif_email = '', 
                        from_address = 'hamza_qureshi@ic.ibi.com', 
                        distrib_type='email'):

    root = ET.Element('rootObject')
    root.attrib['_jt'] = 'IBFSCasterObject'
    root.attrib['description'] = desc
    root.attrib['type'] = 'CasterSchedule'

    caster = ET.SubElement(root, 'casterObject')
    caster.attrib['_jt'] = 'CasterSchedule'
    caster.attrib['active'] = 'Active'
    caster.attrib['deleteJobAfterRun'] = 'DeleteJobAfterRun'
    caster.attrib['description'] = desc
    caster.attrib['owner'] = 'admin' # probably should use session['user_name']  
    caster.attrib['priority'] = '1'
    caster.attrib['traceType'] = '0'

    notifs = ET.SubElement(caster, 'notification')
    notifs.attrib['_jt'] = 'CasterScheduleNotification'
    notifs.attrib['addressForBriefNotification'] = ''
    notifs.attrib['addressForFullNotification'] = notif_email
    notifs.attrib['description'] = ''
    notifs.attrib['from'] = from_address
    notifs.attrib['subject'] = desc
    notifs.attrib['type'] = 'ALWAYS'

    distrib = ET.SubElement(caster, 'distributionList')
    distrib.attrib['_jt'] = 'array'

    # use a factory to get type and return xml object accordingly
    if distrib_type == 'email':
        distrib.attrib['itemsClass'] = 'CasterScheduleDistribution'
        distrib.attrib['size'] = '1'

        item = ET.SubElement(distrib, 'item')
        item.attrib['_jt'] = 'CasterScheduleDistributionEmail'
        item.attrib['authEnabled'] = 'AuthEnabled' # look into details of this
        item.attrib['authPassword'] = item.attrib['authUserid'] = 'admin' # 
        item.attrib['description'] = 'Email' #
        item.attrib['enabled'] = 'true'
        item.attrib['index'] = '0'
        item.attrib['inLineMessage'] = 'test' # change to input variable
        item.attrib['inLineTaskIndex'] = ''
        item.attrib['mailFrom'] = from_address
        item.attrib['mailReplyAddress'] = ''
        item.attrib['mailServerName'] = 'devmail.ibi.com' # find a way to get this information properly
        item.attrib['mailSubject'] = 'Scheduled Report'
        item.attrib['sendingReportAsAttachment'] = 'true'
        # Where is this information available? Shouldn't have to manually config here
        item.attrib['sslEnabled'] = 'false' 
        item.attrib['tlsEnabled'] = 'false'
        item.attrib['zipFileName'] = '' # shouldn't be used but is it still needed in object?
        item.attrib['zipResult'] = 'false'
        
    x = wfrs.Session().pretty_print_xml(ET.tostring(root))
    print(x)

    # print(ET.dump(root))

    return root

def unixtime_ms_to_datetime(unixtime_ms):
    unixtime = unixtime_ms/1000
    datetime_created = datetime.datetime.fromtimestamp(unixtime)
    datetime_string = datetime_created.strftime("%Y-%m-%d %H:%M:%S")
    return datetime_string

if __name__ == '__main__':
    # create_schedule_xml()
    # secret key randomly generated via commandline:
    # python -c 'import os; print(os.urandom(16))'
    # TODO: Add security; should import from config file or env variable
    app.secret_key=b't]S\xfe\xc7*z\x9b\xde\xde\x94n\xb3\x1e\x85\x14'
    app.run(host='0.0.0.0', port=5000, debug=True)
