# Prototype
#
#  A Python wrapper for WebFOCUS RESTful Web Services using
#  Requests: HTTP for Humans. See python-requests.org
#
#  Note: this software is for demonstration purposes only
#        and is not certified to be used in a production
#        environment.
#
# filename:  wfrs.py
#  version:  15
#     date:  2019-02-12
#   author:  Ira Kaplan, Information Builders
#    email:  ira_kaplan@ibi.com
#
# changes
# version 14: added rc_get_library_access_list()



import base64
import csv
import functools
import xml.dom.minidom
import xml.etree.ElementTree as ET
import requests


# Function and method naming conventions, prefixes
#
# sa - Security Administration
# mr - WebFOCUS Repository (formermly Managed Reporting)
# rs - Reporting Server
# rc - Report Caster
# ex - extended or helper functions


class ExRequest:
    """Pseudo request object for supporting ex_ or extended functions."""

    def __init__(self):
        self.headers = None
        self.body = None


class ExRetval:
    """Pseudo response object for supporting ex_ or extended functions."""

    def __init__(self):
        self.text = (
            '<?xml version="1.0" encoding="UTF-8"><extended message="Extended '
            'function for WebFOCUS 8 RESTful Web Services for Everyone">'
            '</extended>'
            )
        self.url = 'http://www.InformationBuilders.com'
        self.content = (
            '<?xml version="1.0" encoding="UTF-8"><extended message="Extended '
            'function for WebFOCUS 8 RESTful Web Services for Everyone">'
            '</extended>'
            )

        self.request = ExRequest()
        self.request.headers = 'This is a dummy header'
        self.request.body = 'This is a dummy body'


