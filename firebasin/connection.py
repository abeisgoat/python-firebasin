from ws4py.client.threadedclient import WebSocketClient
import threading
import time
import json

try:
    import ssl
except:
    ssl = False

from debug import debug

class Connection(threading.Thread):
    '''Connect to a Firebase websocket.'''

    def __init__(self, url, root):
        threading.Thread.__init__(self)

        self.parsed_url = self.parse_url(url)
        self._root = root
        self.outgoing_queue = []
        self.url = None
        self.handshake = None
        self.data = None
        self.connected = False
        self.stopped = False

    def run(self):
        '''Perform a handshake then connect to a Firebase.'''

        def set_url(d):
            self.handshake.close()
            self.url = d['d']['d']

        # An initial handshake is done which returns the actual websocket URL
        self.handshake = DataClient('wss://' + '.'.join(self.parsed_url) + '/.ws?v=5')
        self.handshake.on_received = set_url
        self.handshake.connect()

        # Just hang out until the handshake gives us the actual websocket URL
        while not self.url:
            time.sleep(0.1)

        # Once we have the url connect
        self.connect()

    def connect(self):
        '''Connect to a Firebase.'''

        # Sometimes self.url is a dictionary with extra data, definitely don't know why that is.
        if type(self.url) == type(dict()):
            debug('Dictionary URL Received')
            self.url = self.url['h']

        self.data = DataClient('wss://' + self.url + '/.ws?v=5&ns=' + self.parsed_url[0])
        self.data.on_opened = self.send_outgoing

        def on_connected():
            self.connected = True

        def on_received(o):
            self.connected = True
            self._root._process(o)

        def on_closed(data):
            self.connected = False
            self.stopped = True

        self.data.on_received = on_received
        self.data.on_closed = on_closed
        self.data.on_connected = on_connected

        self.data.connect()

        while self.data._th.is_alive() and not self.stopped:
            self.data._th.join(1)

        self.data.close()

    def send_outgoing(self):
        '''Send all queued outgoing messages to Firebase.'''

        for message in self.outgoing_queue:
            self.data.send(json.dumps(message))

    def send(self, message):
        '''Send or queue a single message to a Firebase.'''

        if not self.connected:
            self.outgoing_queue.append(message)
        else:
            self.data.send(json.dumps(message))

    def parse_url(self, url):
        '''Parse a URL.'''

        return url.split('https://')[1].split('.')

class DataClient(WebSocketClient):
    '''Connect to a web socket.'''

    def __init__(self, url):
        if ssl:
            WebSocketClient.__init__(self, url, ssl_options={'ssl_version': ssl.PROTOCOL_TLSv1})
        else:
            WebSocketClient.__init__(self, url)
        self.data = []
        self.partialdata = []
        self.partialdatanumber = 1

    def opened(self):
        '''Call callback on_opened'''

        debug('Connected to the data server :D')
        if 'on_opened' in dir(self):
            self.on_opened()

    def closed(self, code, reason):
        '''Call callback on_closed.'''

        debug(("Closed down :(", code, reason))
        if 'on_closed' in dir(self):
            self.on_closed(self.data)

    def received_message(self, m):
        '''Store received message and call on_received.'''

        if str(m).isdigit(): #Number, telling how many 16kb chunks to expect
            self.partialdatanumber = int(str(m))
            return;
        if self.partialdatanumber > 1 and len(self.partialdata) < self.partialdatanumber: #Check to see if we're expecing multiple chunks
            self.partialdata.append(str(m))
            if len(self.partialdata) == self.partialdatanumber: 
                m = str.join('', self.partialdata) 
                self.partialdatanumber = 1
                self.partialdata = []
            else:
                return
        obj = json.loads(str(m))
        self.data.append(obj)
        if 'on_received' in dir(self):
            self.on_received(obj)
