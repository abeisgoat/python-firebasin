from ws4py.client.threadedclient import WebSocketClient
import json, sys, time, os, threading

class Structure(dict):
	'''Hold data related to paths in an organized way.'''

	def store(self, root_path, root_path_data):
		'''Store a dict recursively as paths.'''

		changes = []
		def recursive(path, path_data):
			if type(path_data) == type(dict()) and path_data: 
				for node in path_data:
					node_path = os.path.join(path, node)
					node_data = path_data[node]

					change = self.store_one(node_path, node_data)
					changes.append(change)

					if type(node_data) == type(dict()):
						recursive(node_path, node_data)
			else:
				changes.append(self.store_one(path, path_data))

		recursive(root_path, root_path_data)
		self.react(changes)
		return True

	def store_one(self, path, path_data):
		'''Store a single dict or value as a path.'''

		change = []
		if path in self: 
			if '.data' in self[path] and self[path]['.data'] and not path_data:
				change = ['delete', path, None]
				self[path]['.data'] = None

			elif '.data' in self[path] and self[path]['.data'] and path_data:
				change = ['update', path, path_data]
				self[path]['.data'] = path_data
				for anscestor in self.ancestors(path):
					a = self.get(anscestor, {})
					a['.data'] = {}
					self[anscestor] = a

			else:
				change = ['create', path, path_data]
				for anscestor in self.ancestors(path):
					a = self.get(anscestor, {})
					a['.data'] = {}
					self[anscestor] = a
				self[path]['.data'] = path_data

		else:
			change = ['create', path, path_data]
			for anscestor in self.ancestors(path):
				a = self.get(anscestor, {})
				a['.data'] = {}
				self[anscestor] = a
			self[path] = {'.data': path_data}

		return change

	def react(self, log):
		'''Call events based on a list of changes.'''

		for action,path,value in sorted(log, key=lambda d: len(d[1])):
			# If the path contains a . (i.e. it's meta data), just ignore it and don't call anything
			if not '.' in path: 
				all_ancestors = self.ancestors(path)
				parent = all_ancestors[0]
				ancestors = all_ancestors[1:]

				if action == 'create':
					self.trigger(path, 'value', data=value)	
					if value:
						self.trigger(parent, 'child_added', data=value, snapshotPath=path)

					for a in all_ancestors:
						self.trigger(a, 'value', data=self.objectify(a))

				if action == 'update':
					self.trigger(path, 'value', data=value)
					for a in all_ancestors:
						self.trigger(a, 'child_changed', data=value, snapshotPath=path)
						self.trigger(a, 'value', data=self.objectify(a))

				if action == 'delete':
					data = self.objectify(path)
					self.trigger(path, 'value', data=data)
					self.trigger(parent, 'child_removed', data=data, snapshotPath=path)

					for a in all_ancestors:
						self.trigger(a, 'value', data=self.objectify(a))

	def trigger(self, path, event, data, snapshotPath=None):
		'''Call all functions related to an event on path.'''

		event_key = '.event-'+event

		if not snapshotPath:
			snapshotPath = path

		if path in self:
			path_node = self[path]
			if path_node and event_key in path_node:
				# If the "updated" data and the old data are the same, don't do anything
				if data != path_node.get('.last-data'):
					if data==None:
						# If data is None, we pass the old data (for DELETE)
						snapshotData = path_node.get('.last-data')
					else:
						# Otherwise we just set last-data appropriately and set snapshotData to the new data
						path_node['.last-data'] = data
						snapshotData = data

					callbacks = path_node[event_key]

					obj = DataSnapshot(snapshotPath, snapshotData)

					for callback in callbacks:
						callback(obj)
			else:
				return False
		else:
			return False


	def objectify(self, path):
		'''Return an object version of a path.'''

		def recursive(rpath):
			obj = {}
			data = self[rpath].get('.data', {})

			children_paths = self.children(rpath)
			children_last_nodes = self.last_nodes(children_paths)

			if type(data) != type(dict()):
				return data

			for key in children_last_nodes:
				kpath = os.path.join(rpath, key)
				kpath_node = self[kpath]
				if '.data' in kpath_node:
					kpath_data = kpath_node['.data']
					if kpath_data or kpath_data == {}:
						if type(kpath_data) == type(dict()):
							obj[key] = recursive(kpath)
							if obj[key] == {}:
								obj.pop(key)
						else:
							obj[key] = kpath_data

			return obj

		obj = recursive(path)
		return obj


	def children(self, parent):
		'''Return direct children of path in self.'''

		parent_nodes = self.nodes(parent)
		children = []
		for path in self:
			path_nodes = self.nodes(path)
			if path_nodes[:len(parent_nodes)] == parent_nodes and len(path_nodes) == len(parent_nodes) + 1:
				children.append(path)
		return children


	def descendants(Self, path):
		'''Return all descendants of path in self.'''

		parent_nodes = self.nodes(parent)
		children = []
		for path in self:
			path_nodes = self.nodes(path)
			if path_nodes[:len(parent_nodes)] == parent_nodes and path_nodes != parent_nodes:
				children.append(path)
		return children

	def ancestors(self, path):
		'''Return all anscestors of a path.'''

		nodes = path.split('/')
		ancestors = []
		for n in range(0, len(nodes)):
			ancestors.append('/'.join(nodes[:-n]))
		return [a for a in ancestors if a]

	def nodes(self, path):
		'''Returns a list containing individual nodes in a path.'''

		dirty_nodes = path.split('/')
		clean_nodes = []
		for node in dirty_nodes:
			if node:
				clean_nodes.append(node)
		return clean_nodes

	def first_node(self, path):
		'''Return the first node in a path.'''

		nodes = self.nodes(path)
		return nodes[0]

	def last_node(self, path):
		'''Return the last node in a path.'''

		nodes = self.nodes(path)
		return nodes[-1:][0]

	def first_nodes(self, paths):
		'''Return the first nodes for each path in paths.'''

		nodes = []
		for path in paths:
			first_node = self.first_node(path)
			nodes.append(first_node)
		return nodes


	def last_nodes(self, paths):
		'''Return the last nodes for each path in paths.'''

		nodes = []
		for path in paths:
			last_node = self.last_node(path)
			nodes.append(last_node)
		return nodes

