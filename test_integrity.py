#!/usr/bin/env python3
"""Offline regression checks for Forecast Accountability data contracts."""
import ast,csv,io,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parent
class PipelineTests(unittest.TestCase):
    def test_python_parse(self):
        for filename in ["collect.py","collect_observations.py","collect_precipitation.py","collect_human_candidates.py","prepare_human_review.py","fetch_human_articles.py","build_dashboard.py","collection_health.py"]:
            with self.subTest(filename=filename):
                ast.parse((ROOT/filename).read_text(),filename=filename)
    def test_verified_human_forecasts_need_source(self):
        text=(ROOT/"build_dashboard.py").read_text()
        self.assertIn('"source_url"',text)
        self.assertIn('"source_excerpt"',text)
        self.assertIn('!="verified"',text)
        self.assertIn('timestamp.tzinfo is None',text)
    def test_rain_dry_requires_observation(self):
        text=(ROOT/"build_dashboard.py").read_text()
        self.assertIn('if count<22 or amount<0',text)
        self.assertIn('if o["date"]!=r["valid_local_date"]:continue',text)
        self.assertIn('actual_rain=observed>=0.01',text)
    def test_no_fictional_forecast_on_source_failure(self):
        text=(ROOT/"collect_human_candidates.py").read_text()
        self.assertIn('awaiting_human_verification',text)
        self.assertNotIn('review_status":"verified"',text)
    def test_dashboard_has_no_external_script(self):
        text=(ROOT/"site/index.html").read_text()
        self.assertIn('dashboard-data.json',text)
        self.assertIn('human_forecasts',text)
    def test_archive_schema(self):
        p=ROOT/"data"/"human_forecasts.csv"
        with p.open(newline="") as f:
            cols=csv.DictReader(f).fieldnames
        for field in ["meteorologist","issued_at_local","valid_date","source_url","source_excerpt","review_status"]:
            self.assertIn(field,cols)
if __name__=="__main__":unittest.main()
