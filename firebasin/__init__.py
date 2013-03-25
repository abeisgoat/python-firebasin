from ws4py.client.threadedclient import WebSocketClient
import json, sys, time, os, threading

class Structure(dict):
	# The store function has two main jobs, firstly it stores entities
	# in self like this: {"/my/cat": {".data": "red"}}
	# Second, it fill changes with a list of changes to self which we
	# then react() on to trigger any callbacks 
	def store(self, root_path, root_path_data):
		changes = []
		def recursive(path, path_data):
			if type(path_data) == type(dict()) and path_data: 
				#print path_data, '<da fuck i sth'
				for node in path_data:
					node_path = os.path.join(path, node)
					node_data = path_data[node]

					if type(node_data) != type(dict()):
						if node_data:
							if node_path in self:
								if '.data' in self[node_path] and self[node_path]['.data']:
									changes.append(['update', node_path, node_data])
									self[node_path][".data"] = path_data[node]
								else:
									changes.append(['create', node_path, node_data])
									self[node_path][".data"] = path_data[node]	
							else:
								changes.append(['create', node_path, node_data])
								self[node_path] = {".data": path_data[node]}

						else:
							changes.append(['delete', node_path, node_data])
							self[node_path][".data"] = None
					else:
						if node_path in self:
							if '.data' in self[node_path] and self[node_path]['.data']:
								changes.append(['update', node_path, node_data])
								self[node_path]['.data'] = None
							else:
								changes.append(['create', node_path, node_data])
								self[node_path]['.data'] = None							
						else:
							changes.append(['create', node_path, node_data])
							self[node_path] = {".data": None}

						recursive(node_path, node_data)
			else:
				if path in self: 
					if '.data' in self[path] and self[path]['.data'] and not path_data:
						changes.append(['delete', path, self.objectify(path)])
						self[path]['.data'] = path_data
				else:
					changes.append(['create', path, path_data])
					self[path] = {'.data': path_data}

		recursive(root_path, root_path_data)
		#print changes
		self.react(changes)
		return True

	def react(self, log):
		#print log
		for action,path,value in sorted(log, key=lambda d: len(d[1])):
			# If the path contains a . (i.e. it's meta data), just ignore it and don't call anything
			if not '.' in path: 
				# We get all the anscestors of this path
				all_ancestors = self.getAncestorsPaths(path)
				# Then take the first and mark it as the parent
				parent = all_ancestors[0]
				# Then take the rest and put them into general ancestors
				ancestors = all_ancestors[1:]

				# Once we know which paths are effected by the changes we
				# can make the proper calls to update them. 

				# Value doesn't appear to be being called as aggresively as needed, it doesn't call
				# when child nodes are updated, so yeah that should get fixed.
				if action == 'create':
					self.trigger(path, 'value', data=value)	
					if value:
						self.trigger(parent, 'child_added', data=value, snapshotPath=path)

					for a in all_ancestors:
						self.trigger(a, 'value', data=self.objectify(a))

				if action == 'update':
					self.trigger(path, 'value', data=value)
					for a in ancestors:
						# Prolly need a snapshotPath set here
						self.trigger(a, 'child_changed', data=value)
						self.trigger(a, 'value', data=self.objectify(a))

				if action == 'delete':
					self.trigger(path, 'value', data=value)
					self.trigger(parent, 'child_removed', data=value, snapshotPath=path)

					for a in all_ancestors:
						self.trigger(a, 'value', data=self.objectify(a))

	def getAncestorsPaths(self, path):
		nodes = path.split('/')
		ancestors = []
		for n in range(0, len(nodes)):
			ancestors.append('/'.join(nodes[:-n]))
		return [a for a in ancestors if a]

	def trigger(self, path, event, data=None, snapshotPath=None):
		event_key = '.'+event

		if not snapshotPath:
			snapshotPath = path

		if path in self:
			path_node = self[path]
			#print path_node, path
			if path_node and event_key in path_node:
				callbacks = path_node[event_key]

				obj = DataSnapshot(snapshotPath, data)

				for callback in callbacks:
					callback(obj)
			else:
				return False
		else:
			return False


	def objectify(self, path):
		children = sorted(self.children(path), key=lambda d: len(d))
		# This path_length hack breaks stuff, it, replace with proper node removing
		path_length = len(path)
		obj = {}   
		if len(children) > 1:
			for child_path in children:
				nodes = child_path[path_length:].split('/')
				o = obj
				for node in nodes:
					if node:
						if not node in o:
							if self[child_path].get('.data', False):
								o[node] = self[child_path]['.data']
							else:
								o[node] = {}
						o = o[node]
		else:
			obj = self[path]['.data']

		def clean(tree):
			if type(tree) == type(dict()):
				for child in tree.keys():
					if tree[child] == {}:
						tree.pop(child)
					elif type(tree[child]) == type(dict()):
						clean(tree[child])

		clean(obj)
		return obj


	def children(self, path):
		return [a for a in self.keys() if a[:len(path)] == path]

# Connection which threads the handshake and data websockets into a managable bundle
class Connection(threading.Thread):
	def __init__(self, url, parent):
		threading.Thread.__init__(self)

		self.parsed_url = self.parse_url(url)
		self.parent = parent
		self.outgoing_quene = []
		self.incoming_quene = []
		self.url = None
		self.handshake = None
		self.data = None
		self.connected = False
		self.stopped = False

	def run(self):
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
		self.data = DataClient('wss://' + self.url + '/.ws?v=5&ns=' + self.parsed_url[0])
		self.data.on_opened = self.process_outgoing_quene

		def on_received(o):
			self.incoming_quene.append(o)
			self.parent.process_incoming_quene()

		def on_closed(data):
			self.stopped = True

		self.data.on_received = on_received
		self.data.on_closed = on_closed

		self.data.connect()

		while self.data._th.is_alive() and not self.stopped:
			self.data._th.join(1)

		self.data.close()

	def process_outgoing_quene(self):
		for message in self.outgoing_quene:
			self.data.send(json.dumps(message))

	# All internal functions are shown here
	def parse_url(self, url):
		return url.split('https://')[1].split('.')