class Connection(threading.Thread):
	'''Connect to a Firebase websocket.'''

	def __init__(self, url, parent):
		threading.Thread.__init__(self)

		self.parsed_url = self.parse_url(url)
		self.parent = parent
		self.outgoing_quene = []
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
		self.handshake.on_received= set_url
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
			print 'Dictionary URL Received'
			self.url = self.url['h']

		self.data = DataClient('wss://' + self.url + '/.ws?v=5&ns=' + self.parsed_url[0])
		self.data.on_opened = self.send_outgoing

		def on_connected():
			self.connected = True

		def on_received(o):
			self.parent._process(o)

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
		'''Send all quened outgoing messages to Firebase.'''

		for message in self.outgoing_quene:
			self.data.send(json.dumps(message))

	def send(self, message):
		'''Send or quene a single message to a Firebase.'''

		if not self.connected:
			self.outgoing_quene.append(message)
		else:
			self.data.send(message)

	def parse_url(self, url):
		'''Parse a URL.'''

		return url.split('https://')[1].split('.')

class DataRef(object):
	'''Reference a specific location in a Firebase.'''

	def __init__(self, parent, path):
		self.parent = parent
		self.path = os.path.join('/', path)

	def on(self, event, callback, on_cancel=None, context=None):
		'''Connect a callback to an event.'''

		self.parent._bind(self.path, event, callback)
		self.parent._subscribe(self.path)

	def set(self, data, on_complete=None):
		'''Write data to this Firebase location.'''

		message = {"t":"d","d":{"r":0, "a":"p", "b":{"p":self.path, "d":data }}}
		self.parent._send(message)

	def setWithPriority(self, data, priority, on_complete=None):
		'''Write data like set, but also specify the priority for that data.'''

		data['.priority'] = priority
		self.set(data, on_complete=on_complete)

	def setPriority(self, priority, on_complete=None):
		'''Set a priority for the data at this Firebase location.'''

		self.child('.priority').set(priority)

	def child(self, path):
		'''Return a new DataRef of a child location.'''

		return DataRef(self.parent, os.path.join(self.path, path))

	def parent(self):
		'''Return the parent of this location.'''

		if self.path != '':
			parent_path = '/'.join(self.path.split('/')[-1:])
			return DataRef(self.parent, parent_path)
		else:
			return None

	def auth(self, auth_token, on_complete=None, on_cancel=None):
		'''Send an authentication token.'''

		message = {"t":"d","d":{"r":0,"a":"auth","b":{"cred":auth_token}}}
		self.parent._send(message)

	def unauth(self): pass

	def root(self): 
		'''Get a Firebase reference for the root of the Firebase.'''

		return self.parent

	def name(self):
		'''Get the last node (name) of this Firebase location.'''

		last_node = [p for p in self.path.split('/') if p][:-1]
		if last_node:
			return last_node
		else:
			return None

	def __str__(self):
		return self.parent.url + self.path

	def toString(self):
		'''Get the absolute URL corresponding to this Firebase reference's location.'''
		return self.__str__()

	def update(self, value, on_complete=None):
		'''Similar to set, except this will overwrite only children enumerated in value.'''

		message = {'t':'d','d':{'r':0,'a':'m','b':{'p':self.path,'d':value}}}
		self.parent._send(message)

	def remove(self, on_complete=None):
		'''Remove the data at this Firebase location.'''
		self.set(None, on_complete=on_complete)

	def push(self, value, on_complete=None): pass
	def transaction(self, updateFunction, on_complete=None): pass
	def off(self, event=None, callback=None, context=None): pass
	def once(self, event, on_success=None, on_failure=None, context=None): pass

	# Query methods
	def limit(self, limit): pass
	def startAt(self, priority=None, name=None): pass
	def endAt(self, priority=None, name=None): pass

	def onDisconnect(self):
		''' The onDisconnect class allows you to write or clear data when your client disconnects from the Firebase servers. '''
		return onDisconnect(self.parent, self.path)

