from connection import *
from structure import *
from debug import *

class DataRef(object):
    '''Reference a specific location in a Firebase.'''

    def __init__(self, root, path):
        self._root = root
        self.path = '/' + '/'.join([p for p in path.split('/') if p])

    def on(self, event, callback, onCancel=None, context=None):
        '''Connect a callback to an event.'''

        self._root._bind(self.path, event, callback)
        self._root._subscribe(self.path)

    def set(self, data, onComplete=None):
        '''Write data to this Firebase location.'''

        message = {"t":"d", "d":{"r":0, "a":"p", "b":{"p":self.path, "d":data }}}
        self._root._send(message)

    def setWithPriority(self, data, priority, onComplete=None):
        '''Write data like set, but also specify the priority for that data.'''

        data['.priority'] = priority
        self.set(data, onComplete=on_complete)

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
        self._root._send(message)

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
        return self._root.url + self.path

    def toString(self):
        '''Get the absolute URL corresponding to this Firebase reference's location.'''

        return self.__str__()

    def update(self, value, onComplete=None):
        '''Similar to set, except this will overwrite only children enumerated in value.'''

        message = {'t':'d', 'd':{'r':0, 'a':'m', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message)

    def remove(self, onComplete=None):
        '''Remove the data at this Firebase location.'''
        self.set(None, onComplete=on_complete)

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
        pass

    def push(self, value, onComplete=None): pass
    def transaction(self, updateFunction, onComplete=None): pass

    # Query methods
    def limit(self, limit): pass
    def startAt(self, priority=None, name=None): pass
    def endAt(self, priority=None, name=None): pass

    def onDisconnect(self):
        ''' The onDisconnect class allows you to write or clear data when your client disconnects from the Firebase servers. '''
        return onDisconnect(self._root, self.path)

class RootDataRef(DataRef):
    '''A reference to a root of a Firbase.'''

    def __init__(self, url):
        '''Construct a new Firebase reference from a full Firebase URL.'''
        self.connection = Connection(url, self)
        self.base_url = url
        self.structure = Structure()
        self.subscriptions = []
        self.callbacks = []
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
                debug(self.callbacks[data['r']-1])
                b = data['b'] # B is where the majority of data relavant to the request is stored
                if b['s'] == 'invalid_token':
                    pass
                if b['s'] == 'permission_denied':
                    pass

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

    def _send(self, message):
        '''Send a single message to Firebase.'''

        self.callbacks.append(message)
        message['d']['r'] = len(self.callbacks)
        self.connection.send(message)

    def _subscribe(self, path):
        '''Subscribe to updates regarding a path'''

        isSubscribed = any([s.split('/')==path.split('/')[:len(s.split('/'))] for s in self.subscriptions])
        if not isSubscribed:
            message = {"t":"d", "d":{"r":0, "a":"l", "b":{"p":path}}}
            self._send(message)
            self.subscriptions.append(path)
            return True
        else:
            return False

    def _bind(self, path, event, callback):
        '''Bind a single callback to an event on a path'''

        event_key = '.event-'+event
        structure_path = self.structure.get(path, {})
        self.structure[path] = structure_path
        events = structure_path.get(event_key, [])
        events.append(callback)
        self.structure[path][event_key] = events

class onDisconnect(object):
    '''Allows writing or clearing of data regardless of quality of disconnect.'''

    def __init__(self, parent, path):
        self._root = parent
        self.path = path

    def set(self, value, onComplete=None): 
        '''Ensure the data at this location is set to the specified value when the client is disconnected.'''

        message = {'t':'d', 'd':{'r':0, 'a':'o', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message)

    def setWithPriority(self, value, priority, onComplete=None):
        '''Ensure the data at this location is set to the specified value and priority when the client is disconnected.'''

        if isinstance(value, dict):
            data = value
        else:
            data = {".value": value}

        data['.priority'] = priority
        self.set(data, onComplete=on_complete)

    def update(self, value, onComplete=None):
        '''Similar to set, except this will overwrite only children enumerated in value when the client is disconnected.'''

        message = {'t':'d', 'd':{'r':0, 'a':'om', 'b':{'p':self.path, 'd':value}}}
        self._root._send(message)

    def remove(self, onComplete=None): 
        '''Ensure the data at this location is deleted when the client is disconnected.'''

        self.set(None, onComplete=on_complete)

    def cancel(self, onComplete=None): 
        '''Cancel all previously queued onDisconnect() set or update events for this location and all children.'''

        message = {"t":"d", "d":{"r":0, "a":"oc", "b":{"p":self.path, "d":None}}}
        self._root._send(message)