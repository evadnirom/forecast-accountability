#!/usr/bin/env python3
"""Build transparent status report for each independent data pipeline."""
import csv,datetime as dt,json,pathlib
root=pathlib.Path(__file__).resolve().parent
data=root/"data";out=root/"site";out.mkdir(exist_ok=True)
checks={"model_forecasts":("snapshots-*.jsonl","jsonl"),
"airport_temperature":("observations.csv","csv"),
"airport_rainfall":("precip_observations.csv","csv"),
"tv_website_snapshots":("webpage_snapshots.jsonl","jsonl"),
"tv_article_discovery":("human_candidates.csv","csv"),
"tv_review_hints":("human_review_queue.csv","csv"),
"tv_article_excerpts":("human_article_reviews.csv","csv"),
"verified_human_forecasts":("human_forecasts.csv","csv")}
result={}
for name,(glob,kind) in checks.items():
    files=sorted(data.glob(glob));count=0;newest=None
    for file in files:
        if kind=="jsonl":count+=sum(bool(line.strip()) for line in file.read_text().splitlines())
        else:
            with file.open(newline="") as f:count+=sum(1 for _ in csv.DictReader(f))
        timestamp=dt.datetime.fromtimestamp(file.stat().st_mtime,dt.timezone.utc)
        newest=max(newest,timestamp) if newest else timestamp
    result[name]={"status":"not_generated" if not files else "empty" if count==0 else "populated",
                  "records":count,"last_file_modified_utc":newest.isoformat() if newest else None}
report={"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"pipelines":result,
        "notes":"Counts prove files exist, not that external sources were fully accessed. No human forecasts are verified automatically."}
(out/"collection-health.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if result["model_forecasts"]["records"]==0:raise SystemExit("No forecast records: core archive empty")
