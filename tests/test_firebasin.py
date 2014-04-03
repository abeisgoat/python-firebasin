import sys
sys.path.insert(0, '../')

'''
Due to the nature of testing against an online database,
it is hard to create tests which can run out of the box.
Instead, set FIREBASE_URL to an empty firebase and this will
automatically fill the firebase then test against it.

Remember, an EMPTY firebase. 
'''

testdata = {
    'test_child_added': {},
    'test_child_changed': {'child_a': '1'},
    'test_child_removed': {'child_a': '1'},
    'test_value_read': {'child_a': '-test-'}
}

from firebasin import Firebase

FIREBASE_URL = 'https://brilliant-fire-67.firebaseio.com/'

server = Firebase(FIREBASE_URL)


def on_child_added(snapshot):
    print str(snapshot.name()) + ' < child_added to /test_child_added/'


def on_value_read(snapshot):
    print str(snapshot.name()) + str(snapshot.val()) + ' < value of test '


def on_child_added(snapshot):
    print str(snapshot.name()) + ' < child_added to /test_child_added/'

def on_value_read(snapshot):
    print str(snapshot.val())  + ' < value of /test_value_read/' + snapshot.name()

def on_child_removed (snapshot):
    print str(snapshot.val()) + ' < child_removed from /test_child_removed/'

def on_child_added(snapshot):
    print str(snapshot.name()) + ' < child_added to /test_child_added/'

def on_value_read(snapshot):
    print str(snapshot.name()) + str(snapshot.val()) + ' < value of test '

def on_child_changed (snapshot):
    print str(snapshot.name()) + ' < child_changed in /test_child_changed/'

def on_child_added_once (snapshot):
    print str(snapshot.name()) + ' < child_added once!'

def on_value_read_specific(snapshot):
    print snapshot.val(), "<specific"

def onCancel(data):
    print 'On was canceled'

def onComplete(data):
    print 'Set was completed', data


server.child("ask").on('value', on_value_read)
server.child("bid").on('value', on_value_read)

# This is important to interupt the threaded socket when a
# keyboard interupt is received, it allows us to shut down gracefully
server.waitForInterrupt()