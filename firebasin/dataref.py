import datetime
import math
import random

from connection import *
from structure import *
from debug import *

class DataRef(object):
    '''Reference a specific location in a Firebase.'''

    def __init__(self, root, path, startPoint=None, endPoint=None, limit=None):
        self._root = root
        self.path = '/' + '/'.join([p for p in path.split('/') if p])
        self.query_start = startPoint
        self.query_end = endPoint
        self.query_limit = limit

    def on(self, event, callback, onCancel=None, context=None):
        '''Connect a callback to an event.'''

        self._root._bind(self.path, event, callback)
        self._root._subscribe(self.path, self._get_query(), callbacks={"onCancel": onCancel})

    def set(self, data, onComplete=None):
        '''Write data to this Firebase location.'''

        message = {"t":"d", "d":{"r":0, "a":"p", "b":{"p":self.path, "d":data }}}
        self._root._send(message, {'onComplete': onComplete})

    def setWithPriority(self, data, priority, onComplete=None):
        '''Write data like set, but also specify the priority for that data.'''

        data['.priority'] = priority
        self.set(data, onComplete=onComplete)

    def setPriority(self, priority, onComplete=None):
        '''Set a priority for the data at this Firebase location.'''

        self.child('.priority').set(priority)

    def child(self, path):
        '''Return a new DataRef of a child location.'''

        clean_path = '/' + '/'.join([p for p in path.split('/') if p])
        return DataRef(self._root, self.path+clean_path)

    def parent(self):
        '''Return the parent of this location.'''

        if self.path != '':
            parent_path = '/'.join(self.path.split('/')[-1:])
            return DataRef(self._root, parent_path)
        else:
            return None

    def auth(self, auth_token, onComplete=None, onCancel=None):
        '''Send an authentication token.'''

        message = {"t":"d", "d":{"r":0, "a":"auth", "b":{"cred":auth_token}}}
        self._root._send(message, {'onComplete': onComplete, 'onCancel': onCancel})

    def unauth(self):
        '''Unauthenticates a Firebase client (i.e. logs out).'''

        message = {"t":"d","d":{"r":0,"a":"unauth","b":{}}}
        self._root._send(message)

    def root(self): 
        '''Get a Firebase reference for the root of the Firebase.'''

        return self._root

    def name(self):
        '''Get the last node (name) of this Firebase location.'''

        last_node = [p for p in self.path.split('/') if p][:-1]
        if last_node:
            return last_node
        else:
            return None

    def __str__(self):
        return self._root.base_url + self.path

    def toString(self):
        '''Get the absolute URL corresponding to this Firebase reference's location.'''

        return self.__str__()

    def update(self, value, onComplete=None):
        '''Similar to set, except this will overwrite only children enumerated in value.'''

        message = {'t':'d', 'd':{'r':0, 'a':'m', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message, {'onComplete': onComplete})

    def remove(self, onComplete=None):
        '''Remove the data at this Firebase location.'''

        self.set(None, onComplete=onComplete)

    def off(self, event=None, callback=None, context=None):
        '''Detach a callback previously attached with on.'''

        node = self._root.structure.get(self.path, {})
        eventSets = {}

        if event:
            event_key = '.event-' + event
            eventSets[event_key] = node.get(event_key, [])
        else:
            events = []
            for key,value in node.items():
                if key.startswith('.event-'):
                    eventSets[key] = value

        for eventKey,eventSet in eventSets.items():
            if callback and callback in eventSet:
                eventSet.remove(callback)
            elif event:
                for callback in eventSet:
                    eventSet.remove(callback)
            eventSets[eventKey] = eventSet

        for eventName,eventSet in eventSets.items():
            node[eventName] = eventSet

    def once(self, event,  successCallback=None, failureCallback=None, context=None): 
        '''Listens for exactly one event of the specified event type, and then stops listening.'''

        def once_wrapper(*args, **kwargs):
            successCallback(*args, **kwargs)
            self.off(event, once_wrapper)

        self.on(event, once_wrapper)

    def push(self, value, onComplete=None):
        '''Generate a new child location using a unique name and returns a Firebase reference to it.'''

        pushId = self._get_push_id()
        path = self.path + '/' + pushId

        message = {"t":"d", "d":{"r":0, "a":"p", "b":{"p":path, "d":value }}}
        self._root._send(message, {'onComplete': onComplete})

        return DataRef(self._root, path)

    def transaction(self, updateFunction, onComplete=None): pass

    def limit(self, limit):
        '''Create a new Firebase object limited to the specified number of children.'''

        return DataRef(self._root, self.path, endPoint=self.query_end, startPoint=self.query_start, limit=limit)

    def startAt(self, priority=None, name=None): 
        '''Create a Firebase with the specified starting point.'''

        startPoint = {'priority': priority, 'name': name}
        return DataRef(self._root, self.path, endPoint=self.query_end, startPoint=startPoint, limit=self.query_limit)

    def endAt(self, priority=None, name=None): 
        '''Create a Firebase with the specified ending point.'''

        endPoint = {'priority': priority, 'name': name}
        return DataRef(self._root, self.path, endPoint=endPoint, startPoint=self.query_start, limit=self.query_limit)

    def onDisconnect(self):
        ''' The onDisconnect class allows you to write or clear data when your client disconnects from the Firebase servers. '''

        return onDisconnect(self._root, self.path)

    def _get_query(self):
        ''' Return a query based on limit, startPoint, and endPoint. '''

        query = {}

        if self.query_limit != None:
            query['l'] = self.query_limit

        if self.query_start != None:
            if self.query_start['priority']:
                query['sp'] = self.query_start['priority']
            if self.query_start['name']:
                query['sn'] = self.query_start['name']

        if self.query_end != None:
            if self.query_end['priority']:
                query['ep'] = self.query_end['priority']
            if self.query_end['name']:
                query['en'] = self.query_end['name']

        if len(query.keys()) == 3:
            raise Exception("Query: Can't combine startAt(), endAt(), and limit().")

        return [query] if query != {} else None

    def _get_push_id(self):
        ''' Return a new string containing an ID for pushing. '''

        # This is the only method interpreted directly from the Javascript SDK
        now = datetime.datetime.now()
        a = int(now.strftime('%s%f')[:-3])

        characters = "-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"

        c = [0 for p in range(0, 8)]
        p = []

        for d in reversed(range(0, 8)):
            c[d] = characters[int(a) % 64]
            a = math.floor(a / 64)

        a = "".join(c)

        for d in range(0, 12):
            num = random.randint(0, 63)
            a += characters[num]

        return a

class RootDataRef(DataRef):
    '''A reference to a root of a Firbase.'''

    def __init__(self, url):
        '''Construct a new Firebase reference from a full Firebase URL.'''
        self.connection = Connection(url, self)
        self.base_url = url
        self.structure = Structure(self)
        self.subscriptions = {}
        self.history = []
        self.connection.start()
        DataRef.__init__(self, self, '')

    def _process(self, message):
        '''Process a single incoming message'''

        # This whole thing needs to be rewritten to use all the new information about the protocol
        # and to trigger callbacks based on success, failure, and cancel
        debug(message)

        # If message type is data
        if message['t'] == 'd':
            data = message['d']
            # If r is in data and set to 1 then it's probably a response 
            # to something we sent like a sub request or an auth token
            if 'r' in data:
                historical_entry = self.history[data['r']-1]
                request = historical_entry['message']
                callbacks = historical_entry['callbacks']
                b = data['b'] # B is where the majority of data relavant to the request is stored
                error = b['s']
    
                if error != 'ok':
                    if error == 'permission_denied':
                        path = request['d']['b']['p']
                        print 'FIREBASE WARNING: on() or once() for %s failed: %s' % (path, error)

                    elif error == 'expired_token' or error =='invalid_token':
                        print 'FIREBASE WARNING: auth() failed: %s' % (error)

                    else:
                        path = request['d']['b']['p']
                        print 'FIREBASE WARNING: unknown for %s failed: %s' % (path, error)

                    onCancel = callbacks.get('onCancel', None)
                    if not onCancel is None:
                        onCancel(error)

                onComplete = callbacks.get('onComplete', None)
                if not onComplete is None:
                    onComplete(error if error != 'ok' else None)

            # If t is in data then it's the response to the initial connection, maybe
            elif 't' in data:
                pass

            # If a is in data, it's a new data blob for a node, maybe
            elif 'a' in data:
                b = data['b']
                path = b['p']
                path_data = b['d']
                
                self._store(path, path_data)

        # If message type is... control?
        if message['t'] == 'c':
            pass

    def _store(self, path, path_data):
        '''Store a single path worth of data into the strucutre.'''

        self.structure.store(path, path_data)

    def _send(self, message, callbacks=None):
        '''Send a single message to Firebase.'''

        historical_entry = {
            'message': message,
            'callbacks': {} if callbacks is None else callbacks
        }

        self.history.append(historical_entry)
        message['d']['r'] = len(self.history)
        self.connection.send(message)

    def _subscribe(self, path, query, callbacks=None):
        '''Subscribe to updates regarding a path'''

        isSubscribed = self._is_subscribed(path, query)

        # A subscription (listen) request takes two main arguments, p (path) and q (query). 
        if not isSubscribed:

            message = {"t":"d", "d":{"r":0, "a":"l", "b":{"p":path}}}

            if not query is None:
                message['d']['b']['q'] = query

            self._send(message, callbacks)
            self.subscriptions[path] = query
            return True
        else:
            # Should probably trigger callbacks['onComplete'] here
            return False

    def _bind(self, path, event, callback):
        '''Bind a single callback to an event on a path'''

        event_key = '.event-'+event
        structure_path = self.structure.get(path, {})
        self.structure[path] = structure_path
        events = structure_path.get(event_key, [])
        events.append(callback)
        self.structure[path][event_key] = events

    def _is_subscribed(self, path, query):
        '''Return True if already subscribed to this path or an ancestor.'''

        return any([s.split('/')==path.split('/')[:len(s.split('/'))] for s in self.subscriptions.keys()])

class onDisconnect(object):
    '''Allows writing or clearing of data regardless of quality of disconnect.'''

    def __init__(self, parent, path):
        self._root = parent
        self.path = path

    def set(self, value, onComplete=None): 
        '''Ensure the data at this location is set to the specified value when the client is disconnected.'''

        message = {'t':'d', 'd':{'r':0, 'a':'o', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message, {"onComplete": onComplete})

    def setWithPriority(self, value, priority, onComplete=None):
        '''Ensure the data at this location is set to the specified value and priority when the client is disconnected.'''

        if isinstance(value, dict):
            data = value
        else:
            data = {".value": value}

        data['.priority'] = priority
        self.set(data, onComplete=onComplete)

    def update(self, value, onComplete=None):
        '''Similar to set, except this will overwrite only children enumerated in value when the client is disconnected.'''

        message = {'t':'d', 'd':{'r':0, 'a':'om', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message, {"onComplete": onComplete})

    def remove(self, onComplete=None): 
        '''Ensure the data at this location is deleted when the client is disconnected.'''

        self.set(None, onComplete=onComplete)

    def cancel(self, onComplete=None): 
        '''Cancel all previously queued onDisconnect() set or update events for this location and all children.'''

        message = {"t":"d", "d":{"r":0, "a":"oc", "b":{"p":self.path, "d":None}}}
        self._root._send(message, {"onComplete": onComplete})