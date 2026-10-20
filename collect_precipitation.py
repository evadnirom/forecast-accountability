#!/usr/bin/env python3
"""Collect cautious daily precipitation totals from hourly METAR reports at HVN.

Do NOT equate an absent p01i reading with zero rain. A complete daily score
requires >= 22 distinct local clock-hour buckets with valid p01i reports.
Only routine METAR reports are requested to avoid summing multiple specials.
IEM p01i is a preceding-hour accumulation and may not align perfectly with
local clock boundaries; results are marked provisional airport references.
"""
import csv,datetime as dt,io,pathlib,urllib.parse,urllib.request
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"data"/"precip_observations.csv"
LOCAL=ZoneInfo("America/New_York")

def main():
    today=dt.datetime.now(LOCAL).date()
    start=today-dt.timedelta(days=12)
    query={"station":"HVN","data":"p01i","year1":start.year,"month1":start.month,
           "day1":start.day,"year2":today.year,"month2":today.month,
           "day2":today.day,"tz":"Etc/UTC","format":"onlycomma",
           "missing":"empty","trace":"empty","report_type":"3"}
    url="https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={"User-Agent":"ForecastAccountability/0.6"})
    with urllib.request.urlopen(req,timeout=60) as response:
        incoming=csv.DictReader(io.StringIO(response.read().decode("utf-8")))
        hourly={}
        for r in incoming:
            if r.get("station","").upper()!="HVN":continue
            try:
                utc=dt.datetime.strptime(r["valid"].strip(),"%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
                local=utc.astimezone(LOCAL)
                value=float(r["p01i"])
            except (KeyError,ValueError,TypeError):continue
            if local.date()>=today or value<0:continue
            # Period ending timestamp near the top of the hour; deduplicate.
            day=local.date().isoformat()
            hour=local.hour
            key=(day,hour)
            diff=min(local.minute,60-local.minute)
            if key not in hourly or diff<hourly[key][0]:
                hourly[key]=(diff,value,local.isoformat(timespec="minutes"))
    existing={}
    if OUT.exists():
        with OUT.open(newline="") as file:
            for r in csv.DictReader(file):
                if r.get("date"):existing[r["date"]]=r
    dates=sorted({day for day,_ in hourly})
    for day in dates:
        vals=[item[1] for (d,h),item in hourly.items() if d==day]
        count=len(vals)
        if count<22:continue
        existing[day]={"date":day,"station":"Tweed-New Haven Airport (HVN)",
            "rain_total_in":str(round(sum(vals),3)),"observed_hour_count":str(count),
            "evidence_url":url,"coverage_note":"Provisional sum of unique hourly routine METAR p01i; missing hours excluded; min 22 required."}
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",newline="") as file:
        fields=["date","station","rain_total_in","observed_hour_count","evidence_url","coverage_note"]
        writer=csv.DictWriter(file,fieldnames=fields)
        writer.writeheader()
        for day in sorted(existing): writer.writerow({k:existing[day].get(k,"") for k in fields})
    print("Eligible daily rainfall records:",len(existing))

if __name__=="__main__": main()
