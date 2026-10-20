#!/usr/bin/env python3
"""Discover possible CT television weather articles for human review.
Discovery is NOT an archived meteorologist prediction and earns no score.
Public Google News RSS search results may be incomplete; dedupe by link.
"""
import csv,datetime as dt,email.utils,pathlib,urllib.parse,urllib.request,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"data"/"human_candidates.csv"
SITES={"WTNH":"wtnh.com","WFSB":"wfsb.com","FOX61":"fox61.com","NBC Connecticut":"nbcconnecticut.com"}
HEADERS=["discovered_at_utc","station","headline","published_at_utc","source_url","status"]
def main():
    seen={}
    if OUT.exists():
        with OUT.open(newline="") as f:
            for r in csv.DictReader(f):
                if r.get("source_url"):seen[r["source_url"]]=r
    found=0
    now=dt.datetime.now(dt.timezone.utc)
    for station,domain in SITES.items():
        query=f"site:{domain} weather forecast when:3d"
        url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":query,"hl":"en-US","gl":"US","ceid":"US:en"})
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ForecastAccountability/0.8"})
            with urllib.request.urlopen(req,timeout=25) as resp:root=ET.fromstring(resp.read())
            for item in root.findall(".//item"):
                title=(item.findtext("title") or "").strip()
                link=(item.findtext("link") or "").strip()
                published=(item.findtext("pubDate") or "").strip()
                if not title or not link or link in seen:continue
                try:
                    stamp=email.utils.parsedate_to_datetime(published).astimezone(dt.timezone.utc)
                    if abs((now-stamp).total_seconds())>4*86400:continue
                except (ValueError,TypeError):continue
                seen[link]={"discovered_at_utc":now.isoformat(),"station":station,
                    "headline":title,"published_at_utc":stamp.isoformat(),
                    "source_url":link,"status":"awaiting_human_verification"}
                found+=1
        except Exception as exc:
            print(station,"feed unavailable:",str(exc)[:180])
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader()
        for row in sorted(seen.values(),key=lambda r:r["published_at_utc"],reverse=True)[:500]:
            writer.writerow({key:row.get(key,"") for key in HEADERS})
    print("New possible articles:",found,"total stored:",len(seen))
if __name__=="__main__":main()
