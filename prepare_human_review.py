#!/usr/bin/env python3
"""Extract *review hints* from article headlines, never publish them as forecasts.
Headline keywords cannot establish forecast amounts, dates, or attribution.
"""
import csv,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/"data"/"human_candidates.csv"
TARGET=ROOT/"data"/"human_review_queue.csv"
FIELDS=["station","headline","published_at_utc","source_url","weather_topics","possible_forecast","review_status","review_note"]
KEYWORDS={"snow":r"\b(snow|blizzard|flurries|sleet|ice|icy)\b",
"rain":r"\b(rain|showers|downpours|flood|thunderstorms?)\b",
"wind":r"\b(wind|gusts?|breezy)\b",
"temperature":r"\b(heat|cold|warm|temperatures?|degrees|chilly|freeze|frost)\b",
"severe":r"\b(warning|watch|severe|tornado|storm)\b"}
def main():
    existing={}
    if TARGET.exists():
        with TARGET.open(newline="") as f:
            for row in csv.DictReader(f):
                if row.get("source_url"): existing[row["source_url"]]=row
    if SOURCE.exists():
        with SOURCE.open(newline="") as f:
            for item in csv.DictReader(f):
                url=item.get("source_url","")
                if not url:continue
                title=item.get("headline","")
                topics=[label for label,regex in KEYWORDS.items() if re.search(regex,title,re.I)]
                if url not in existing:
                    existing[url]={"station":item.get("station",""),"headline":title,
                      "published_at_utc":item.get("published_at_utc",""),
                      "source_url":url,"weather_topics":";".join(topics),
                      "possible_forecast":"yes" if re.search(r"\b(forecast|expect|coming|ahead|likely|chance|next week|this weekend)\b",title,re.I) else "unknown",
                      "review_status":"unverified",
                      "review_note":"Headline hint only; open original publication and verify the author, issued time, target date, location and exact predicted values."}
    TARGET.parent.mkdir(exist_ok=True)
    with TARGET.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for row in sorted(existing.values(),key=lambda r:r["published_at_utc"],reverse=True)[:500]:
            w.writerow({k:row.get(k,"") for k in FIELDS})
    print("Review candidates:",len(existing))
if __name__=="__main__":main()