# DataRefs are used as reference to specific locations in a firebase
class DataRef(object):
	# Parent is a reference to the base Firebase which holds our connection object
	# and path is a string containing a path like '/user/example/name'
	def __init__(self, parent, path):
		self.parent = parent
		self.path = os.path.join('/', path)

	# All client facing functions are shown here
	def on(self, event, callback):
		structure_path = self.parent.structure.get(self.path, {})
		self.parent.structure[self.path] = structure_path
		events = structure_path.get('.'+event, [])
		events.append(callback)
		self.parent.structure[self.path]['.'+event] = events
		#print self.parent.structure[self.path], self.path

		if not self.path in self.parent.subscriptions:
			self.parent.subscriptions.append(self.path)

			message = {"t":"d","d":{"r":1,"a":"l","b":{"p":self.path}}}
			self.parent.c.outgoing_quene.append(message)

	# Get a DataRef to a child of this DataRef
	def child(self, path):
		return DataRef(self.parent, os.path.join(self.path, path))

	# Get the DateRef of the element directly above this
	def parent(self):
		if self.path != '':
			parent_path = '/'.join(self.path.split('/')[-1:])
			return DataRef(self.parent, parent_path)
		else:
			return None

	def auth(self, auth_token, callback=None):
		message = {"t":"d","d":{"r":1,"a":"auth","b":{"cred":auth_token}}}
		self.parent.auth_callback = callback
		self.parent.c.outgoing_quene.append(message)

class DataSnapshot(object):
	def __init__(self, path, data):
		self.data = data
		self.path = path

	def val(self): 
		return {key:value for (key, value) in self.data.items() if key[0] != '.'}

	def child(self, childPath):
		c = self.data
		nodes = childPath.split('/')
		for node in nodes:
			if node:
				c = c[node]
		return c

	def forEach(self, callback):
		for key in self.data.keys():
			response = callback(self.data[key])
			if response:
				return True
		return False

	def hasChild(self, childPath):
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
		return type(self.data) == type(dict()) and len(self.data.keys())

	def name(self):
		return self.path.split('/')[-1:][0]

	def numChildren(self):
		if self.hasChildren():
			return len(self.keys())
		else:
			return False

	def ref(self):
		# Not sure how I'm gonna get the ref here 
		pass

	def getPriority(self): 
		return self.data['.priority'] if '.priority' in self.data else None

	def exportVal(self): 
		return self.data

# Firebase is the top level node which is just a DateRef with a hard-coded 
# path, a connection, and a tree of the database
class Firebase(DataRef):
	def __init__(self, url):
		self.c = Connection(url, self)
		#self.structure = Tree()
		self.structure = Structure()
		self.subscriptions = []
		self.auth_callback = None
		self.c.start()
		DataRef.__init__(self, self, '')

	def process_incoming_quene(self):
		for message in self.c.incoming_quene:
			# If message type is data
			if message['t'] == 'd':
				data = message['d']
				# If r is in data and set to 1 then it's probably a response 
				# to something we sent like a sub request or an auth token
				if 'r' in data and data['r']:
					b = data['b'] # B is where the majority of data relavant to the request is stored
					if b['s'] == 'invalid_token':
						# If an auth callback was specified when DataRef.auth was called, let it know it didn't go through
						if self.auth_callback:
							self.auth_callback(b, None)
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
					
					self.store(path, path_data)

			# If message type is... control?
			if message['t'] == 'c':
				pass
		self.c.incoming_quene = []

	def store(self, path, path_data):
		self.structure.store(path, path_data)

# DataClient is just a WebSocketClient who stores the incoming messages
class DataClient(WebSocketClient):
	def __init__(self, url):
		WebSocketClient.__init__(self, url)
		self.data = []

	def opened(self):
		print 'Connected to the data server :D'
		if 'on_opened' in dir(self):
			self.on_opened()

	def closed(self, code, reason):
		print(("Closed down :(", code, reason))
		if 'on_closed' in dir(self):
			self.on_closed(self.data)

	def received_message(self, m):
		obj = json.loads(str(m))
		self.data.append(obj)
		if 'on_received' in dir(self):
			self.on_received(obj)

if __name__ == '__main__':
	fb = Firebase('https://greatblue.firebaseio.com')

	def p(d):  print str(d.name()) + ' < child_added to /sms '
	def pa(d): print str(d.name()) + ' < value of /sms/dat'
	def pr(d): print str(d.name()) + ' < child_removed from /sms'
	def ba(d): print str(d.name()) + ' < child_added to /sms/test'
	def bo(d): print str(d.name()) + str(d.val()) + ' < value of test '

	fb.auth('eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpYXQiOiAxMzY0MTk2NTUxLCAiZCI6IHsidXNlciI6ICJ0d2lsaW8iLCAicHJvdmlkZXIiOiAidG9rZW4ucHkifSwgInYiOiAwfQ.7zxE63N_oLpgSvfVojtU6nNsdbnLopRS6WRF5j_JK5A')
	sms = fb.child('sms')
	sms.on('child_added', p)
	sms.on('child_removed', pr)
	sms.child('dat').on('value', pa)
	sms.child("test").on('child_added', ba)
	sms.child("test").on('value', bo)

	try:
		while 1: time.sleep(1)
	except KeyboardInterrupt:
		fb.c.stopped = True