"""Layer 1 - Data ingestion, validation, cleaning and feature engineering."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

# Artists whose names contain ", " or " & " and must not be split
PROTECTED = ["Tyler, The Creator", "Tyler, the Creator", "Earth, Wind & Fire",
             "Florence + The Machine", "Brooks & Dunn", "Hall & Oates"]
_SPLIT = re.compile(r"\s*(?:,|&|\bfeat\.?|\bft\.?|\bx\b|\bwith\b)\s*", re.I)


@dataclass
class ValidationReport:
    rows_raw: int = 0
    rows_clean: int = 0
    date_min: str = ""
    date_max: str = ""
    n_days: int = 0
    missing_dates: int = 0
    invalid_rank_rows: int = 0
    missing_values: int = 0
    duplicate_song_date: int = 0
    duplicate_rank_date: int = 0
    days_not_50: int = 0

    def as_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"check": list(self.__dict__.keys()), "value": list(self.__dict__.values())})


def standardize_text(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip()


def lead_artist(name: str) -> str:
    for p in PROTECTED:
        if name.startswith(p):
            return p
    return _SPLIT.split(name, maxsplit=1)[0].strip()


REQUIRED = ["date", "position", "song", "artist", "popularity", "duration_ms",
            "album_type", "total_tracks", "is_explicit"]


def _read_csv(path: str) -> pd.DataFrame:
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):      # Windows-safe encodings
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as e:
            last = e
    raise last


def load_and_validate(path: str) -> tuple[pd.DataFrame, ValidationReport]:
    raw = _read_csv(path)
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {missing}. Found: {list(raw.columns)}")
    if "album_cover_url" not in raw.columns:
        raw["album_cover_url"] = ""
    rep = ValidationReport(rows_raw=len(raw))
    df = raw.copy()

    d = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    if d.isna().mean() > 0.5:                                    # different date format -> flexible parse
        d = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["date"] = d
    for c in ["position", "popularity", "duration_ms", "total_tracks"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["is_explicit"] = df["is_explicit"].astype(str).str.lower().eq("true")
    rep.missing_values = int(df.drop(columns=["album_cover_url"]).isna().sum().sum())
    df = df.dropna(subset=["date", "position", "song", "artist", "popularity", "duration_ms", "total_tracks"])
    df = df.astype({"position": int, "popularity": int, "duration_ms": int, "total_tracks": int})
    if df.empty:
        raise ValueError("No valid rows left after cleaning - check the date format and column values.")

    bad = ~df["position"].between(1, 50)                      # rank range 1-50
    rep.invalid_rank_rows = int(bad.sum())
    df = df[~bad]

    df["song"] = df["song"].map(standardize_text)
    df["artist"] = df["artist"].map(standardize_text)
    df["lead_artist"] = df["artist"].map(lead_artist)
    df["song_id"] = df["song"] + " \u2014 " + df["artist"]    # disambiguates same-titled songs

    rep.duplicate_song_date = int(df.duplicated(["date", "song_id"]).sum())
    df = df.sort_values(["date", "position"]).drop_duplicates(["date", "song_id"], keep="first")
    rep.duplicate_rank_date = int(df.duplicated(["date", "position"]).sum())

    full = pd.date_range(df["date"].min(), df["date"].max())
    rep.missing_dates = len(full.difference(df["date"].unique()))
    rep.n_days = df["date"].nunique()
    rep.days_not_50 = int((df.groupby("date").size() != 50).sum())
    rep.date_min, rep.date_max = str(df["date"].min().date()), str(df["date"].max().date())
    rep.rows_clean = len(df)
    return df.reset_index(drop=True), rep


def add_features(df: pd.DataFrame, trend_window: int = 7) -> pd.DataFrame:
    """Row-level derived metrics."""
    df = df.sort_values(["song_id", "date"]).copy()
    df["duration_min"] = df["duration_ms"] / 60000
    g = df.groupby("song_id")
    df["pop_trend"] = g["popularity"].transform(lambda s: s.rolling(trend_window, min_periods=1).mean())
    gap = g["date"].diff().dt.days
    df["prev_position"] = g["position"].shift(1).where(gap == 1)
    df["rank_change"] = df["prev_position"] - df["position"]      # + = climbed
    df["is_entry"] = gap.ne(1)                                     # first appearance or re-entry
    df["tier"] = pd.cut(df["position"], [0, 10, 20, 50], labels=["Top 10", "Top 11-20", "Top 21-50"])
    return df.sort_values(["date", "position"]).reset_index(drop=True)


def song_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby("song_id").agg(
        song=("song", "first"), artist=("artist", "first"), lead_artist=("lead_artist", "first"),
        days_on_chart=("date", "nunique"),
        avg_rank=("position", "mean"), best_rank=("position", "min"),
        rank_volatility=("position", "std"),
        avg_popularity=("popularity", "mean"), pop_volatility=("popularity", "std"),
        first_date=("date", "min"), last_date=("date", "max"),
        duration_min=("duration_min", "first"), album_type=("album_type", "first"),
        total_tracks=("total_tracks", "first"), is_explicit=("is_explicit", "first"),
    ).reset_index()
    out[["rank_volatility", "pop_volatility"]] = out[["rank_volatility", "pop_volatility"]].fillna(0)
    out["span_days"] = (out["last_date"] - out["first_date"]).dt.days + 1
    return out


def artist_features(df: pd.DataFrame, by: str = "lead_artist") -> pd.DataFrame:
    """Artist Dominance Index = % share of total rank points (51 - position)."""
    d = df.assign(points=51 - df["position"])
    total = d["points"].sum()
    a = d.groupby(by).agg(
        unique_songs=("song_id", "nunique"), total_appearances=("date", "size"),
        days_present=("date", "nunique"), avg_rank=("position", "mean"),
        best_rank=("position", "min"), avg_popularity=("popularity", "mean"),
        points=("points", "sum"),
    ).reset_index().rename(columns={by: "artist"})
    a["dominance_index"] = a["points"] / total * 100
    return a.sort_values("dominance_index", ascending=False).reset_index(drop=True)


def load_all(path: str):
    df, rep = load_and_validate(path)
    return add_features(df), rep
