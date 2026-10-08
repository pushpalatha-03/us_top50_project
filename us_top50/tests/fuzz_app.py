"""Stress test: random + extreme filter combos against the real Streamlit app."""
import random, datetime as dt, sys, warnings
warnings.filterwarnings("ignore")
from streamlit.testing.v1 import AppTest
import pandas as pd
sys.path.insert(0, ".")
from src.data_pipeline import load_all
df, _ = load_all("data/Atlantic_United_States.csv")
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
dates = sorted(df.date.dt.date.unique()); artists = sorted(df.lead_artist.unique())
types = sorted(df.album_type.unique())
fails = {}
def case(label, fn):
    at = AppTest.from_file("../app.py", default_timeout=180).run()
    try:
        fn(at); at.run()
    except Exception as e:
        fails.setdefault("HARNESS " + str(e)[:80], []).append(label); return
    for e in at.exception:
        key = e.value.split("\n")[0][:110]
        fails.setdefault(key, []).append(label)
cases = []
for r in [(1,1),(50,50),(1,2),(25,26),(49,50)]:
    cases.append((f"rank{r}", lambda at, r=r: at.sidebar.slider[0].set_value(r)))
for t in types:
    cases.append((f"type={t}", lambda at, t=t: at.sidebar.multiselect[0].set_value([t])))
cases.append(("no album types", lambda at: at.sidebar.multiselect[0].set_value([])))
for c in ["Explicit only", "Non-explicit only"]:
    cases.append((c, lambda at, c=c: at.sidebar.radio[0].set_value(c)))
for d in [dates[0], dates[-1], dates[100]]:
    cases.append((f"oneday {d}", lambda at, d=d: at.sidebar.date_input[0].set_value((d, d))))
    cases.append((f"2days {d}", lambda at, d=d: at.sidebar.date_input[0].set_value((d, d + dt.timedelta(days=1)))))
cases.append(("date single value", lambda at: at.sidebar.date_input[0].set_value((dates[5],))))
for _ in range(N):
    def f(at):
        d0 = random.choice(dates); d1 = random.choice([x for x in dates if x >= d0])
        at.sidebar.date_input[0].set_value((d0, d1))
        a = random.randint(1, 50); b = random.randint(a, 50); at.sidebar.slider[0].set_value((a, b))
        at.sidebar.multiselect[0].set_value(random.sample(types, random.randint(1, 3)))
        at.sidebar.radio[0].set_value(random.choice(["All", "Explicit only", "Non-explicit only"]))
        if random.random() < .6: at.sidebar.multiselect[1].set_value(random.sample(artists, random.randint(1, 2)))
    cases.append((f"random{_}", f))

songs = sorted(df.song_id.unique())
# every kind of single-song / single-row selection
for _ in range(25):
    def g(at):
        sid = random.choice(songs); a = sid.split(" \u2014 ")[-1]
        row = df[df.song_id == sid].sample(1).iloc[0]
        at.sidebar.multiselect[1].set_value([row.lead_artist]); at.run()
        at.sidebar.multiselect[2].set_value([sid]);
        if random.random() < .5:
            d = row.date.date(); at.sidebar.date_input[0].set_value((d, d))
        if random.random() < .5:
            at.sidebar.slider[0].set_value((int(row.position), int(row.position)))
    cases.append((f"song{_}", g))
# in-tab widgets
cases.append(("topN=5", lambda at: at.slider[1].set_value(5)))
cases.append(("topN=30", lambda at: at.slider[1].set_value(30)))
def empty_plot(at):
    at.tabs[1].multiselect[0].set_value([])
cases.append(("plot none", empty_plot))

for label, fn in cases: case(label, fn)
print(f"{len(cases)} cases, {sum(len(v) for v in fails.values())} failures")
for k, v in fails.items(): print(" *", k, "| e.g.", v[:3], f"({len(v)})")
