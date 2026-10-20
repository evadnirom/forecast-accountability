#!/usr/bin/env python3
"""Import independent METAR temperature observations near 2 p.m. Eastern.
Source: Iowa Environmental Mesonet ASOS archive; station HVN (Tweed-New Haven).
No interpolation, invented observations, or ERA5 model-as-measurement substitution.
"""
import csv,datetime as dt,io,pathlib,urllib.parse,urllib.request
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"data"/"observations.csv"
TZ=ZoneInfo("America/New_York")
STATION="HVN"
URL="https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

def run():
    today=dt.datetime.now(TZ).date()
    # Archive only completed days. Each run revisits the past 10 days to cover late reports.
    start=today-dt.timedelta(days=10)
    params={"station":STATION,"data":"tmpf","year1":start.year,"month1":start.month,
        "day1":start.day,"year2":today.year,"month2":today.month,"day2":today.day,
        "tz":"Etc/UTC","format":"onlycomma","missing":"empty","report_type":"3,4"}
    url=URL+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"ForecastAccountability/0.4"})
    with urllib.request.urlopen(req,timeout=60) as response:
        raw=response.read().decode("utf-8")
    rows=csv.DictReader(io.StringIO(raw))
    candidate={}
    for row in rows:
        if row.get("station","").upper()!=STATION:continue
        try:
            stamp=dt.datetime.strptime(row["valid"].strip(),"%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).astimezone(TZ)
            temp=float(row["tmpf"])
        except (KeyError,ValueError,TypeError):continue
        if stamp.date()>=today:continue
        target=stamp.replace(hour=14,minute=0,second=0,microsecond=0)
        delta=abs((stamp-target).total_seconds())/60
        if delta>35:continue
        day=stamp.date().isoformat()
        if day not in candidate or delta<candidate[day][0]:
            candidate[day]=(delta,stamp,temp)
    records={}
    if OUT.exists():
        with OUT.open(newline="") as f:
            for item in csv.DictReader(f):
                if item.get("date") and item.get("station"):
                    records[(item["date"],item["station"])]=item
    for day,(delta,stamp,temp) in candidate.items():
        records[(day,"Tweed-New Haven Airport (HVN)")]={
            "date":day,"station":"Tweed-New Haven Airport (HVN)",
            "temperature_14_local_f":str(temp),"evidence_url":url,
            "observed_local_time":stamp.isoformat(timespec="minutes"),
            "minutes_from_14":str(int(delta)),
            "reference_type":"METAR observed near 14:00; airport station, not Hamden"}
    OUT.parent.mkdir(exist_ok=True)
    cols=["date","station","temperature_14_local_f","evidence_url",
          "observed_local_time","minutes_from_14","reference_type"]
    with OUT.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for key in sorted(records):w.writerow({col:records[key].get(col,"") for col in cols})
    print("Stored observation rows:",len(records),"new/updated:",len(candidate))
if __name__=="__main__":run()
