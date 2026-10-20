#!/usr/bin/env python3
"""Take a time-stamped 1 PM ET snapshot of public station forecast webpages.

This is a capture of a page *at collection time*, not a forecast
issued at collection time. Never invent individual forecast values.
Each source gets an explicit outcome even if the site blocks retrieval.
"""
import datetime as dt,hashlib,json,pathlib,re,urllib.request
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"data"/"webpage_snapshots.jsonl"
SITES={
"WTNH":"https://www.wtnh.com/weather/",
"WFSB":"https://www.wfsb.com/weather/forecast/",
"FOX61":"https://www.fox61.com/weather",
"NBC Connecticut":"https://www.nbcconnecticut.com/weather-news/"
}
class Reader(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg"):self.skip=max(0,self.skip-1)
    def handle_data(self,value):
        if not self.skip and value.strip():self.parts.append(value.strip())
def main():
    now=dt.datetime.now(dt.timezone.utc)
    local=now.astimezone(ZoneInfo("America/New_York"))
    scheduled=__import__("os").getenv("GITHUB_EVENT_NAME")=="schedule"
    batch=("13" if scheduled else "adhoc-"+now.strftime("%H%M%S"))
    rows=[]
    for name,url in SITES.items():
        row={"snapshot_key":local.date().isoformat()+"|"+name+"|"+batch,
             "source":name,"source_kind":"television_station_website",
             "url":url,"captured_at_utc":now.isoformat(),
             "capture_window":"1 PM ET scheduled window" if scheduled else "ad hoc test (not the 1 PM scheduled snapshot)",
             "published_at_utc":None,"meteorologist":None,
             "status":"unavailable","title":None,"text_excerpt":None,"content_sha256":None,
             "error":None,"verification":"page_capture_only_not_scored"}
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; ForecastAccountability/1.0; public research)"})
            with urllib.request.urlopen(request,timeout=25) as resp:
                raw=resp.read(400000)
                row["final_url"]=resp.geturl()
            p=Reader();p.feed(raw.decode("utf-8","replace"))
            content=re.sub(r"\s+"," "," ".join(p.parts)).strip()
            if len(content)<100:raise ValueError("No substantial readable HTML text")
            row["status"]="captured"
            row["text_excerpt"]=content[:2200]
            row["content_sha256"]=hashlib.sha256(raw).hexdigest()
            row["bytes_read"]=len(raw)
        except Exception as error:
            row["error"]=str(error)[:200]
        rows.append(row)
        print(name,row["status"],row["error"] or "")
    known=set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            try:known.add(json.loads(line)["snapshot_key"])
            except (ValueError,KeyError):pass
    with OUT.open("a") as f:
        for row in rows:
            if row["snapshot_key"] not in known:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    print("Website capture attempts:",len(rows))
if __name__=="__main__":main()
