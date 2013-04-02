class DataSnapshot(object):
    '''A snapshot of data at a specific location and time.'''

    def __init__(self, path, data, root_ref):
        self.data = data
        self.path = path
        self.root_ref = root_ref

        self.clean_data = self._clean_data(self.data)

    def val(self): 
        '''Return the value of this snapshot.'''
        return self.clean_data

    def child(self, childPath):
        '''Return a DataSnapshot of a child location.'''

        childData = self.data
        nodes = childPath.split('/')
        full_path = self.path + '/' + childPath
        for node in nodes:
            if node:
                childData = childData[node]
            else:
                return DataSnapshot(full_path, None, self.root_ref)
        
        return DataSnapshot(full_path, childData, self.root_ref)

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
            child = self.data
            for node in nodes:
                if node:
                    if node == nodes[-1:]:
                        return node in child
                    else:
                        child = child[node]
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
            return len(self.clean_data.keys())
        else:
            return False

    def ref(self):
        '''Return a DataRef at location of DataSnapshot.'''

        return self.root_ref.child(self.path)

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
                for key, value in data.items():
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