"""Run every analytics function on many random tiny subsets; warnings are errors."""
import sys, warnings, random, traceback
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from src.data_pipeline import load_all, song_features, artist_features
from src import analytics as an
df, _ = load_all("data/Atlantic_United_States.csv")
warnings.simplefilter("error")
random.seed(3); np.random.seed(3)
def calls(d):
    sf, af = song_features(d), artist_features(d)
    an.daily_summary(d); an.rank_movement_distribution(d); an.entry_exit(d)
    an.entry_position_profile(d); an.exit_position_profile(d)
    an.risers_decliners(d); an.fast_risers(d); an.peak_vs_longevity(sf)
    an.pop_rank_corr(d); an.pop_by_tier(d); an.pop_stability_vs_volatility(sf)
    for f in (an.explicit_perf, an.album_type_perf, an.duration_perf, an.album_size_perf,
              an.content_correlations, an.explicit_share_trend): f(d)
subs = []
for n in [1, 2, 3, 5, 10]:
    for _ in range(25): subs.append((f"rows{n}", df.sample(n)))
for _ in range(25):
    sid = random.choice(df.song_id.unique()); subs.append(("onesong", df[df.song_id == sid]))
for _ in range(25):
    d = random.choice(df.date.unique()); subs.append(("oneday", df[df.date == d]))
for lo, hi in [(1,1),(50,50),(1,3),(48,50)]:
    subs.append((f"rank{lo}-{hi}", df[df.position.between(lo, hi)]))
subs.append(("all", df)); subs.append(("compilation", df[df.album_type == "compilation"]))
bad = {}
for label, d in subs:
    try: calls(d)
    except Exception as e:
        key = f"{type(e).__name__}: {str(e).splitlines()[0][:90]} @ {traceback.extract_tb(e.__traceback__)[-1].name}"
        bad.setdefault(key, []).append(label)
print(len(subs), "subsets;", len(bad), "distinct problems")
for k, v in bad.items(): print(" *", k, "|", sorted(set(v))[:4], len(v))
