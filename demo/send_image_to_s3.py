#!/usr/bin/env python
import requests
import collections
import sys

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " IMG_PATH"
    sys.exit(1)

r = requests.post("https://demo-excamera.s3.amazonaws.com/",
                  data=collections.OrderedDict(
                      {'key': 'uploaded-faces/john.jpg', 
                       'AWSAccessKeyId': 'AKIAJ4YD5RZTAMXCRS6A', 
                       'acl': 'private',
                       'success_action_redirect' : 'https://hq1pnoxl8b.execute-api.us-east-1.amazonaws.com/prod',
                       'policy' : 'CnsKICAgImV4cGlyYXRpb24iOiAiMjAxOS0wMS0wMVQwMDowMDowMFoiLAogICAiY29uZGl0aW9ucyI6IFsgCiAgICAgeyJidWNrZXQiOiAiZGVtby1leGNhbWVyYSJ9LCAKICAgICBbInN0YXJ0cy13aXRoIiwgIiRrZXkiLCAidXBsb2FkZWQtZmFjZXMvIl0sCiAgICAgeyJhY2wiOiAicHJpdmF0ZSJ9LAogICAgIHsic3VjY2Vzc19hY3Rpb25fcmVkaXJlY3QiOiAiaHR0cHM6Ly9ocTFwbm94bDhiLmV4ZWN1dGUtYXBpLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL3Byb2QifSwKICAgICBbInN0YXJ0cy13aXRoIiwgIiRDb250ZW50LVR5cGUiLCAiIl0sCiAgICAgWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDAsIDEwNDg1NzZdCiAgXQp9Cg==',
                       'signature' : 'DbutOkj3U+i83WOoaoyudQYaAUY=',
                       'Content-Type' : 'image/jpeg',
                  }),
                  files={'file': open(sys.argv[1], 'rb')}
              )

if( r.status_code == 200  ):
    print "SUCCESS!"
else:
    print "FAILURE", r.status_code
    sys.exit(1)
