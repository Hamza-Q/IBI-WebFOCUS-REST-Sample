"""
WebFOCUS embedded in a Python Web Application
Sample application highlighting most important WebFOCUS REST calls
Created by Hamza Qureshi
hq343@nyu.edu
"""

import wfrs
from flask import Flask, render_template, request, session, \
                    url_for, redirect, flash, g, send_from_directory, \
                    make_response, send_file, abort
import urllib
import requests
import xml.etree.ElementTree as ET
import datetime
import time
import os
from base64 import b64encode


# Initialize app
app = Flask(__name__)
# TODO: Extract these from config file or env vars
ibi_client_protocol = "http"
ibi_client_host = "localhost"
ibi_client_port = "8080"  # standard is 80 for http and 443 for https
ibi_rest_url =  \
    f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/rs'
ibi_default_folder_path = "WFC/Repository/Public"


@app.route('/doc')
def pdf():
    return send_from_directory(
            directory=app.root_path,
            filename="Embedding WebFOCUS into Python Application.pdf"
        )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# Creates and returns a signed in webfocus session object
# TODO: Add proper security, maybe add current user to a list in WF
def wf_login():
    # g is the application context; g objects are created and destroyed
    # with the same lifetime as the current request to the server
    # By creating the WF Session within g, we can use one connection
    # per request and sign out at the end,
    # rather than sign in/out for every action

    # Create a WF Session if one does not already exist
    if 'wf_sess' not in g:
        g.wf_sess = wfrs.WF_Session()
        g.wf_sess.mr_sign_on(
            protocol=ibi_client_protocol,
            host=ibi_client_host,
            port=ibi_client_port
        )
    return g.wf_sess


# gets xml ET object of response
def list_files_in_path_xml(path=ibi_default_folder_path, file_type=""):
    wf_sess = wf_login()
    params = {'IBIRS_action': 'list'}
    # payload = {}
    # if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
    #    payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN
    response = wf_sess.get(
        f'{ibi_rest_url}/ibfs/{path}',
        params=params, # data=payload
    )
    files_xml_response = ET.fromstring(response.content)
    files_xml = files_xml_response.find('rootObject')
    # if requested a certain file type
    if file_type:
        # check children and find those without proper return type
        invalid_children = []
        # TODO: refactor based on
        # https://stackoverflow.com/questions/22817530/elementtree-element-remove-jumping-iteration
        # Note: removing from files_xml within first for loops leads to errors;
        # for loop does not iterate over every child
        for child in files_xml:
            if child.get("type") != file_type:
                invalid_children.append(child)
        for child in invalid_children:
            files_xml.remove(child)
    return files_xml


def files_xml_to_list(files_xml):
    item_list = []
    for item in files_xml:
        item_name = item.get("name")
        item_list.append(item_name)
    return item_list


# signs out of WF after request (closes connection)
@app.teardown_appcontext
def teardown_wf_sess(error=None):
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

    user_name = request.form['user_name']
    password = request.form['password']

    # TODO: authenticate user_name+password

    # if acceptable credentials:
    if user_name and password:
        # creates a session for the the user
        session['user_name'] = user_name
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('index'))


@app.route('/home')
def home():
    if not session.get('user_name'):
        return redirect(url_for('index'))
    return render_template('home.html')


@app.route('/logout')
def logout():
    session['user_name'] = None
    # session['wf_sess'].mr_signoff()
    return redirect('/')


@app.route('/delete_item', methods=['POST'])
def delete_item():
    item_name = request.form.get('item_name')
    item_type = request.form.get('item_type')
    wf_sess = wf_login()
    
    payload = dict()
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    if item_type == 'deferred':
        payload['IBIRS_action'] = 'deleteTicket'
        payload['IBIRS_service'] = 'defer'
        payload['IBIRS_ticketName'] = item_name
        response = wf_sess.post(ibi_rest_url, data=payload)
    else:
        payload['IBIRS_action'] = 'delete'
        response = wf_sess.post(
            f'{ibi_rest_url}/ibfs/WFC/Repository/Public/{item_name}',
            data=payload
        )
    message = f"Deleted Item: {item_name}" if response.status_code == 200 \
              else "Could not delete item"
    flash(message) 
    return redirect(request.referrer)