class Session(requests.Session):
    """Extend the features of Requests' Session object."""

    # --[ Helper functions ]--------------------------------------------------
     
    #----------------------------[ pretty_print_xml ]-----------------------------
    def pretty_print_xml(self, xml_string=None):
        '''Reformat xml string suitable for reading.'''

        # See: http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python

        try:
            xml_parsed = xml.dom.minidom.parseString(xml_string)
        except:
            pretty_xml_as_string = '<Response not formatted as XML, cannot pretty print>'
        else:
            pretty_xml_as_string = xml_parsed.toprettyxml()

        return pretty_xml_as_string
        

   # ------------------------------[ sort_records ]------------------------------
    def sort_records(self, records, *sort_keys):
        '''Sort records represented as a list of dictionaries.'''

        # for nested sorts, start with the last sort key
        sort_keys = list(sort_keys)
        sort_keys.reverse()
        
        
        for sort_key in sort_keys:
            # Python sorts a list in place, no value returned
            records.sort(key=lambda record: record[sort_key].lower())

        return records



    # ------------------------------[ write_records_to_csv ]----------------------
    def write_records_to_csv(self, filename, fieldnames, records):
        '''Write list of dictionaries as csv file.

        See https://pymotw.com/2/csv/index.html
        '''

        with open(filename, 'wt', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames, restval='', 
                                    extrasaction='ignore', 
                                    dialect='excel', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(records)
            

    # ------------------------[ tabular_print_to_string ]---------------------
    def tabular_print_to_string(self, records, fieldnames):
        ''' Print records, a list of dictionaries, in columnar format.
            Columns are in order of fieldnames passed as a list.
        '''

        buffer = ''
        column_padding = 3
        underline_character = '-'

        # handle missing keys in records: 'if fieldname in record...'       
        column_widths = dict(zip(fieldnames, map(lambda fieldname: max([ len(record[fieldname] if fieldname in record else '') for record in records]) + column_padding, fieldnames)))

       # adjust column widths so no column is narrower than its title
        column_widths = { k : max(len(k) + column_padding, column_widths[k])  for k in column_widths.keys() }

        # print header row
        for fieldname in fieldnames:
            buffer += '%-*s' % (column_widths[fieldname], fieldname)
        buffer += '\n'

        # print underline row
        for fieldname in fieldnames:
            buffer += '%-*s' % (column_widths[fieldname], underline_character * (column_widths[fieldname] - 3)) 
        buffer += '\n'
        
        # print data records
        for record in records:
            for fieldname in fieldnames:
                buffer += '%-*s' % (column_widths[fieldname], record[fieldname] if fieldname in record else '') 
            buffer += '\n'    

        return buffer




    # --[ WebFOCUS Security Administration: list users ]----------------------
    def sa_list_users(self):
        """Listing Users."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/USERS'.format(self.protocol,
                                                              self.host,
                                                              self.port)

        return self.request(method=method, url=url, params=params)

    def sa_list_groups(self, group_name=''):
        """WebFOCUS Security Administration: Listing Groups.

        List groups in the level immediately below the parent group.
        """

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/GROUPS/{}'.format(
                                                             self.protocol,
                                                             self.host,
                                                             self.port,
                                                             group_name)

        return self.request(method=method, url=url, params=params)

    def sa_list_privileges(self):
        """WebFOCUS Security Administration: Listing Privileges."""

        method = 'get'
        params = {'IBIRS_action': 'privileges'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)

        return self.request(method=method, url=url, params=params)

    def sa_list_roles(self):
        """WebFOCUS Security Administration: Listing Roles."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/ROLES'.format(self.protocol,
                                                              self.host,
                                                              self.port)

        return self.request(method=method, url=url, params=params)

    def sa_list_users_in_group(self, group_name=''):
        """WebFOCUS Security Administration: Listing Users Within a Group."""

        method = 'get'

        args = """<object _jt="HashMap">
                    <entry>
                      <key _jt="string" value="TYPE"/>
                      <value _jt="string" value="USERS"/>
                    </entry>
                  </object>"""

        params = {'IBIRS_action': 'get', 'IBIRS_args': args}

        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/GROUPS/{}'.format(
                                                             self.protocol,
                                                             self.host,
                                                             self.port,
                                                             group_name)

        return self.request(method=method, url=url, params=params)



    # user_name is the same as userid in the REST service's documentation.
    # user_name is a more meaningful label than userid
    def sa_add_or_update_user(self, user_name='',
                              replace_userid_properties='false',
                              userid_title='',
                              email_address='',
                              password='',
                              group_name='EVERYONE',
                              status='ACTIVE'):
        """WebFOCUS Security Administration: Adding and Updating a User."""

        method = 'post'

        object = """<object _jt="IBFSUserObject"
                      description="{}"
                      email="{}"
                      password="{}"
                      type="User"
                      primaryGroupPath="IBFS:/SSYS/GROUPS/{}">
                        <status _jt="IBSSUserStatus" name="{}"/>
                    </object>""".format(userid_title, email_address, password,
                                        group_name, status)

        data = {
            'IBIRS_action': 'put',
            'IBIRS_object': object,
            'IBIRS_replace': replace_userid_properties
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/USERS/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            user_name)

        # Add the CSRF token value to the body (data) of the request.
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_change_password(self, userid='', password=''):
        """WebFOCUS Security Administration: Changing a Password for a User."""

        method = 'post'
        data = {
            'IBIRS_action': 'changePassword',
            'IBIRS_userName': userid,
            'IBIRS_password': password
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_delete_user(self, user_name=None):
        """WebFOCUS Security Administration: Deleting a User."""

        method = 'delete'
        data = {'IBIRS_action': 'delete'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/USERS/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            user_name)

        # Add the CSRF token value to the body (data) of the request.
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_add_or_update_group(self, group_name=None, description='',
                               replace_group_properties='false'):
        """WebFOCUS Security Administration: Adding and Updating a Group."""

        method = 'post'

        object = """<object _jt="IBFSGroupObject"
                        container="true"
                        description="{}"
                        type="Group">
                    </object>""".format(description)

        data = {
            'IBIRS_action': 'put',
            'IBIRS_object': object,
            'IBIRS_replace': replace_group_properties
        }

        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/GROUPS/{}'.format(
                                                             self.protocol,
                                                             self.host,
                                                             self.port,
                                                             group_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_delete_group(self, group_name=None):
        """WebFOCUS Security Administration: Deleting a Group."""

        method = 'delete'
        data = {'IBIRS_action': 'delete'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/GROUPS/{}'.format(
                                                             self.protocol,
                                                             self.host,
                                                             self.port,
                                                             group_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_add_user_to_group(self, user_name=None, group_name=None):
        """WebFOCUS Security Administration: Adding a User to a Group."""

        method = 'post'
        data = {
            'IBIRS_action': 'addUserToGroup',
            'IBIRS_groupPath': 'SSYS/GROUPS/{}'.format(group_name)
        }

        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/USERS/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            user_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_remove_user_from_group(self, user_name=None, group_name=None):
        """WebFOCUS Security Administration: Removing a User From a Group."""

        method = 'post'
        data = {
            'IBIRS_action': 'removeUserFromGroup',
            'IBIRS_groupPath': 'SSYS/GROUPS/{}'.format(group_name)
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/USERS/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            user_name)

        # add the CSRF token value to the body (data) fof the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_list_rules_for_subject(self, type='group', groupuser=''):
        """WebFOCUS Security Administration: Listing Rules for a Subject."""

        method = 'post'
        data = {'IBIRS_action': 'listRulesForSubject'}
        types = {'group': 'GROUPS', 'user': 'USERS'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/SSYS/{}/{}'.format(self.protocol,
                                                              self.host,
                                                              self.port,
                                                              types[type],
                                                              groupuser)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_list_rules_for_resource(self, resource=''):
        """WebFOCUS Security Administration: Listing Rules for a Resource"""

        method = 'post'
        data = {'IBIRS_action': 'listRulesForResource'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/{}'.format(self.protocol,
                                                      self.host,
                                                      self.port,
                                                      resource)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_list_rules_for_role(self, role=''):
        """WebFOCUS Security Administration: Listing Rules for a Role."""

        method = 'post'
        data = {'IBIRS_action': 'listRulesForRole'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/{}'.format(self.protocol,
                                                      self.host,
                                                      self.port,
                                                      role)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def sa_expand_policy_string(self, policy_string=''):
        """WebFOCUS Security Administration: Expanding a Policy String.

        Expand Base64-encoded policy string representing the Effective Policy.
        """

        method = 'post'
        data = {'IBIRS_action': 'expandPolicy',
                'IBIRS_base64Policy': policy_string}
        url = '{}://{}:{}/ibi_apps/rs/utils'.format(self.protocol,
                                                    self.host,
                                                    self.port)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def save_ibi_csrf_token(self, xml):
        """Save IBI_CSRF_Token_Value from response to sign-on request."""

        tree = ET.fromstring(xml)
        token = tree.find('properties/entry[@key="IBI_CSRF_Token_Value"]')

        token_value = token.attrib['value']
        self.IBIWF_SES_AUTH_TOKEN = token_value

    def mr_sign_on(self,
                   protocol='http',
                   host='localhost',
                   port='8080',
                   userid='admin',
                   password='admin'):
        """WebFOCUS Repository: Authenticating WebFOCUS Sign-On Requests."""

        self.protocol = protocol
        self.host = host
        self.port = port

        method = 'post'
        data = {
            'IBIRS_action': 'signOn',
            'IBIRS_userName': userid,
            'IBIRS_password': password,
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)

        response = self.request(method=method, url=url, data=data)
        self.save_ibi_csrf_token(response.content)
        return response

    def mr_signoff(self):
        """WebFOCUS Repository: Signing-Off From WebFOCUS."""

        method = 'post'
        data = {'IBIRS_action': 'signOff'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)

        return self.request(method=method, url=url, data=data)

    def mr_run_report(self, foldername='', reportname='', report_parms=''):
        """WebFOCUS Repository: Running a Report From the WebFOCUS Repository

        Output format for reports run with mr_run_report should be
        html or xml.  For Excel or PDF output use
        mr_run_report_no_redirect.

        Optional report_parms are entered as parm_name=parm_value.
        Multiple parameters are separated by &.

        Example
        -------
        COUNTRY=ENGLAND&CAR=JAGUAR

        This function in in development.  IBIRS_clientPath and
        IBIRS_htmlPath needs fixing for correct values. Add support for
        report parameters, too.
        """

        method = 'post'
        data = {'IBIRS_action': 'run'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                self.protocol,
                                                                self.host,
                                                                self.port,
                                                                foldername,
                                                                reportname)
        # Parse report parameters
        if report_parms:
            report_parms_dict = dict([item.split('=') for item
                                      in report_parms.split('&')])

        data.update(report_parms_dict)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_run_report_no_redirect(self, foldername='', reportname='',
                                  report_parms=''):
        """WebFOCUS Repository: Running a Report From the WebFOCUS Repository
        (no redirection)

        Output format for reports run with mr_run_report_no_redirect
        should be Excel or PDF.  For html or xml output use
        mr_run_report.

        Optional report_parms are entered as parm_name=parm_value.
        Multiple parameters are separated by &.

        Example
        -------
        COUNTRY=ENGLAND&CAR=JAGUAR

        This function in in development.  IBIRS_clientPath and
        IBIRS_htmlPath needs fixing for correct values. Add support for
        report parameters, too.
        """

        method = 'post'
        data = {'IBIRS_action': 'run'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                self.protocol,
                                                                self.host,
                                                                self.port,
                                                                foldername,
                                                                reportname)
        # Parse report parameters
        if report_parms:
            report_parms_dict = dict([item.split('=') for item
                                      in report_parms.split('&')])

        data.update(report_parms_dict)

        # Object (Optional)
        # Is the XML object that is used to turn off redirection when
        # retrieving report output for MIME types like EXCEL and PDF
        # using the following format:
        object = """<rootObject _jt="HashMap">
                      <entry>
                        <key _jt="string" value="IBFS_contextVars"/>
                        <value _jt="HashMap">
                          <entry>
                            <key _jt="string" value="IBIWF_redirect"/>
                            <value _jt="string" value="NEVER"/>
                          </entry>
                        </value>
                        </entry>
                    </rootObject>"""

        # Not clear which key should receive object
        data['IBIRS_args'] = object
        data['IBIRS_object'] = object

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_list_report_parameters(self, foldername='', fexname=''):
        """WebFOCUS Repository: Listing the Parameters for a Repository Report.
        """

        method = 'get'
        params = {'IBIRS_action': 'describeFex'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                self.protocol,
                                                                self.host,
                                                                self.port,
                                                                foldername,
                                                                fexname)

        return self.request(method=method, url=url, params=params)

    def mr_move_item(self, foldername_source='', itemname_source='',
                     foldername_destination='', itemname_destination='',
                     replace='true'):
        """WebFOCUS Repository: Moving an Item."""

        method = 'post'
        data = {
            'IBIRS_action': 'move',
            'IBIRS_destination': '/WFC/Repository/{}/{}'.format(
                                 foldername_destination,
                                 itemname_destination),
            'IBIRS_replace': replace
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            foldername_source,
                                                            itemname_source)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_copy_item(self, foldername_source='', itemname_source='',
                     foldername_destination='', replace='true'):
        """WebFOCUS Repository: Copying an Item."""

        method = 'post'
        data = {
            'IBIRS_action': 'copy',
            'IBIRS_destination': '/WFC/Repository/{}/{}'.format(
                                 foldername_source, foldername_destination),
            'IBIRS_replace': replace
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                            self.protocol,
                                                            self.host,
                                                            self.port,
                                                            foldername_source,
                                                            itemname_source)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_create_or_update_folder(self, folder_name='',
                                   folder_description='', summary='',
                                   # applist = '', # not working correctly
                                   private='false', replace='false'):
        """WebFOCUS Repository: Creating and Updating a Folder.

        This function is in development.  IBIRS_action=get to be
        supported. Consider splitting into two functions, one for get
        and one for put.
        """

        method = 'post'
        # applist = '' # removed applist from function parameters

        # object = """<object _jt="IBFSMRObject" container="true"
        #                description="{}"
        #                summary="{}"
        #                appName="{}">
        #                <properties size="2">
        #                    <entry key="autogenmyreports"/>
        #                    <entry key="hidden"/>
        #                </properties>
        #            </object>""".format(folder_description, summary, applist)

        object = """<object _jt="IBFSMRObject"
                      container="true"
                      description="{}"
                      summary="{}"                      >
                    </object>""".format(folder_description, summary)

        data = {
            'IBIRS_action': 'put',
            'IBIRS_object': object,
            'IBIRS_private': private,
            'IBIRS_replace': replace
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}'.format(
                                                              self.protocol,
                                                              self.host,
                                                              self.port,
                                                              folder_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_list_folders_and_subfolders(self, folder_name=''):
        """WebFOCUS Repository: List Folders and Subfolders.

        List folders one levels below the parent folder.
        """

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}'.format(
                                                              self.protocol,
                                                              self.host,
                                                              self.port,
                                                              folder_name)

        return self.request(method=method, url=url, params=params)

    def mr_publish_item(self, folder_name='', item_name=''):
        """WebFOCUS Repository: Publishing an Item.

        Publish a folder or an item within a folder.
        Note: an item cannot be published if the parent folder is
        unpublished.
        """

        method = 'post'
        data = {'IBIRS_action': 'publish'}
        folder_and_item = '{}/{}'.format(
                                         folder_name,
                                         item_name
                                        ) if item_name else folder_name

        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}'.format(
                                                              self.protocol,
                                                              self.host,
                                                              self.port,
                                                              folder_and_item)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_unpublish_item(self, folder_name='', item_name='',
                          userid='admin', clear_shares='false'):
        """WebFOCUS Repository: Unpublishing an Item.

        Unpublish a folder or an item within a folder.
        """

        method = 'post'

        # user_name
        # ---------
        # If the item is private, then the full path to the owner of the item.
        # For example, /SSYS/USERS/admin.
        #
        # clear_shares
        # ------------
        # If the item is private, specify one of the following:
        # true. Unshares the item.
        # false. Does not unshare the item.

        data = {
            'IBIRS_action': 'unpublish',
            'IBIRS_ownerPath': '/SSYS/USERS/{}'.format(userid),
            'IBIRS_clearShares': clear_shares
        }
        folder_and_item = '{}/{}'.format(
                                         folder_name,
                                         item_name
                                        ) if item_name else folder_name

        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}'.format(
                                                              self.protocol,
                                                              self.host,
                                                              self.port,
                                                              folder_and_item)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_rename_item(self, folder_name='', item_name='', renamed_item=''):
        """WebFOCUS Repository: Renaming an Item."""

        method = 'post'
        data = {
            'IBIRS_action': 'rename',
            'IBIRS_newName': renamed_item
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                              self.protocol,
                                                              self.host,
                                                              self.port,
                                                              folder_name,
                                                              item_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_upload_report(self, folder_name='', fex_name='', report_title='',
                         local_file_path=''):
        """WebFOCUS Repository: Uploading a WebFOCUS Report.

        This function is in development. Response indicates success
        but uploaded file appears empty.
        """

        method = 'post'

        with open(local_file_path, 'rt') as f:
            content = f.read()
        content_base64 = base64.b64encode(content)
        content_string = content_base64.decode("utf-8")

        object = """<rootObject _jt="IBFSMRObject"
                      description="{}"
                      type="FexFile">
                      <content _jt="IBFSByteContent"
                        char_set="Cp1252">{}</content>
                    </rootObject>""".format(report_title, content_string)

        data = {
            'IBIRS_action': 'put',
            'IBIRS_object': object,
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 fex_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def mr_get_report_or_url_content_decoded(self, folder_name='',
                                             content_name=''):
        """WebFOCUS Repository: Retrieving Content for a WebFOCUS Report and URL.

        Return content as plain text and not base64 encoded.
        """

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 content_name)

        retval = self.request(method=method, url=url, params=params)

        tree = ET.fromstring(retval.content)
        content_item = tree.find('rootObject/content')
        content_base64_encoded = content_item.text
        content_base64_decoded = base64.b64decode(content_base64_encoded)
        content_string = content_base64_decoded.decode('utf-8')

        # pseudo object for handling requests that require post processing
        pseudo_retval = ExRetval()
        pseudo_retval.text = content_string
        pseudo_retval.content = content_string
        return pseudo_retval

    def mr_get_report_or_url_content_raw(self, folder_name='',
                                         content_name=''):
        """WebFOCUS Repository: Retrieving Content for a WebFOCUS Report and URL.

        Return content base64 encoded
        """

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 content_name)

        return self.request(method=method, url=url, params=params)

    def rs_run_report(self, nodename='EDASERVE', appname='', fexname='',
                      report_parms=''):
        """Reporting Server: Running a Report Within an Application.

        Optional report_parms are entered as parm_name=parm_value.
        Multiple parameters are separated by &.

        Example
        -------
        COUNTRY=ENGLAND&CAR=JAGUAR

        This function in in development.  IBIRS_clientPath and
        IBIRS_htmlPath needs fixing for correct values. Add support for
        report parameters, too.

        This function will be split into versions with no redirection
        and redirection.
        """

        method = 'post'
        data = {'IBIRS_action': 'run'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA/{}/{}/{}'.format(
                                                         self.protocol,
                                                         self.host,
                                                         self.port,
                                                         nodename,
                                                         appname,
                                                         fexname)
        # Parse report parameters
        if report_parms:
            report_parms_dict = dict([item.split('=') for item
                                      in report_parms.split('&')])
            data.update(report_parms_dict)

        # Object (Optional)
        # Is the XML object that is used to turn off redirection when
        # retrieving report output for MIME types like EXCEL and PDF
        # using the following format:
        object = """<rootObject _jt="HashMap">
                      <entry>
                        <key _jt="string" value="IBFS_contextVars"/>
                        <value _jt="HashMap">
                          <entry>
                            <key _jt="string" value="IBIWF_redirect"/>
                            <value _jt="string" value="NEVER"/>
                          </entry>
                        </value>
                        </entry>
                    </rootObject>"""

        # Not clear which key should receive object
        data['IBIRS_args'] = object
        data['IBIRS_object'] = object

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def rs_run_ad_hoc_fex(self, nodename='EDASERVE', fex_content=''):
        """Reporting Server: Running a Report Within an Application."""

        method = 'post'
        data = {
            'IBIRS_action': 'runAdHocFex',
            'IBIRS_path': 'EDA',
            'IBIRS_nodeName': nodename,
            'IBIRS_fexContent': fex_content
        }
        
        # added redirect section in v16, 2019-04-05
        # Object (Optional)
        # Is the XML object that is used to turn off redirection when
        # retrieving report output for MIME types like EXCEL and PDF
        # using the following format:
        object = """<rootObject _jt="HashMap">
                      <entry>
                        <key _jt="string" value="IBFS_contextVars"/>
                        <value _jt="HashMap">
                          <entry>
                            <key _jt="string" value="IBIWF_redirect"/>
                            <value _jt="string" value="NEVER"/>
                          </entry>
                        </value>
                        </entry>
                    </rootObject>"""

        # Not clear which key should receive object
        data['IBIRS_args'] = object
        data['IBIRS_object'] = object

        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA'.format(self.protocol,
                                                       self.host,
                                                       self.port)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def rs_list_nodes(self):
        """Reporting Server: Listing WebFOCUS Reporting Server Nodes."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA'.format(self.protocol,
                                                       self.host,
                                                       self.port)

        return self.request(method=method, url=url, params=params)

    def rs_create_application(self, node_name='EDASERVE', app_name=''):
        """Reporting Server: Creating an Application."""

        method = 'post'
        object = """<object _jt="IBFSFolder"
                      container="true"
                      type="IBFSFolder">
                    </object>"""
        data = {'IBIRS_action': 'put', 'IBIRS_object': object}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA/{}/{}'.format(self.protocol,
                                                             self.host,
                                                             self.port,
                                                             node_name,
                                                             app_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def rs_list_applications(self, node_name='EDASERVE'):
        """Reporting Server: Listing Applications."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA/{}'.format(self.protocol,
                                                          self.host,
                                                          self.port,
                                                          node_name)

        return self.request(method=method, url=url, params=params)

    def rs_list_application_files(self, node_name='EDASERVE', app_name=''):
        """Reporting Server: Listing Files Within an Application."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/EDA/{}/{}'.format(self.protocol,
                                                             self.host,
                                                             self.port,
                                                             node_name,
                                                             app_name)

        return self.request(method=method, url=url, params=params)

    def rc_create_schedule(self, folder_name='', schedule_name='',
                           schedule_object=''):
        """ReportCaster: Creating and Updating a Schedule.

        Do not use.  Function in development. New approach: get, modify,
        and save-as existing schedule.
        """

        method = 'post'
        data = {
            'IBIRS_action': 'put',
            'IBIRS_replace': False,
            'IBIRS_object': schedule_object
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 schedule_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)

    def rc_get_schedule(self, folder_name='', schedule_name=''):
        """ReportCaster: Retrieving a Schedule."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 schedule_name)

        return self.request(method=method, url=url, params=params)

    def rc_run_schedule(self, folder_name='', schedule_name=''):
        """ReportCaster: Run Schedule."""

        method = 'post'
        data = {'IBIRS_action': 'run'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 schedule_name)

        # add the CSRF token value to the body (data) of the request
        if self.IBIWF_SES_AUTH_TOKEN is not None:
            data['IBIWF_SES_AUTH_TOKEN'] = self.IBIWF_SES_AUTH_TOKEN

        return self.request(method=method, url=url, data=data)


    def rc_get_library_access_list(self, folder_name='', list_name=''):
        """ReportCaster: Retrieving a Library Access List."""

        method = 'get'
        params = {'IBIRS_action': 'get'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs/WFC/Repository/{}/{}'.format(
                                                                 self.protocol,
                                                                 self.host,
                                                                 self.port,
                                                                 folder_name,
                                                                 list_name)

        return self.request(method=method, url=url, params=params)
    
    
    def ex_sa_list_users_to_csv_file(self, csv_filename=r'C:\ibi\apps\wf_restful_lab\users.csv'):
        '''Write list of users to a csv file'''

        records = []

        retval = self.sa_list_users()
        tree = ET.fromstring(retval.content)

        for user in tree.iterfind(".//item[@_jt='IBFSUserObject']"):
            attributes = user.attrib
            attributes['status'] = user.find('status').get('name')
            # rename field (user) 'name' to 'user_name'
            attributes['user_name'] = attributes.pop('name')
            records.append(attributes)

        records = self.sort_records(records, 'user_name')

        fieldnames = ('user_name', 'description', 'email', 'fullPath',
                      'status', 'handle', 'index', 'length',
                      'parent', 'policy', 'rsPath', 'type',
                      'dummy', '_jt')
        
        self.write_records_to_csv(csv_filename, fieldnames, records) 

        retval = ExRetval()
        retval.text = self.tabular_print_to_string(records, fieldnames)
        return retval
     
        
    def ex_sa_add_or_update_users_from_csv_file(self, csv_filename=r'C:\ibi\apps\wf_restful_lab\users.csv'):
        '''Add or update users read from a csv file.
        
           The column titles "user_name", "description", "email", and "status" must exist
           and must be in lowercase.  "password" is optional.  All other columns will
           be ignored.
        '''

        stream_in  = open(csv_filename, 'rt', newline='')

        # all fields must be quoted
        reader = csv.DictReader(stream_in, dialect='excel',
                                quoting=csv.QUOTE_ALL, 
                                skipinitialspace=True)  

        # create a pseudo-response object to store each call's response
        response_values = ExRetval()

        # user_name is the same as userid in the REST service's documentation.
        # user_name is a more meaningful label than userid
        for row in reader:            
            retval = self.sa_add_or_update_user(user_name = row['user_name'],
                                                replace_userid_properties = 'false',
                                                userid_title = row['description'], 
                                                email_address = row['email'],
                                                status = row['status'],
                                                password =  row['password'] if 'password' in row else ''
                                               )
            
            response_values.content += self.pretty_print_xml(retval.content)
            response_values.text    += self.pretty_print_xml(retval.text)
            
        return response_values
    

    def ex_sa_delete_users_read_from_csv_file(self, csv_filename=r'C:\ibi\apps\wf_restful_lab\users.csv'):
        '''Add or update users read from a csv file.
        
           The column title "user_name" must exist and must be in lowercase.
           All other columns will be ignored.
        '''

        stream_in  = open(csv_filename, 'rt', newline='')

        # all fields must be quoted
        reader = csv.DictReader(stream_in, dialect='excel', 
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)  

        # create a pseudo-response object to store each call's response
        response_values = ExRetval()

        for row in reader:            
            retval = self.sa_delete_user(user_name=row['user_name'])
                                               
            response_values.content += self.pretty_print_xml(retval.content)
            response_values.text    += self.pretty_print_xml(retval.text)
            
        return response_values
    
	
    def ex_sa_add_or_update_groups_from_csv_file(self, replace_group_properties='false',
                                                 csv_filename=r'C:\ibi\apps\wf_restful_lab\groups.csv'):
        
        '''Add or update groups read from a csv file.
        
           The column titles "group_name" and "description" must exist and must be in lowercase.
           All other columns will be ignored.
        '''

        stream_in = open(csv_filename, 'rt', newline='')

        # all fields must be quoted
        reader = csv.DictReader(stream_in, dialect='excel', 
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)  

        # create a pseudo-response object to store each call's response
        response_values = ExRetval()

        for row in reader:
            retval = self.sa_add_or_update_group(group_name=row['group_name'],
                                                 description=row['description'],
                                                 replace_group_properties=replace_group_properties)
            
            response_values.content += self.pretty_print_xml(retval.content)
            response_values.text    += self.pretty_print_xml(retval.text)
            
        return response_values

		
    def ex_sa_add_users_to_groups_from_csv_file(self, csv_filename=r'C:\ibi\apps\wf_restful_lab\users_to_groups.csv'):
        '''Add users to groups read from a csv file.
        
           The column titles "user_name" and "group_name" must exist and must be in lowercase.
           All other columns will be ignored.

           Before using this function users and groups must have already been created.
        '''

        stream_in = open(csv_filename, 'rt',  newline='')

        # all fields must be quoted
        reader = csv.DictReader(stream_in, dialect='excel',
                                quoting=csv.QUOTE_ALL, skipinitialspace=True)  

        # create a pseudo-response object to store each call's response
        response_values = ExRetval()

        for row in reader:            
            retval = self.sa_add_user_to_group(user_name = row['user_name'],
                                               group_name = row['group_name'])
            
            response_values.content += self.pretty_print_xml(retval.content)
            response_values.text    += self.pretty_print_xml(retval.text)
            
        return response_values
    

    def ex_sa_list_all_groups(self, group_name='/'):
        '''Listing Groups. List groups in all levels below the parent group.'''

        records = []
        
        def get_nested_groups(group_name=group_name):
            retval = self.sa_list_groups(group_name=group_name)
            tree = ET.fromstring(retval.content)
    
            for group in tree.iter('item'):
                attributes = group.attrib
                attributes['fullName'] = attributes['fullPath'].replace('IBFS:/SSYS/GROUPS/', '')
                # add a copy of 'fullName' titled 'group_name' for compatibility with other functions
                # requiring a group_name
                attributes['group_name'] = attributes['fullName']
                records.append(attributes)
                get_nested_groups(group_name=attributes['fullName'])


        get_nested_groups(group_name=group_name)
        records = self.sort_records(records, 'fullName')

        fieldnames = ['group_name', 'fullName', 'name', 'description', 'rsPath',
                      'fullPath', 'dummy', 'container', 'handle', 'parent',
                      'index', 'length', 'policy','typeDescription', 'type', '_jt']
        
        retval = ExRetval()
        retval.content = self.tabular_print_to_string(records, fieldnames)
        retval.text = self.tabular_print_to_string(records, fieldnames)
        return retval


    def ex_sa_list_all_groups_to_csv_file(self, group_name='/',
                                          csv_filename=r'C:\ibi\apps\wf_restful_lab\groups.csv'):
        '''Listing Groups. List groups in all levels including and below the parent group.
           Write results to csv file.close
        '''

        records = []
        
        def get_nested_groups(group_name=group_name):
            retval = self.sa_list_groups(group_name=group_name)
            tree = ET.fromstring(retval.content)
    
            for group in tree.iter('item'):
                attributes = group.attrib
                attributes['fullName'] = attributes['fullPath'].replace('IBFS:/SSYS/GROUPS/', '')
                # add a copy of 'fullName' titled 'group_name' for compatibility with other functions
                # requiring a group_name
                attributes['group_name'] = attributes['fullName']
                records.append(attributes)
                get_nested_groups(group_name=attributes['fullName'])


        get_nested_groups(group_name=group_name)
        records = self.sort_records(records, 'fullName')

        fieldnames = ['group_name', 'fullName', 'name', 'description', 'rsPath',
                      'fullPath', 'dummy', 'container', 'handle', 'parent',
                      'index', 'length', 'policy','typeDescription', 'type', '_jt']
        
        self.write_records_to_csv(csv_filename, fieldnames, records) 
        retval = ExRetval()
        retval.text = self.tabular_print_to_string(records, fieldnames)
        return retval


    

    
    def ex_sa_list_groups_with_users(self, group_name= '/', sort_by='group'):
        '''List groups, with users, in all levels below the parent group.
           Default sorting is by group. sort_by values are 'user' or 'group'.
        '''

        records = []
        
        def get_nested_groups(group_name=group_name):
            retval_groups = self.sa_list_groups(group_name=group_name)
            tree_groups = ET.fromstring(retval_groups.content)
    
            for group in tree_groups.iter('item'):
                group_full_name = group.attrib['fullPath'].replace('IBFS:/SSYS/GROUPS/', '')
                # skip the group EVERYONE
                if group_full_name == 'EVERYONE': continue
                
                # get users in group
                retval_users = self.sa_list_users_in_group(group_name = group_full_name)
                tree_users = ET.fromstring(retval_users.content)
                for user in tree_users.iter('item'):
                    user_name = user.attrib['name']
                    records.append({'group_name': group_full_name, 'user_name': user_name})
                    
                get_nested_groups(group_name=group_full_name)


        get_nested_groups(group_name=group_name)

        if sort_by.lower() == 'user':
            records = self.sort_records(records, 'user_name', 'group_name')
        elif sort_by.lower() == 'group':
            # sort by group, by user within group
            records = self.sort_records(records, 'group_name', 'user_name')
        else:
            # future development: raise an exception
            pass
        
        fieldnames = ['group_name', 'user_name' ]        
        retval = ExRetval()
        retval.text = self.tabular_print_to_string(records, fieldnames)
        return retval

    
    def ex_sa_list_groups_with_users_to_csv_file(self, group_name= '/', sort_by='group',
                                                 csv_filename=r'C:\ibi\apps\wf_restful_lab\groups_with_users.csv'):
        
        '''List groups, with users, in all levels including and below the parent group.
           Default sorting is by group. sort_by values are 'user' or 'group'.
        '''

        records = []
        
        def get_nested_groups(group_name=group_name):
            retval_groups = self.sa_list_groups(group_name=group_name)
            tree_groups = ET.fromstring(retval_groups.content)
    
            for group in tree_groups.iter('item'):
                group_full_name = group.attrib['fullPath'].replace('IBFS:/SSYS/GROUPS/', '')
                # skip the group EVERYONE
                if group_full_name == 'EVERYONE': continue
                
                # get users in group
                retval_users = self.sa_list_users_in_group(group_name = group_full_name)
                tree_users = ET.fromstring(retval_users.content)
                for user in tree_users.iter('item'):
                    user_name = user.attrib['name']
                    records.append({'group_name': group_full_name, 'user_name': user_name})
                    
                get_nested_groups(group_name=group_full_name)


        get_nested_groups(group_name=group_name)

        if sort_by.lower() == 'user':
            records = self.sort_records(records, 'user_name', 'group_name')
        elif sort_by.lower() == 'group':
            # sort by group, by user within group
            records = self.sort_records(records, 'group_name', 'user_name')
        else:
            # future development: raise an exception
            pass
        
        fieldnames = ['group_name', 'user_name' ]
        self.write_records_to_csv(csv_filename, fieldnames, records) 
        retval = ExRetval()
        
        # debugging
        print(fieldnames)
        for record in records:
            print(record)
        
        retval.text = self.tabular_print_to_string(records, fieldnames)
        return retval


    def ex_mr_list_folders_and_subfolders(self, folder_name=''):
        '''Extended List Folders and Subfolders. List folders in all levels below the
           parent folder.
           Code can be simplified. See ex_sa_list_all_groups() for example.
        '''

        folder_list = []

        def get_folders(folder_name = ''):
            method = 'get'
            params = {'IBIRS_action' : 'get'}
            
            url = '%s://%s:%s/ibi_apps/rs/ibfs/WFC/Repository/%s' % (self.protocol,
                                                                     self.host,
                                                                     self.port,
                                                                     folder_name)
           
            f = self.request(method = method, url = url, params = params)

            folder_names = []            
            tree = ET.fromstring(f.content)
            
            # can a list comprehension replace these lines?
            # should the folder name include the path to eliminate ambiguity?
            for folder in tree.findall(".//item[@_jt='IBFSMRObject']"):
                name = folder.attrib.get('name')
                if name: folder_names.append(name)
            
            return folder_names


        def count_subfolders(folder_name=''):
            '''Return count of folder's subfolders one level down only.'''
            return len(get_folders(folder_name = folder_name))

    
        def compare(x, y):
            if x.lower() == y.lower(): return 0
            if x.lower()  < y.lower(): return -1
            if x.lower()  > y.lower(): return 1
    

        def walk_folder_tree(folder_name, folder_list):
            folder_list.append(folder_name)
        
            for folder in get_folders(folder_name):
                path = folder_name + '/' + folder 
            
                if not count_subfolders(folder_name = path):  
                    folder_list.append(path)
                else:
                    walk_folder_tree(path, folder_list)
             
            return folder_list

        # see https://docs.python.org/3.6/library/
        #        functools.html#functools.cmp_to_key
        folder_list.sort(key=functools.cmp_to_key(compare))  
        completed_folder_list = walk_folder_tree(folder_name, folder_list)

        completed_folder_list_as_text = ('\n').join(completed_folder_list)
        retval = ExRetval()
        retval.text = completed_folder_list_as_text
        retval.content = completed_folder_list_as_text
        return retval



#  --[ main ]------------------------------------------------------------------
if __name__ == '__main__':

    session = Session()
    r = session.mr_sign_on(protocol='http',
                           host='localhost',
                           port='8080',
                           userid='admin',
                           password='admin')
    
    