class DataSnapshot(object):
	'''A snapshot of data at a specific location and time.'''

	def __init__(self, path, data):
		self.data = data
		self.path = path

		self.clean_data = self._clean_data(self.data)
		

	def val(self): 
		'''Return the value of this snapshot.'''
		return self.clean_data

	def child(self, childPath):
		'''Return a DataSnapshot of a child location.'''

		c = self.data
		nodes = childPath.split('/')
		for node in nodes:
			if node:
				c = c[node]
		return c

	def forEach(self, callback):
		'''Call a function for each child.'''

		for key in self.data.keys():
			response = callback(self.data[key])
			if response:
				return True
		return False

	def hasChild(self, childPath):
		'''Return True if child exists in data.'''

		if type(self.data) == type(dict()):
			nodes = childPath.split('/')
			c = self.data
			for node in nodes:
				if node:
					if node == nodes[-1:]:
						return node in c
					else:
						c = c[node]
		else:
			return False

	def hasChildren(self):
		'''Return True if data has children.'''

		return type(self.data) == type(dict()) and len(self.data.keys())

	def name(self):
		'''Return name of DataSnapshot.'''

		return self.path.split('/')[-1:][0]

	def numChildren(self):
		'''Return number of children.'''

		if self.hasChildren():
			return len(self.keys())
		else:
			return False

	def ref(self):
		'''Return a DataRef at location of DataSnapshot.'''
		# Not sure how I'm gonna get the ref here 
		pass

	def getPriority(self): 
		'''Return the priority of the data in this snapshot.'''

		return self.data['.priority'] if '.priority' in self.data else None

	def exportVal(self): 
		'''Return all data related to this snapshot including priority.'''

		return self.data

	def _clean_data(self, data):
		'''Cleans data of all hidden (.) fields and converts .value fields.'''

		def recursive(data):
			obj = {}
			if isinstance(data, dict):
				for key,value in data.items():
					if isinstance(value, dict):
						obj[key] = recursive(value)
					elif not key.startswith('.'):
						obj[key] = value
					elif key == '.value':
						return value
				return obj
			else:
				return data

		return recursive(data)