@app.route('/run_reports')
def run_reports():
    if not session.get('user_name'):
        return redirect(url_for('index'))
    files_xml = list_files_in_path_xml(file_type="FexFile")
    # reports is a list of report names
    reports = files_xml_to_list(files_xml)
    return render_template('run_reports.html', reports=reports)


@app.route('/run_report', methods=['GET', 'POST'])
def run_report():
    report_name = request.form.get('report_name')
    if not report_name:
        return redirect(url_for('run_reports'))
    wf_sess = wf_login()
    # Used to properly return PDF and EXCEL files from WebFOCUS
    turn_off_redirection_xml = \
        '''<rootObject _jt="HashMap">
                <entry>
                    <key _jt="string" value="IBFS_contextVars"/>
                    <value _jt="HashMap">
                        <entry>
                            <key _jt="string" value="IBIWF_redirect"/>
                            <value _jt="string" value="NEVER"/>
                        </entry>
                    </value>
                </entry>
            </rootObject>
        '''
    params = {
        'IBIRS_action': 'run',
        'IBIRS_args': turn_off_redirection_xml
    }
    wf_response = wf_sess.get(
        f'{ibi_rest_url}/ibfs/WFC/Repository/Public/{report_name}',
        params=params
    )
    report = wf_response.content
    content_type = wf_response.headers.get('Content-Type')
    if 'text/html' in content_type:
        response = make_response(report)
        return response
    elif 'image' in content_type:  # send image as base 64 encoded data url
        report_image = b64encode(report).decode('utf-8')
        report_html = f'''
            <html><body align="middle">
                <img src="data:image/png;base64,{report_image}"
                style="background-color:white;"/>
            </body></html>'''
        response = make_response(report_html)
        return response
    response = make_response(report)
    response.headers.set('Content-Type', content_type)
    return response


# Used to receive webfocus report local files (js/css) from proper source
@app.route('/ibi_apps/<path:page>', methods=['GET', 'POST'])
def client_app_redirect(page):
    # Security: Only allow this url to serve content
    # when referred from this application
    referrer_url = request.referrer
    referrer = urllib.parse.urlparse(referrer_url)
    referrer_base_url = f'{referrer.scheme}://{referrer.hostname}'
    referrer_base_url += f':{referrer.port}/' if referrer.port else '/'
    if request.host_url != referrer_base_url:
        abort(403)

    # Use this line of code if you copy ibi html folder into static:
    # return send_from_directory('static', f'ibi_static/{page}')
    
    base_url = f'{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}/ibi_apps/'
    wf_sess = wf_login()

    # Python requests automatically decodes a gzip-encoded response
    # so set stream=True for raw bytes
    response = wf_sess.get(base_url+page, stream=True)
    # Forward response content and headers to user
    return response.raw.read(), response.status_code, response.headers.items()



# Schedules home page: get dropdown of schedules in the Public Repository
@app.route('/schedules')
def schedules():
    if not session.get('user_name'):
        return redirect(url_for('index'))

    sched_files_xml = list_files_in_path_xml(file_type="CasterSchedule")

    if not request.args.get("expand"):
        schedules = files_xml_to_list(sched_files_xml)
        return render_template('schedules.html', schedules=schedules)
    else:
        schedule_items = dict()
        for item in sched_files_xml:  # always a schedule item
            item_dict = {}
            item_name = item.get('name')
            item_dict['desc'] = item.get('description')
            item_dict['summary'] = item.get('summary')
            # 13 digit unix epoch time in ms listed in xml
            # Convert to 10 digit secs unixtime then format as datetime string
            unixtime_created_ms = int(item.get('createdOn'))
            datetime_created = unixtime_ms_to_datetime(unixtime_created_ms)
            item_dict['creation_time'] = datetime_created
            # casterObject is a child of item
            casterObject = item.find('casterObject')

            # Only support email schedules
            if casterObject.get('sendMethod') != 'EMAIL':
                continue

            # Get destination address, owner, last time executed by
            # parsing property tagged entries; reportname is an attribute
            item_dict['destinationAddress'] = casterObject.get('destinationAddress')
            item_dict['owner'] = casterObject.get('owner')
            schedule_items[item_name] = item_dict

        # Creates a list of 2-tuples (item_name, item_dict) sorted by datecreated, most to least recent
        schedule_items_list = sorted(
            schedule_items.items(), 
            key=lambda x: x[1]['creation_time'], 
            reverse=True
        )

        return render_template('schedules.html', schedules=schedule_items_list, expand=True)

