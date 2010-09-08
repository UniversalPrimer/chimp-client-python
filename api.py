#!/usr/bin/env python

# This is a Python implementation of an APE client

import json
import urllib
import string
import random
import socket

class APEClient:


    def __init__(self, host, port=80):

        self.sessid = None
        self.pipeid = None
        self.host = host
        self.port = port
        self.protocol = 1 # the APE protocol
        self.chl = 1
        
        self.name = self.identifier(16)

        self.login()
        

    def identifier(self, length):

        nums = '0123456789'

        return ''.join(random.choice(string.letters + nums) for i in xrange(length))


    def connect(self):
        self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.con.connect((self.host, self.port))


    def send_cmd(self, cmd, params):

        self.connect()

        data = [{'cmd': cmd.upper(),
                 'chl': self.chl,
                 'params': params}]

        if self.sessid:
            data[0]['sessid'] = self.sessid



        self.chl += 1

        data_json = json.dumps(data, False, True, True, True, json.JSONEncoder, None, (',',':'))

        url = '/'+str(self.protocol)+'/?'

        self.con.send("POST "+url+" HTTP/1.1\r\n")
        self.con.send('Host: '+self.host+':'+str(self.port)+"\r\n")
        self.con.send("Accept-Encoding: identity\r\n")
        self.con.send("Content-type: application/x-www-form-urlencoded; charset=utf-8\r\n")
        self.con.send("Content-Length: "+str(len(data_json))+"\r\n")
        self.con.send("\r\n")

        self.con.send(data_json+"\r\n")


    def recv_raw(self):

        # TODO do some non-blocking stuff so we can safely receive more than 4 kb without blocking
        data = self.con.recv(4096)

        self.con.close()

        idx = string.find(data, "\r\n\r\n")

        if(idx < 0):
            raise Exception("could not find JSON data in server response")

        raws_json = data[idx:len(data)-1]

        raws = json.loads(raws_json)

        return raws

    def get_raw(self, raws, name):
        name = name.upper()
        for raw in raws:
            if raw['raw'] == name:
                return raw
        return None


    def login(self):

        self.send_cmd('connect', {'name': self.name})

        raws = self.recv_raw()
        raw = self.get_raw(raws, 'login')

        if not raw:
            raise Exception("No login raw returned")

        if not raw['data'] or not raw['data']['sessid']:
            raise Exception("Did not receive sessid from server")

        self.sessid = raw['data']['sessid']
    

    def join(self, channel):

        self.send_cmd('join', {'channels': channel})

        raws = self.recv_raw()
        raw = self.get_raw(raws, 'channel')

        if not raw or not raw['data'] or not raw['data']['pipe'] or not raw['data']['pipe']['pubid']:
            raise Exception("Did not receive pipe pubid from server")

        self.pipeid = raw['data']['pipe']['pubid']


    def send(self, data):
        data = urllib.quote(data)
        
        self.send_cmd('send', {
                'msg': data,
                'pipe': self.pipeid})
                  
    def recv(self):
        raws = self.recv_raw()
        raw = self.get_raw(raws, 'data')

        if not raw or not raw['data'] or not raw['data']['msg']:
            raise Exception("Problem with received data")

        data = raw['data']['msg']

        return urllib.unquote(data)
        
        
# =======================
# end code to be librarified
# ======================


# Example usage of library
#
# NOTE: A simple web-client that sends and receives on the 'foo' channel
#       is available here: http://gui.grafiki.org/

ape = APEClient('1.ape.gui.grafiki.org', 6969)

# If the channel doesn't exist, it will be automatically created
ape.join('foo')

ape.send("Wohooo!") # send a string. the string is escaped, so you can safely send JSON data

data = ape.recv() # blocks until data is received. this unescapes the string data before returning it

print data

