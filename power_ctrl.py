#!/usr/bin/env python3
from http import cookies
from bs4 import BeautifulSoup
import http.client
import sys
import urllib.parse

class sp8h:
    """
    A Python class to access Smart Power 8H power switch.
    This mimics web access because we don't know how to use API interface.
    For now, this library only supports turn on/off directly via http interface.
    """

    POWER_OFF = 2
    POWER_ON = 1
    POWER_RST = 3

    LOGIN_STS_OK = b'0'
    LOGIN_STS_FAIL = b'1'
    LOGIN_STS_FULL = b'2'

    LOGIN_URL = "/login_auth.csp"
    LOGOUT_URL = "/logout.csp"
    POWER_CTL_URL = "/power_monitor_frame.csp"
    POWER_STS_URL = POWER_CTL_URL

    def __init__(self):
        self.port = 80
        self.target_url = ""
        self.http_header = {}
        self.http_params = {}
        self.cookie_db = cookies.SimpleCookie()
        self.user = ""
        self.passwd = ""
        self.is_connected = False
        self.is_login = False

    def eprint(self, *args, **kwargs):
        """
        Print error message to stderr.
        """
        print(*args, file=sys.stderr, **kwargs)

    def connect(self):
        """
        Connect to target SP8H.
        """

        #TODO: check parameters if valid.
        self.conn = http.client.HTTPConnection(self.target_url, self.port)
        self.is_connected = True

    def disconnect(self):
        """
        Disconnect from target SP8H.
        """
        if self.is_connected:
            self.conn.close()
            self.is_connected = False

    def store_cookies(self, cookie_str=""):
        """
        Parse cookie raw string and store them.
        """
        if cookie_str is not None:
            self.cookie_db.load(cookie_str)

    def login(self):
        """
        Log in SP8H, needs to configure parameters and connect to server via connect() first.
        """
        # TODO: Check parameters if valid

        # If logged in, restart a new session.
        if self.is_login:
            self.disconnect()
            self.connect()

        if not self.is_connected:
            self.connect()

        if not self.is_connected:
            sys.exit('Connection failed!')

        self.http_params = urllib.parse.urlencode({'auth_user': self.user, 'auth_passwd': self.passwd})
        self.http_header = {"Content-type": "application/x-www-form-urlencoded"}

        try:
            self.conn.request("POST", self.LOGIN_URL, self.http_params, self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

        data = response.read()

        if data == self.LOGIN_STS_FAIL:
            sys.exit("Failed to login.")
        elif data == self.LOGIN_STS_FULL:
            sys.exit("Failed to login, too much login users")

        self.store_cookies(response.getheader("Set-Cookie"))

        #DBG: print cookie
        #print(self.cookie_db)
        self.is_login = True

    def logout(self):
        """
        logout SP8H
        """
        if not self.is_login:
            self.eprint("Login first!")
            return False

        self.http_header = {"Cookie": self.cookie_db.output(header="", sep=";")}

        url = '{url}'.format(url=self.LOGOUT_URL)

        self.http_params = ""

        try:
            self.conn.request("GET", url, self.http_params, self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

        self.is_login = False

    def switch(self, machin_id=0, power_id=0, action=1):
        """
        Turn On/Off the power port.
        """

        if not self.is_login:
            sys.exit("Login first!")

        if action != self.POWER_ON and action != self.POWER_OFF and action != self.POWER_RST:
            sys.exit("Invalid action detected!")

        self.http_header = {"Cookie": self.cookie_db.output(header="", sep=";")}

        #DBG: print http header
        #print(self.http_header)

        self.http_params = urllib.parse.urlencode({'srm_no': machin_id, 'power_id': power_id, 'status': action})
        #DBG: print http params
        #print(self.http_params)

        url = '{url}?{params}'.format(url=self.POWER_CTL_URL, params=self.http_params)

        try:
            self.conn.request("GET", url, self.http_params, self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

    def get_status(self, machin_id=0):
        """
        Get the status of power port.
        """

        if not self.is_login:
            sys.exit("Login first!")

        self.http_header = {"Cookie": self.cookie_db.output(header="", sep=";")}

        #DBG: print http header
        #print(self.http_header)

        self.http_params = urllib.parse.urlencode({'srm_no': machin_id})
        #DBG: print http params
        #print(self.http_params)

        url = '{url}?{params}'.format(url=self.POWER_STS_URL, params=self.http_params)

        try:
            self.conn.request("GET", url, self.http_params, self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

        html_data = response.read().decode("utf-8")

        #For Debug
        #print(html_data)

        merge_list = []
        if len(html_data) > 0 and html_data != "TimeOut":
            try:
                #Parse power status.
                status_list = html_data.split("],[")[1][1:-1].split("','")
                #print(status_list)

                #Parse power ampere.
                ampere_list = html_data.split("],[")[2][1:-3].split("','")
                #print(ampere_list)

                merge_list = [list(a) for a in zip(status_list, ampere_list)]
                #print(merge_list)
            except (ValueError, IndexError) as e:
                sys.exit('Error:' + str(e))

        return merge_list

class aw2401:
    """
    A python class to access cloud power AW-2401.
    This mimics web access because we don't know how to use API interface.
    For now, this library only supports turn on/off directly via http interface.

    """

    POWER_OFF = 0
    POWER_ON = 1

    POWER_CTL_URL = "/set_port_mode.html"
    POWER_STS_URL = "/get_port_mode.html"

    def __init__(self):
        self.port = 80
        self.target_url = ""
        self.http_header = {}
        self.http_params = {}
        self.pwr1_sel = False
        self.pwr2_sel = False
        self.pwr3_sel = False
        self.pwr4_sel = False
        self.is_connected = False

    def eprint(self, *args, **kwargs):
        """
        Print error message to stderr.
        """
        print(*args, file=sys.stderr, **kwargs)

    def connect(self):
        """
        Connect to target AW-2401.
        """

        #TODO: check parameters if valid.
        self.conn = http.client.HTTPConnection(self.target_url, self.port)
        self.is_connected = True

    def disconnect(self):
        """
        Disconnect from target AW-2401.
        """
        if self.is_connected:
            self.conn.close()
            self.is_connected = False

    def switch(self, pwr_list, action=1):
        """
        Turn On/Off the power port.
        """

        if action != self.POWER_ON and action != self.POWER_OFF:
            sys.exit("Invalid action detected!")

        self.http_header = {"Content-type": "application/x-www-form-urlencoded"}

        #DBG: print http header
        #print(self.http_header)

        for pwr in pwr_list:
            if pwr == 1:
                self.pwr1_sel = True
            if pwr == 2:
                self.pwr2_sel = True
            if pwr == 3:
                self.pwr3_sel = True
            if pwr == 4:
                self.pwr4_sel = True

        self.http_params = urllib.parse.urlencode({'portMode1': 'jj' if not self.pwr1_sel else 'on' if action == 1 else 'off', \
                                                   'portMode2': 'jj' if not self.pwr2_sel else 'on' if action == 1 else 'off', \
                                                   'portMode3': 'jj' if not self.pwr3_sel else 'on' if action == 1 else 'off', \
                                                   'portMode4': 'jj' if not self.pwr4_sel else 'on' if action == 1 else 'off'})

        #DBG: print http params
        #print(self.http_params)

        url = '{url}?{params}'.format(url=self.POWER_CTL_URL, params=self.http_params)

        #DBG: print http url
        #print(url)

        try:
            self.conn.request("GET", url, self.http_params, self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

    def get_status(self):
        """
        Get the status of power port.
        """

        self.http_header = {"Content-type": "application/x-www-form-urlencoded"}

        url = self.POWER_STS_URL

        try:
            self.conn.request("GET", url, "", self.http_header)
            response = self.conn.getresponse()
        except (OSError, ConnectionResetError) as e:
            sys.exit('Error:' + str(e))

        if response.status != http.client.OK:
            sys.exit("Failed to login, status={}".format(response.status))

        html_data = response.read()

        #For Debug
        #print(html_data)

        soup = BeautifulSoup(html_data, "html.parser")
        foundTags = soup.find_all('input')
        #print(foundTags)
        power_state = []
        for inpTag in foundTags:
             #print(inpTag['value'])
             power_state.append(inpTag['value'])

        return power_state
