import sys
sys.path.insert(0, '../')

# This script will NOT work out of the box
# Replace "greatblue" with an EMPTY firebase
# of your choice, does use it on a full one,
# it might destory data. You've been warned.

from firebasin import Firebase
flame = Firebase('https://greatblue.firebaseio.com')

def child_added_sms(snapshot):  
    print str(snapshot.name()) + ' < child_added to /sms '

def value_dat(snapshot): 
    print str(snapshot.val())  + ' < value of /sms/dat'

def child_removed_sms(snapshot): 
    print str(snapshot.val()) + ' < child_removed from /sms'

def child_added_sms_test(snapshot): 
    print str(snapshot.name()) + ' < child_added to /sms/test'

def value_test(snapshot): 
    print str(snapshot.name()) + str(snapshot.val()) + ' < value of test '

def child_changed_sms(snapshot): 
    print str(snapshot.name()) + ' < sms child changed'

def child_added_sms_once(snapshot): 
    print str(snapshot.name()) + ' <sms child added once!'

def say_body(snapshot): 
    print snapshot.val().get('Body')
    print snapshot.ref()
    print snapshot.child('Body').val(), snapshot.child('Body').ref()
    
def say_specific(snapshot): 
    print snapshot.val()['Body'], "<specific"

def onCancel(data): 
    print 'On was canceled'
def onComplete(data): 
    print 'Set was completed', data

#flame.auth( AUTH_KEY )
sms = flame.child('sms')

# Push only works on Unix boxes, need to fix _get_push_id to work cross platform
#sms.push("Push test") 
sms.on('child_added', child_added_sms, onCancel)
sms.once('child_added', child_added_sms_once)
sms.on('child_removed', child_removed_sms)
sms.child('dat').on('value', value_dat)
sms.child('online').set(True, onComplete)
sms.child('online').setPriority(100)
sms.child('online').onDisconnect().set(False)
sms.child("test").on('child_added', child_added_sms_test)
sms.child("test").on('value', value_test)
sms.child('dat').update({'broom': 'bristle'})
sms.child("test").off('value')

# Querying half works, when your supply a query with a larger scope (ie a "value" bind to a parent)
# it breaks because we're not filtering incoming results.
#sms.startAt(None, '-Ip_SsFU5LY_63gH07x2').limit(3).on('child_added', say_body)
sms.child('-Ip_SxEZ-ZG7Q1yfPiuf').on('value', say_specific)

# This is important to interupt the threaded socket when a 
# keyboard interupt is received, it allows us to shut down gracefully
flame.waitForInterrupt()