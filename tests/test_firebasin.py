import sys
sys.path.insert(0, '../')

'''
Due to the nature of testing against an online database,
it is hard to create tests which can run out of the box.
Instead, set FIREBASE_URL to an empty firebase and this will
automatically fill the firebase then test against it.

Remember, an EMPTY firebase. 
'''

FIREBASE_URL = 'https://firebasin-testbed.firebaseio.com'

testdata = {
    'test_child_added': {},
    'test_child_changed': {'child_a': '1'},
    'test_child_removed': {'child_a': '1'},
    'test_value_read': {'child_a': '-test-'}
}

from firebasin import Firebase
flame = Firebase(FIREBASE_URL)

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

#flame.auth( AUTH_KEY )

# Push only works on Unix boxes, need to fix _get_push_id to work cross platform
#sms.push("Push test") 
flame.on('child_added', on_child_added, onCancel)
flame.once('child_added', on_child_added)
flame.on('child_removed', on_child_removed )
flame.child('dat').on('value', on_value_read)
flame.child('online').set(True, onComplete)
flame.child('online').setPriority(100)
flame.child('online').onDisconnect().set(False)
flame.child("test").on('child_added', on_child_added)
flame.child("test").on('value', on_value_read)
flame.child('dat').update({'broom': 'bristle'})
flame.child("test").off('value')

# Querying half works, when your supply a query with a larger scope (ie a "value" bind to a parent)
# it breaks because we're not filtering incoming results.
#sms.startAt(None, '-Ip_SsFU5LY_63gH07x2').limit(3).on('child_added', say_body)
flame.child('-Ip_SxEZ-ZG7Q1yfPiuf').on('value', on_value_read_specific)

# This is important to interupt the threaded socket when a 
# keyboard interupt is received, it allows us to shut down gracefully
flame.waitForInterrupt()