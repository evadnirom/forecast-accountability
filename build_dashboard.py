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
precip_observations=[]
precip_path=data/"precip_observations.csv"
if precip_path.exists():
    with precip_path.open(newline="") as f:
        for item in csv.DictReader(f):
            try:
                amount=float(item["rain_total_in"])
                count=int(item["observed_hour_count"])
                if count<22 or amount<0 or not item.get("evidence_url"):continue
            except (ValueError,TypeError,KeyError):continue
            precip_observations.append({**item,"rain_total_in":amount,"observed_hour_count":count})
rain_groups=defaultdict(list)
rain_event_groups=defaultdict(lambda:{"hits":0,"misses":0,"false_alarms":0,"correct_dry":0})
for r in forecasts:
    estimated=r.get("sum_hourly_precipitation_in")
    if not isinstance(estimated,(int,float)):continue
    for o in precip_observations:
        if o["date"]!=r["valid_local_date"]:continue
        key=(r["source"],r["lead_calendar_days"],o["station"])
        observed=o["rain_total_in"]
        rain_groups[key].append(abs(estimated-observed))
        actual_rain=observed>=0.01
        predicted_rain=estimated>=0.01
        label="hits" if predicted_rain and actual_rain else "false_alarms" if predicted_rain else "misses" if actual_rain else "correct_dry"
        rain_event_groups[key][label]+=1
rain_leaderboard=[
    {"source":source,"lead":lead,"station":station,
     "sample_count":len(errors),"rain_mae_in":round(statistics.mean(errors),3),
     **rain_event_groups[(source,lead,station)]}
    for (source,lead,station),errors in rain_groups.items()]
payload={"schema_version":2,"precip_observations":precip_observations,
    "rain_leaderboard":rain_leaderboard,"rain_scored_count":sum(len(v) for v in rain_groups.values()),"forecasts":forecasts,
    "observations":list(observations.values()),"leaderboard":leaderboard,
    "scored_count":sum(len(x) for x in groups.values())}
(site/"dashboard-data.json").write_text(json.dumps(payload,indent=2))
print("Forecasts:",len(forecasts),"Observations:",len(observations),"Scored:",payload["scored_count"])
