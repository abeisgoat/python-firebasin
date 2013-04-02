from dataref import *

if __name__ == '__main__':
    fb = RootDataRef('https://greatblue.firebaseio.com')

    def child_added_sms(d):  print str(d.name()) + ' < child_added to /sms '
    def value_dat(d): print str(d.val())  + ' < value of /sms/dat'
    def child_removed_sms(d): print str(d.val()) + ' < child_removed from /sms'
    def child_added_sms_test(d): print str(d.name()) + ' < child_added to /sms/test'
    def value_test(d): print str(d.name()) + str(d.val()) + ' < value of test '
    def child_changed_sms(d): print str(d.name()) + ' < sms child changed'

    fb.auth('eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpYXQiOiAxMzY0MzQ0MzQ5LCAiZCI6IHsidXNlciI6ICJ0d2lsaW8iLCAicHJvdmlkZXIiOiAidG9rZW4ucHkifSwgInYiOiAwfQ.YFJsFrhER3G-RVdC0_U8uwdYmUwdaM3eDANUAOXFhyc')
    sms = fb.child('sms')
    sms.on('child_added', child_added_sms)
    sms.on('child_removed', child_removed_sms)
    sms.child('dat').on('value', value_dat)
    sms.child('online').set(True)
    sms.child('online').setPriority(100)
    sms.child('online').onDisconnect().set(False)
    sms.child("test").on('child_added', child_added_sms_test)
    sms.child("test").on('value', value_test)
    sms.child('dat').update({'broom': 'bristle'})
    sms.child("test").off('value')

    try:
        while 1: time.sleep(1)
    except KeyboardInterrupt:
        fb.connection.stopped = True