"""Layer 2 - Analytical functions (pure: DataFrame in, DataFrame out)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats

def safe_corr(x, y, method="spearman"):
    """Correlation that returns None (not an exception/warning) when it is undefined."""
    x, y = pd.Series(x).reset_index(drop=True), pd.Series(y).reset_index(drop=True)
    ok = x.notna() & y.notna()
    x, y = x[ok], y[ok]
    if len(x) < 3 or x.nunique() < 2 or y.nunique() < 2:
        return None
    return stats.spearmanr(x, y) if method == "spearman" else stats.pearsonr(x, y)

# ---------- Playlist ranking analysis
def daily_summary(df):
    return df.groupby("date").agg(
        avg_popularity=("popularity", "mean"), explicit_share=("is_explicit", "mean"),
        new_entries=("is_entry", "sum"), unique_artists=("lead_artist", "nunique")).reset_index()

def rank_movement_distribution(df):
    m = df.dropna(subset=["rank_change"])["rank_change"]
    labels = ["Fell >10", "Fell 4-10", "Fell 1-3", "No change", "Rose 1-3", "Rose 4-10", "Rose >10"]
    cat = pd.Series(np.select(
        [m < -10, m < -3, m < 0, m == 0, m <= 3, m <= 10], labels[:6], default=labels[6]), index=m.index)
    return cat.value_counts().reindex(labels).rename_axis("movement").reset_index(name="count")

def entry_exit(df):
    """Daily entries (new/re-entry) vs exits (present yesterday, absent today)."""
    days = sorted(df["date"].unique()); sets = df.groupby("date")["song_id"].agg(set)
    rows = [(c, len(sets[c] - sets[p]), len(sets[p] - sets[c]))
            for p, c in zip(days[:-1], days[1:]) if (c - p).days == 1]
    return pd.DataFrame(rows, columns=["date", "entries", "exits"])

def entry_position_profile(df):
    return df[df["is_entry"]].groupby("position").size().rename("entries").reset_index()

def exit_position_profile(df):
    """Last-seen rank before dropping off (song absent next day)."""
    last = df.sort_values("date").groupby("song_id").tail(1)
    return last.groupby("position").size().rename("exits").reset_index()

def risers_decliners(df, min_days=7, top=15):
    """Linear slope of position over time; negative = climbing."""
    rows = []
    for sid, g in df.groupby("song_id"):
        if len(g) < min_days: continue
        x = (g["date"] - g["date"].min()).dt.days.values
        slope = np.polyfit(x, g["position"].values, 1)[0]
        rows.append((sid, g["song"].iloc[0], g["artist"].iloc[0], len(g),
                     g["position"].iloc[0], g["position"].min(), g["position"].iloc[-1], slope))
    r = pd.DataFrame(rows, columns=["song_id", "song", "artist", "days", "entry_rank",
                                    "best_rank", "last_rank", "slope_per_day"])
    if r.empty:
        return r, r
    r["slope_per_day"] = r["slope_per_day"].astype(float)
    return r.nsmallest(top, "slope_per_day"), r.nlargest(top, "slope_per_day")

def fast_risers(df, within=7, top=15):
    """Enter outside Top 20, reach Top 10 within `within` days."""
    s = df.sort_values("date")
    first = s.groupby("song_id").first()[["song", "artist", "position"]]
    best = s.groupby("song_id").head(within).groupby("song_id")["position"].min()
    out = first.join(best.rename("best_in_window"))
    out = out[(out["position"] > 20) & (out["best_in_window"] <= 10)]
    out["jump"] = out["position"] - out["best_in_window"]
    return out.sort_values("jump", ascending=False).head(top).reset_index()

# ---------- Song level
def peak_vs_longevity(sf):
    return safe_corr(sf["best_rank"], sf["days_on_chart"])

# ---------- Popularity analytics
def pop_rank_corr(df):
    nan = float("nan")
    p, s = safe_corr(df["position"], df["popularity"], "pearson"), safe_corr(df["position"], df["popularity"])
    return {"pearson_r": p[0] if p else nan, "pearson_p": p[1] if p else nan,
            "spearman_rho": s[0] if s else nan, "spearman_p": s[1] if s else nan}

def pop_by_tier(df):
    t = df.groupby("tier", observed=True)["popularity"].agg(["count", "mean", "median", "std", "min"])
    return t.reset_index()

def pop_stability_vs_volatility(sf, min_days=14):
    s = sf[sf["days_on_chart"] >= min_days]
    return s, safe_corr(s["pop_volatility"], s["rank_volatility"])

# ---------- Content attributes
def _perf(df, col):
    return df.groupby(col, observed=True).agg(
        rows=("position", "size"), songs=("song_id", "nunique"),
        avg_rank=("position", "mean"), avg_popularity=("popularity", "mean"),
        top10_share=("position", lambda s: (s <= 10).mean() * 100)).reset_index()

def explicit_perf(df):
    return _perf(df.assign(content=np.where(df["is_explicit"], "Explicit", "Non-explicit")), "content")

def album_type_perf(df): return _perf(df, "album_type")

def duration_perf(df):
    d = df.assign(duration_band=pd.cut(df["duration_min"], [0, 2, 2.5, 3, 3.5, 4, 5, 15],
                  labels=["<2", "2-2.5", "2.5-3", "3-3.5", "3.5-4", "4-5", "5+"]))
    return _perf(d, "duration_band")

def album_size_perf(df):
    d = df.assign(album_size=pd.cut(df["total_tracks"], [0, 1, 5, 12, 20, 40, 200],
                  labels=["1 (single)", "2-5", "6-12", "13-20", "21-40", "40+"]))
    return _perf(d, "album_size")

def content_correlations(df):
    cols = ["position", "popularity", "duration_min", "total_tracks"]
    if len(df) < 3:
        return pd.DataFrame()
    d = df[cols]
    d = d.loc[:, d.nunique() > 1]          # drop constant columns (correlation undefined)
    return d.corr(method="spearman") if d.shape[1] >= 2 else pd.DataFrame()

def explicit_share_trend(df, freq="MS"):
    return df.set_index("date")["is_explicit"].resample(freq).mean().mul(100).rename("explicit_share").reset_index()
