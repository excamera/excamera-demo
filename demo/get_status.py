#!/usr/bin/env python
import ConfigParser
import base64
import requests
import json
import sys
import timeit
import datetime

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

config = ConfigParser.ConfigParser()
config.readfp(open('/home/jemmons/demo_excamera_auth.cfg'))
# print config.get('demo_excamera', 'x-api-key')

if len(sys.argv) != 2:
    print 'Usage: ' + sys.argv[0] + ' REQUEST_ID'
    sys.exit(1)


start_request = timeit.default_timer()    
r = requests.post('https://3n61exvxul.execute-api.us-east-1.amazonaws.com/prod/demo-excamera-getstatus',
                 headers={
                     "x-api-key" : config.get("demo_excamera", "x-api-key")
                 },
                 data=json.dumps({
                     'request_id': sys.argv[1]
                 })
)
end_request = timeit.default_timer()    
#print 'request time,', end_request - start_request 

#print r.status_code
response = eval(r.text)
if( 'error' not in response.keys() or response['error'] != 'None' ):
    print json.dumps(response, indent=4, sort_keys=True)
    print 'error:', response['error']

else:
    print json.dumps(response, indent=4, sort_keys=True)

    print 'current_stage:', response['stage']

    time_start = response['time_start']
    time_end = response['time_current_op']
    print 'execution_time:', datetime.datetime.strptime(time_end, DATETIME_FORMAT) -datetime.datetime.strptime(time_start, DATETIME_FORMAT)
