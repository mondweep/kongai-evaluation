from mk import *; import sys,time
from run_guard import run
from corpus import *
ids=json.load(open("ids.json"))
for th in [float(x) for x in sys.argv[1:]]:
    patch_plugin(ids["semguard"],{"search":{"threshold":th}}); time.sleep(20)
    out=run("/chat-semguard",{"direct":INJ_DIRECT,"paraphrased":INJ_PARAPHRASED,"benign":BENIGN})
    print("threshold",th,{k:f"{sum(1 for r in v if r[1]==400)}/{len(v)} blocked, statuses {sorted(set(r[1] for r in v))}" for k,v in out.items()})
    json.dump(out,open(f"res_sem_{th}.json","w"))