@app.route('/run_schedule', methods=['POST'])
def run_schedule():
    schedule_name = request.form.get('schedule_name')
    wf_sess = wf_login()
    payload = {
        'IBIRS_action': 'run',
    }
    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    response = wf_sess.post(
        f'{ibi_rest_url}/ibfs/WFC/Repository/Public/{schedule_name}',
        data=payload 
    )

    if response.status_code == 200:
        flash(f"Successfully added schedule: {schedule_name} to the queue.")
    elif response.status_cdode == 404:
        flash(f"Error: Could not run schedule {schedule_name}")
    else:
        flash(f"Undetermined error; Response status code: {response.status_code}")
    return redirect(request.referrer)


@app.route('/view_schedule_log', methods=['GET'])
def view_schedule_log():
    schedule_name = request.args.get('schedule_name')
    # If no schedule requested, give users a dropdown of available
    if not schedule_name: 
        files_xml = list_files_in_path_xml(file_type="CasterSchedule")
        # schedules is a list of schedule names
        schedules = []
        for item in files_xml:
            schedule_name = item.get("name")
            schedules.append(schedule_name)
        return render_template(
            "schedule_log_info.html", schedule=None, schedules=schedules
        )
    wf_sess = wf_login()
    # Get schedule xml object
    params = {'IBIRS_action': 'get'}
    response = wf_sess.get(
        f'{ibi_rest_url}/ibfs/WFC/Repository/Public/{schedule_name}',
        params=params
    )
    # Parse xml for schedule id
    if response.status_code != 200:
        return 'Error: Could not communicate with WebFOCUS Client' + \
            f'<br> <a href="{url_for("schedules")}">Go Back</a>', 404
    root = ET.fromstring(response.content)
    if root.attrib['returncode'] != "10000":
        print("error retcode != 10k")
        return 'Error 404: Could not retrieve selected schedule.' + \
            f'<br> <a href="{url_for("schedules")}">Go Back</a>', 404
    for child in root:
        if child.tag == 'rootObject':
            rootObject = child
    schedule_id = rootObject.attrib['handle'] 
    # Parse xml for more schedule information
    for child in rootObject:
        if child.tag == 'casterObject':
            casterObject = child
    lastTimeExecuted_unix = casterObject.get('lastTimeExecuted')
    if lastTimeExecuted_unix:
        lastTimeExecuted = unixtime_ms_to_datetime(int(lastTimeExecuted_unix))
    nextRunTime = casterObject.get('nextRunTime')
    if not nextRunTime:
        nextRunTime = "None Scheduled"
    schedule = {
        'Name': schedule_name,
        'Owner':    casterObject.get('owner'),
        'ID':   schedule_id,
        'Description':  casterObject.get('description'),
        'Summary':      casterObject.get('summary'),
        'Send Method':   casterObject.get('sendMethod'),
        'Destination Address':   casterObject.get('destinationAddress'),
        'Last Time Executed':     lastTimeExecuted,
        'Status Last Executed':   casterObject.get('statusLastExecuted'),
        'Next Run Time':  nextRunTime,
        'Procedures':   []
    }
    # Parse xml for procedure information

    for child in casterObject:
        if child.tag == 'taskList':
            taskList = child

    # taskList can have multiple items
    for item in taskList:
        procedureName = item.get('procedureName')
        schedule['Procedures'].append(procedureName)

    # Have schedule id, now use it to retrieve log list 
    url = f"{ibi_client_protocol}://{ibi_client_host}:{ibi_client_port}" + \
          "/ibi_apps/services/LogServiceREST/getLogInfoListByScheduleId"

    params = dict()
    params['scheduleId'] = schedule_id

    log_response = wf_sess.get(url, params=params)
    if log_response.status_code != 200:
        flash(f"Could not receive log data for {schedule_name}")
        return render_template('schedule_log_info.html', schedule=schedule)

    log_root = ET.fromstring(log_response.content)
    # log_data is a list of log_item attribute dictionaries
    log_data = list()

    # tags are of the form "{url}tag" in the xml; parse out the actual tag
    format_tag = lambda x: x.split('}')[1]

    # timestamps are of the form "yyyy-mm-ddThh:mm:ss.xxx-xx:xx; 
    # omit anything after seconds; split will return tuple as 
    # (date_string, time_string)
    # so join these as a string separated by a space
    def format_time(time_string):
        date_str, time_str = time_string.split('T')
        time_str = time_str[:8]  # first 8 digits are hh:mm:ss
        return f"{date_str} {time_str}"

    # errorType will be a string of a 1-digit code, mapped in this dictionary:
    error_code_values = {
        "0": "None",
        '1': 'Error',
        '2': 'Warning',
        '6': 'Running',
        '7': 'Running With Error'
    }

    format_error = lambda error_code: error_code_values.get(error_code)

    # relevant xml data for table column headers as keys.
    # text formattor function as value
    log_formatter = {
        'startTime': format_time,
        'endTime': format_time, 
        'errorType': format_error, 
        'owner': lambda x: x,  # Nothing to format
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
                    attributes[key] = format_func(attribute.text)
        log_data.append(attributes)

    # sort data by start time, most recent to least recent
    log_data.sort(key=lambda x: x['startTime'], reverse=True)

    return render_template('schedule_log_info.html', schedule=schedule, log_data=log_data)




@app.route('/defer_reports')
def defer_reports():
    if not session.get('user_name'):
        return redirect(url_for('index'))

    files_xml = list_files_in_path_xml(file_type="FexFile")
    
    reports = []

    for item in files_xml:
        report_name = item.get("name")
        reports.append(report_name)

    return render_template('defer_reports.html', reports=reports)


# Run report deferred and store id info in session
@app.route('/defer_report', methods=['POST'])
def defer_report():
    report_name = request.form.get('report_name')
    tDesc = request.form.get('IBIRS_tDesc')

    wf_sess = wf_login()
    payload = {'IBIRS_action': 'runDeferred' }
    payload['IBIRS_tDesc'] = tDesc
    payload['IBIRS_path'] = f"IBFS:/WFC/Repository/Public/{report_name}"
    payload['IBIRS_parameters'] = "__null"
    payload['IBIRS_args'] = "__null"
    payload['IBIRS_service'] = "ibfs"

    if wf_sess.IBIWF_SES_AUTH_TOKEN is not None:
        payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN

    response = wf_sess.post(ibi_rest_url, data=payload)

    if response.status_code != 200:
        print("Error status code != 200")
        flash("Error: Could not defer report.")
        return redirect(url_for('defer_reports'))

    root = ET.fromstring(response.content)

    # returncode 10000 means it ran successfully
    if root.get('returncode') != "10000":
        print("Error retcode != 10k")
        flash("Error: Could not defer report.")
        return redirect(url_for('defer_reports'))

    flash(f"Successfully ran deferred report: {report_name}")
    return redirect(url_for('defer_reports'))


# Retrieves deferred report data
@app.route('/get_deferred_report', methods=['GET', 'POST'])
def get_deferred_report():
    ticket_name = request.form.get('ticket_name')
    if not ticket_name:
        return "Error: No ticket selected"
    wf_sess = wf_login()
    turn_off_redirection_xml = \
        '''<rootObject _jt="HashMap">
                <entry>
                    <key _jt="string" value="IBFS_contextVars"/>
                    <value _jt="HashMap">
                        <entry>
                            <key _jt="string" value="IBIWF_redirect"/>
                            <value _jt="string" value="NEVER"/>
                        </entry>
                    </value>
                </entry>
            </rootObject>
        '''
    params = {
        'IBIRS_action': 'getReport',
        'IBIRS_service': 'defer',
        'IBIRS_args': turn_off_redirection_xml
    }
    params['IBIRS_ticketName'] = ticket_name
    wf_response = wf_sess.get(ibi_rest_url, params=params)
    report = wf_response.content
    content_type = wf_response.headers.get('Content-Type')
    if 'text/html' in content_type:
        response = make_response(report)
        return response
    elif 'image' in content_type:  # send image as base 64 encoded data url
        report_image = b64encode(report).decode('utf-8')
        report_html = f'''
            <html><body align="middle">
                <img src="data:image/png;base64,{report_image}"
                style="background-color:white;"/>
            </body></html>'''
        response = make_response(report_html)
        return response
    elif 'pdf' in content_type:
        print(wf_response.status_code)
        response = make_response(report)
        response.headers.set('Content-Type', content_type)
        return response    
    response = make_response(report)
    response.headers.set('Content-Type', content_type)
    return response


@app.route('/deferred_reports_table', methods=['GET'])
def deferred_reports_table():
    if "user_name" not in session:
        return redirect('/')
    wf_sess = wf_login()

    # used to sort table in html
    sort_reversed = True if request.args.get('reverse') == 'True' else False

    # retrieve list of deferred tickets
    payload = {"IBIRS_action": "listTickets"}
    payload['IBIRS_service'] = 'defer'
    payload['IBIRS_filters'] = payload['IBIRS_args'] = '__null'
    payload['IBIWF_SES_AUTH_TOKEN'] = wf_sess.IBIWF_SES_AUTH_TOKEN
    response = wf_sess.get(ibi_rest_url, params=payload)  # will be xml
    # convert xml response to minimal dict for easy access
    tree = ET.fromstring(response.text)
    response_code = tree.get("returncode")
    if response_code != '10000':
        flash("Error receiving deferred items")
        return redirect(url_for('home'))
    root = tree.find('rootObject')

    deferred_tickets = dict()
    for item in root:
        item_dict = {}
        item_name = item.attrib['name']
        item_dict['desc'] = item.attrib['description']
        # 13 digit unix epoch time in ms listed in xml
        # Convert to 10 digit secs unixtime then format as datetime string
        unixtime_created_ms = int(item.attrib['createdOn'])
        item_dict['creation_time'] = unixtime_ms_to_datetime(unixtime_created_ms)
        # status and properties are a child of item in xml
        for node in item:
            # Create sub elements
            if node.tag =='status':
                status = node.attrib['name']
                item_dict['status'] = 'READY' if status == 'CTH_DEFER_READY' \
                    else 'NOT READY'

            # parse property tagged entries; reportname is an attribute
            if node.tag == 'properties':
                for property_node in node:
                    if property_node.attrib['key'] == 'IBIMR_fex_name':
                        item_dict['report_name'] = property_node.attrib['value']
            
        deferred_tickets[item_name] = item_dict

    # Creates a list of 2-tuples (item_name, item_dict) sorted by datecreated
    # Default is most to least recent; can be changed by reverse flag in query
    deferred_tickets = sorted(
        deferred_tickets.items(), 
        key=lambda x: x[1]['creation_time'], 
        reverse=not sort_reversed
    )

    return render_template(
        "deferred_reports_table.html", 
        deferred_items=deferred_tickets, 
        reverse=sort_reversed
    )


def unixtime_ms_to_datetime(unixtime_ms):
    unixtime = unixtime_ms/1000
    datetime_created = datetime.datetime.fromtimestamp(unixtime)
    datetime_string = datetime_created.strftime("%Y-%m-%d %H:%M:%S")
    return datetime_string

if __name__ == '__main__':
    # secret key randomly generated via commandline:
    # python -c 'import os; print(os.urandom(16))'
    # TODO: Add security; should import from config file or env variable
    app.secret_key = b't]S\xfe\xc7*z\x9b\xde\xde\x94n\xb3\x1e\x85\x14'
    app.run(host='0.0.0.0', port=5000, debug=True)
