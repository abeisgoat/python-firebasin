from firebase import Firebase
import time

if __name__ == '__main__':
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
        print snapshot.val()['Body'], "<unique?"

    def onCancel(data): 
        print 'On was canceled'
    def onComplete(data): 
        print 'Set was completed', data

    flame.auth('eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpYXQiOiAxMzY0ODkxNzUzLCAiZCI6IHsidXNlciI6ICJ0d2lsaW8iLCAicHJvdmlkZXIiOiAidG9rZW4ucHkifSwgInYiOiAwfQ.hXTZg95Rt2_1o1zYEH2s2S53UGLhklcC0lNYnENiSzY')
    sms = flame.child('sms')
    sms.push("Push test")
    #sms.on('child_added', child_added_sms, onCancel)
    #sms.once('child_added', child_added_sms_once)
    #sms.on('child_removed', child_removed_sms)
    #sms.child('dat').on('value', value_dat)
    #sms.child('online').set(True, onComplete)
    #sms.child('online').setPriority(100)
    #sms.child('online').onDisconnect().set(False)
    #sms.child("test").on('child_added', child_added_sms_test)
    #sms.child("test").on('value', value_test)
    #sms.child('dat').update({'broom': 'bristle'})
    #sms.child("test").off('value')

    sms.startAt(None, '-Ip_SsFU5LY_63gH07x2').limit(3).on('child_added', say_body)
    sms.child('-Ip_SxEZ-ZG7Q1yfPiuf').on('value', say_specific)

    try:
        while 1: 
            time.sleep(1)
    except KeyboardInterrupt:
        flame.connection.stopped = True