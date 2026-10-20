#!/usr/bin/env python3
"""Fetch public article text for editorial review, never automatically verify forecasts.

Reads candidate links only, limits download size and text retained, and records
errors without failing independent forecast collection. Pages may block scraping.
"""
import csv,datetime as dt,html.parser,pathlib,re,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
SRC=ROOT/"data"/"human_candidates.csv"
OUT=ROOT/"data"/"human_article_reviews.csv"
FIELDS=["station","headline","published_at_utc","source_url","article_url","retrieved_at_utc","excerpts","status","error"]
class Extract(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.skip=0;self.bits=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav","footer"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","nav","footer"):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.bits.append(data.strip())
def main():
    existing={}
    if OUT.exists():
        with OUT.open(newline="") as f:
            for row in csv.DictReader(f):
                if row.get("source_url"):existing[row["source_url"]]=row
    if SRC.exists():
        with SRC.open(newline="") as f:
            items=list(csv.DictReader(f))
        for item in items[:25]:
            link=item.get("source_url","")
            if not link or link in existing:continue
            fields={"station":item.get("station",""),"headline":item.get("headline",""),
                "published_at_utc":item.get("published_at_utc",""),"source_url":link,
                "article_url":"","retrieved_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
                "excerpts":"","status":"needs_review","error":""}
            try:
                parsed=urllib.parse.urlparse(link)
                if parsed.scheme!="https" or parsed.hostname not in ("news.google.com","www.google.com","google.com","wtnh.com","www.wtnh.com","wfsb.com","www.wfsb.com","fox61.com","www.fox61.com","nbcconnecticut.com","www.nbcconnecticut.com"):
                    raise ValueError("source URL outside approved news hosts")
                req=urllib.request.Request(link,headers={"User-Agent":"Mozilla/5.0 (compatible; ForecastAccountabilityResearch/1.0)"})
                with urllib.request.urlopen(req,timeout=15) as response:
                    final=response.geturl()
                    target=urllib.parse.urlparse(final)
                    if target.scheme!="https" or target.hostname not in ("news.google.com","www.google.com","google.com","wtnh.com","www.wtnh.com","wfsb.com","www.wfsb.com","fox61.com","www.fox61.com","nbcconnecticut.com","www.nbcconnecticut.com"):raise ValueError("redirect outside approved hosts")
                    raw=response.read(250000).decode("utf-8","replace")
                p=Extract();p.feed(raw)
                text=re.sub(r"\s+"," "," ".join(p.bits))
                # Keep only small excerpts with potential forecast content; never assign a numeric claim automatically.
                chunks=[]
                for match in re.finditer(r"\b(forecast|snow|rain|showers|degrees|highs|lows|chance|tomorrow|weekend)\b",text,re.I):
                    excerpt=text[max(0,match.start()-65):match.end()+110].strip()
                    if excerpt not in chunks: chunks.append(excerpt)
                    if len(chunks)>=5:break
                fields["article_url"]=final;fields["excerpts"]=" || ".join(chunks)[:950]
            except Exception as error:
                fields["error"]=str(error)[:180]
            existing[link]=fields
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for row in sorted(existing.values(),key=lambda r:r["published_at_utc"],reverse=True)[:300]:
            writer.writerow({k:row.get(k,"") for k in FIELDS})
    print("Article-review records:",len(existing))
if __name__=="__main__":main()
