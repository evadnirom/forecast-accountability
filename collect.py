#!/usr/bin/env python3
"""Append daily, time-stamped Open-Meteo model snapshots; standard library only."""
import datetime as dt, json, os, pathlib, time, urllib.parse, urllib.request
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"data"
DATA.mkdir(exist_ok=True)
TZ="America/New_York"
LAT=float(os.getenv("FA_LAT","41.3959"))
LON=float(os.getenv("FA_LON","-72.8968"))
MODELS={"GFS":"gfs_seamless","ECMWF":"ecmwf_ifs025","ICON":"icon_seamless"}

def fetch(params):
    url="https://api.open-meteo.com/v1/forecast?"+urllib.parse.urlencode(params)
    request=urllib.request.Request(url,headers={"User-Agent":"ForecastAccountability/0.3 (educational)"})
    with urllib.request.urlopen(request,timeout=45) as response:
        return json.load(response),url

def main():
    now=dt.datetime.now(dt.timezone.utc)
    issued=now.astimezone(ZoneInfo(TZ)).date()
    path=DATA/f"snapshots-{issued.year}.jsonl"
    records=[]
    known=set()
    if path.exists():
        for line in path.read_text().splitlines():
            try: known.add(json.loads(line)["snapshot_key"])
            except (KeyError,ValueError): pass
    successes=0
    for name,model in MODELS.items():
        try:
            result,url=fetch({"latitude":LAT,"longitude":LON,"models":model,
                "hourly":"temperature_2m,precipitation_probability,precipitation",
                "forecast_days":8,"temperature_unit":"fahrenheit",
                "precipitation_unit":"inch","timezone":TZ})
            hours=result["hourly"]
            times=hours["time"]
            if not times: raise ValueError("empty forecast")
            successes+=1
            for lead in range(1,8):
                valid=(issued+dt.timedelta(days=lead)).isoformat()
                key=f"{issued}|{name}|{valid}"
                if key in known: continue
                ix=[i for i,t in enumerate(times) if t[:10]==valid]
                if not ix: continue
                def val(var,i):
                    arr=hours.get(var,[])
                    return arr[i] if i<len(arr) and isinstance(arr[i],(float,int)) else None
                temps=[val("temperature_2m",i) for i in ix]
                temps=[x for x in temps if x is not None]
                rain=[val("precipitation",i) for i in ix]
                rain=[x for x in rain if x is not None]
                probs=[val("precipitation_probability",i) for i in ix]
                probs=[x for x in probs if x is not None]
                two_pm=next((val("temperature_2m",i) for i in ix if times[i].endswith("T14:00")),None)
                records.append({"snapshot_key":key,"source_kind":"numerical_model",
                    "source":name,"model":model,"location":"Hamden, CT",
                    "latitude":LAT,"longitude":LON,"timezone":TZ,
                    "collected_at_utc":now.isoformat(),
                    "issued_local_date":issued.isoformat(),
                    "valid_local_date":valid,"lead_calendar_days":lead,
                    "temperature_14_local_f":two_pm,
                    "daily_hourly_max_f":max(temps) if temps else None,
                    "hourly_precip_probability_max_percent":max(probs) if probs else None,
                    "sum_hourly_precipitation_in":round(sum(rain),3) if rain else None,
                    "api_url":url,
                    "notes":"Fetch time is not model initialization time."})
            print(name,"fetched successfully")
        except Exception as error:
            print(name,"ERROR:",error,flush=True)
        time.sleep(0.3)
    if successes==0: raise SystemExit("No models fetched; archive not updated.")
    if records:
        with path.open("a") as f:
            for record in records: f.write(json.dumps(record,separators=(",",":"))+"\n")
    print("New snapshots:",len(records))

if __name__=="__main__": main()