class onDisconnect(object):
	'''Allows writing or clearing of data regardless of quality of disconnect.'''

	def __init__(self, parent, path):
		self.parent = parent
		self.path = path

	def set(self, value, on_complete=None): 
		'''Ensure the data at this location is set to the specified value when the client is disconnected.'''

		message = {'t':'d','d':{'r':0,'a':'o','b':{'p':self.path,'d':value}}}
		self.parent._send(message)

	def setWithPriority(self, value, priority, on_complete=None):
		'''Ensure the data at this location is set to the specified value and priority when the client is disconnected.'''

		if isinstance(value, dict):
			data = value
		else:
			data = {".value": value}

		data['.priority'] = priority
		self.set(data, on_complete=on_complete)

	def update(self, value, on_complete=None):
		'''Similar to set, except this will overwrite only children enumerated in value when the client is disconnected.'''

		message = {'t':'d','d':{'r':0,'a':'om','b':{'p':self.path,'d':value}}}
		self.parent._send(message)

	def remove(self, on_complete=None): 
		'''Ensure the data at this location is deleted when the client is disconnected.'''

		self.set(None, on_complete=on_complete)

	def cancel(self, on_complete=None): 
		'''Cancel all previously queued onDisconnect() set or update events for this location and all children.'''

		message = {"t":"d","d":{"r":0,"a":"oc","b":{"p":self.path,"d":None}}}
		self.parent._send(message)

class Firebase(DataRef):
	'''A reference to a Firbase.'''

	def __init__(self, url):
		'''Construct a new Firebase reference from a full Firebase URL.'''
		self.c = Connection(url, self)
		self.base_url = url
		self.structure = Structure()
		self.subscriptions = []
		self.callbacks = []
		self.c.start()
		DataRef.__init__(self, self, '')

	def _process(self, message):
		'''Process a single incoming message'''
		# This whole thing needs to be rewritten to use all the new information about the protocol
		# and to trigger callbacks based on success, failure, and cancel
		
		# If message type is data
		print message
		if message['t'] == 'd':
			data = message['d']
			# If r is in data and set to 1 then it's probably a response 
			# to something we sent like a sub request or an auth token
			if 'r' in data and data['r']:
				b = data['b'] # B is where the majority of data relavant to the request is stored
				if b['s'] == 'invalid_token':
					pass
				if b['s'] == 'permission_denied':
					pass

			# If t is in data then it's the response to the initial connection
			elif 't' in data:
				pass

			# If a is in data, it's a new data blob for a node
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

		self.callbacks.append({})
		message['d']['r'] = len(self.callbacks)
		self.c.send(message)

	def _subscribe(self, path):
		'''Subscribe to updates regarding a path'''

		isSubscribed = any([s.split('/')==path.split('/')[:len(s.split('/'))] for s in self.subscriptions])
		if not isSubscribed:
			message = {"t":"d","d":{"r":0,"a":"l","b":{"p":path}}}
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

class DataClient(WebSocketClient):
	'''Connect to a web socket.'''

	def __init__(self, url):
		WebSocketClient.__init__(self, url)
		self.data = []

	def opened(self):
		'''Call callback on_opened'''

		print 'Connected to the data server :D'
		if 'on_opened' in dir(self):
			self.on_opened()

	def closed(self, code, reason):
		'''Call callback on_closed.'''

		print(("Closed down :(", code, reason))
		if 'on_closed' in dir(self):
			self.on_closed(self.data)

	def received_message(self, m):
		'''Store received message and call on_received.'''

		obj = json.loads(str(m))
		self.data.append(obj)
		if 'on_received' in dir(self):
			self.on_received(obj)

if __name__ == '__main__':
	fb = Firebase('https://greatblue.firebaseio.com')

	def p(d):  print str(d.name()) + ' < child_added to /sms '
	def pa(d): print str(d.val())  + ' < value of /sms/dat'
	def pr(d): print str(d.val()) + ' < child_removed from /sms'
	def ba(d): print str(d.name()) + ' < child_added to /sms/test'
	def bo(d): print str(d.name()) + str(d.val()) + ' < value of test '
	def cc(d): print str(d.name()) + ' < sms child changed'

	fb.auth('eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpYXQiOiAxMzY0MzQ0MzQ5LCAiZCI6IHsidXNlciI6ICJ0d2lsaW8iLCAicHJvdmlkZXIiOiAidG9rZW4ucHkifSwgInYiOiAwfQ.YFJsFrhER3G-RVdC0_U8uwdYmUwdaM3eDANUAOXFhyc')
	sms = fb.child('sms')
	sms.on('child_added', p)
	sms.on('child_removed', pr)
	sms.child('dat').on('value', pa)
	sms.child('online').set(True)
	sms.child('online').setPriority(100)
	sms.child('online').onDisconnect().set(False)
	sms.child("test").on('child_added', ba)
	sms.child("test").on('value', bo)
	sms.child('dat').update({'broom': 'bristle'})

	try:
		while 1: time.sleep(1)
	except KeyboardInterrupt:
		fb.c.stopped = True