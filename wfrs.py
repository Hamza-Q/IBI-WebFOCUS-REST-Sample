"""
wfrs.py
Very simple authenticated API wrapper for requests.Session object
  for use with WebFOCUS
Modeled from Ira Kaplan at Ira_Kaplan@ibi.com
"""

import xml.etree.ElementTree as ET
import requests


class WF_Session(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.IBIWF_SES_AUTH_TOKEN = None

    def _save_ibi_csrf_token(self, xml):
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

        # Stored for sign off
        self.protocol = protocol
        self.host = host
        self.port = port

        data = {
            'IBIRS_action': 'signOn',
            'IBIRS_userName': userid,
            'IBIRS_password': password,
        }
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)

        response = self.post(url=url, data=data)
        self._save_ibi_csrf_token(response.content)

    def mr_signoff(self):
        """WebFOCUS Repository: Signing-Off From WebFOCUS."""

        data = {'IBIRS_action': 'signOff'}
        url = '{}://{}:{}/ibi_apps/rs/ibfs'.format(self.protocol,
                                                   self.host,
                                                   self.port)
        self.IBIWF_SES_AUTH_TOKEN = None
        self.post(url=url, data=data)
