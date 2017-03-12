#!/usr/bin/env python
import ConfigParser
import base64
import requests
import json
import sys
import timeit

config = ConfigParser.ConfigParser()
config.readfp(open('/home/jemmons/demo_excamera_auth.cfg'))
# print config.get('demo_excamera', 'x-api-key')

if len(sys.argv) != 2:
    print 'Usage: ' + sys.argv[0] + ' IMG_PATH'
    sys.exit(1)


start_encode = timeit.default_timer()    
encoded_image = base64.b64encode( open(sys.argv[1], 'rb').read() )
end_encode = timeit.default_timer()    
print 'encode time,', end_encode - start_encode

start_request = timeit.default_timer()    
r = requests.put('https://3n61exvxul.execute-api.us-east-1.amazonaws.com/prod/demo-excamera-uploadface',
                 headers={
                     "x-api-key" : config.get("demo_excamera", "x-api-key")
                 },
                 data=json.dumps({
                     'image': encoded_image
                 })
)
end_request = timeit.default_timer()    
#print 'request time,', end_request - start_request 
#print r.status_code
print r.text
