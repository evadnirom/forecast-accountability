#!/usr/bin/env python3
"""Build a public dashboard with genuine archived data and verified scoring only."""
import csv,json,pathlib,statistics
from collections import defaultdict
root=pathlib.Path(__file__).resolve().parent
data=root/"data"
site=root/"site"
site.mkdir(exist_ok=True)
forecasts=[]
for path in sorted(data.glob("snapshots-*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        try:
            r=json.loads(line)
            if r.get("source_kind")=="numerical_model" and r.get("valid_local_date"):
                forecasts.append(r)
        except ValueError: pass
observations={}
path=data/"observations.csv"
if path.exists():
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            if not all(r.get(k) for k in ("date","station","temperature_14_local_f","evidence_url")): continue
            try: v=float(r["temperature_14_local_f"])
            except (ValueError,TypeError): continue
            observations[(r["date"],r["station"])]={
                "date":r["date"],"station":r["station"],
                "temperature_14_local_f":v,"evidence_url":r["evidence_url"]}
groups=defaultdict(list)
for r in forecasts:
    for (date,station),o in observations.items():
        if date==r["valid_local_date"] and isinstance(r.get("temperature_14_local_f"),(int,float)):
            groups[(r["source"],r["lead_calendar_days"],station)].append(abs(r["temperature_14_local_f"]-o["temperature_14_local_f"]))
leaderboard=[{"source":src,"lead":lead,"station":station,"sample_count":len(errors),"mae_f":round(statistics.mean(errors),2)}
    for (src,lead,station),errors in groups.items()]
payload={"schema_version":1,"forecasts":forecasts,
    "observations":list(observations.values()),"leaderboard":leaderboard,
    "scored_count":sum(len(x) for x in groups.values())}
(site/"dashboard-data.json").write_text(json.dumps(payload,indent=2))
print("Forecasts:",len(forecasts),"Observations:",len(observations),"Scored:",payload["scored_count"])
