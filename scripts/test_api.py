import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/v2/problem'
with open('data/realtime/problem.json') as f:
    data = f.read().encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        print(f"Problem created: {res['problem_id']}")
        
        # Now reoptimize
        reopt_url = 'http://127.0.0.1:8000/v2/reoptimize'
        reopt_data = json.dumps({
            'problem_id': res['problem_id'],
            'command': 'increase W01 capacity by 20%'
        }).encode('utf-8')
        
        reopt_req = urllib.request.Request(reopt_url, data=reopt_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(reopt_req) as reopt_res:
            res2 = json.loads(reopt_res.read().decode())
            print(f"Reoptimize success. Status: {res2['optimization']['status']}, Validation: {res2['optimization']['validation_status']}")
except urllib.error.URLError as e:
    print(f'Error: {e}')
