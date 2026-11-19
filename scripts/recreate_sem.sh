cd /tmp/claude-0/kv
python3 -c '
from mk import *
ids=json.load(open("ids.json"))
if "semguard" in ids: call("DELETE","plugins/"+ids.pop("semguard"))
json.dump(ids,open("ids.json","w"),indent=1)'
python3 semguard.py aws-0-eu-west-1.pooler.supabase.com
