"""Batch EDA: exports analysis tables to outputs/ and writes the research paper + executive summary
(numbers are computed, so documents never drift from the data).  Usage: python run_eda.py"""
import os
import pandas as pd
from src.data_pipeline import load_all, song_features, artist_features
from src import analytics as an

OUT = "outputs"; os.makedirs(OUT, exist_ok=True)
df, rep = load_all("data/Atlantic_United_States.csv")
sf, af = song_features(df), artist_features(df)

# ---------- export tables
sf.to_csv(f"{OUT}/song_features.csv", index=False)
af.to_csv(f"{OUT}/artist_features.csv", index=False)
rep.as_frame().to_csv(f"{OUT}/validation_report.csv", index=False)
tables = {"explicit": an.explicit_perf(df), "album_type": an.album_type_perf(df),
          "duration": an.duration_perf(df), "album_size": an.album_size_perf(df),
          "tier_popularity": an.pop_by_tier(df), "movement": an.rank_movement_distribution(df)}
for k, v in tables.items(): v.round(3).to_csv(f"{OUT}/{k}.csv", index=False)

# ---------- key numbers
cr = an.pop_rank_corr(df); pl = an.peak_vs_longevity(sf)
_, vol = an.pop_stability_vs_volatility(sf)
ee = an.entry_exit(df); mv = tables["movement"].set_index("movement")["count"]
one_wk = (sf.days_on_chart < 14).mean() * 100
long_ = (sf.days_on_chart >= 180).sum()
top5_share = af.head(5)["dominance_index"].sum()
top10_share = af.head(10)["dominance_index"].sum()
ex = tables["explicit"].set_index("content"); at = tables["album_type"].set_index("album_type")
tier = tables["tier_popularity"].set_index("tier")
daily_ent = ee["entries"].mean()
fr = an.fast_risers(df, top=3)
t = lambda d: d.to_markdown(index=False, floatfmt=".2f")
top_songs = sf.nlargest(8, "days_on_chart")[["song", "artist", "days_on_chart", "avg_rank", "best_rank", "rank_volatility"]]
top_art = af.head(10)[["artist", "unique_songs", "days_present", "total_appearances", "avg_rank", "dominance_index"]]

paper = f"""# United States Top 50 Playlist Performance & Song Popularity Trend Analysis
*Atlantic Recording Corporation – Research Paper*

## 1. Data & validation
{rep.rows_raw:,} daily rows, {rep.date_min} → {rep.date_max} ({rep.n_days} snapshots, {rep.missing_dates} calendar days absent).
Checks: invalid ranks = {rep.invalid_rank_rows}; missing values = {rep.missing_values}; duplicate song-day rows = {rep.duplicate_song_date}
(collapsed to best rank); {rep.days_not_50} day(s) with ≠50 rows. Songs are keyed on *title + artist string*
because titles repeat across artists. Dates are `dd-mm-yyyy`. Popularity = 0 appears on brand-new releases (API not yet populated).

## 2. Feature engineering
Days on chart, average rank, best rank, Rank Volatility Index (std of rank), Popularity Trend Score (7-day rolling mean),
duration (min), day-over-day rank change, entry flag, rank tier, Artist Dominance Index (share of total rank points, where points = 51 − rank).
Lead artist = first name in collaboration strings (protected-name list for e.g. "Tyler, The Creator").

## 3. Playlist dynamics
Average **{daily_ent:.1f} entries and exits per day** – the chart turns over ~{daily_ent/50*100:.0f}% daily, so it is very stable.
Of day-over-day moves, {mv['No change']/mv.sum()*100:.0f}% are unchanged and {(mv['Fell >10']+mv['Rose >10'])/mv.sum()*100:.1f}% are jumps larger than 10 places.
{one_wk:.0f}% of songs chart fewer than 14 days, yet {long_} songs stayed ≥180 days.
Fast risers (enter below #20, Top 10 within a week) mix seasonal songs (Halloween) with major releases:
{', '.join(fr['song'] + ' (' + fr['artist'] + ')')}.

## 4. Song-level performance
{t(top_songs)}

Peak rank vs longevity: Spearman ρ = {pl.statistic:.2f} (better peak ↔ more days). Longevity, not only peak, separates catalog "evergreens" from spikes.

## 5. Artist performance
{t(top_art)}

Top 5 artists hold **{top5_share:.1f}%** and top 10 **{top10_share:.1f}%** of all rank points across {af.shape[0]} artists.
Two dominance models appear: *breadth* (many songs – Taylor Swift, Zach Bryan, Drake) vs *depth* (few songs, high rank – Sabrina Carpenter, Chappell Roan, Billie Eilish).

## 6. Popularity analytics
Pearson r (rank vs popularity) = {cr['pearson_r']:.3f}; Spearman ρ = {cr['spearman_rho']:.3f} – a **weak-to-moderate** link.
Mean popularity: Top 10 = {tier.loc['Top 10','mean']:.1f}, 11-20 = {tier.loc['Top 11-20','mean']:.1f}, 21-50 = {tier.loc['Top 21-50','mean']:.1f}.
Popularity is high everywhere on the chart (≈87-90) so it separates tiers poorly; dispersion is largest in the Top 10 (std {tier.loc['Top 10','std']:.1f}) partly because a few low/zero scores sit at high ranks (e.g. new releases whose API score has not populated).
Songs with volatile popularity also have volatile rank (ρ = {vol.statistic:.2f}).

## 7. Content attributes
{t(tables['explicit'])}

{t(tables['album_type'])}

{t(tables['duration'])}

{t(tables['album_size'])}

* **Explicit** content share is ~{df['is_explicit'].mean()*100:.0f}% of slots; rank is essentially identical ({ex.loc['Explicit','avg_rank']:.1f} vs {ex.loc['Non-explicit','avg_rank']:.1f}) → explicit flag is not a success driver.
* **Singles** outperform album tracks: avg rank {at.loc['single','avg_rank']:.1f} vs {at.loc['album','avg_rank']:.1f}; popularity {at.loc['single','avg_popularity']:.1f} vs {at.loc['album','avg_popularity']:.1f}; Top-10 share {at.loc['single','top10_share']:.0f}% vs {at.loc['album','top10_share']:.0f}%.
* **Duration**: <2 min and 5+ min tracks under-perform; 2-3 min and 4-5 min have the highest Top-10 share (no linear relationship).
* **Album size**: tracks from larger projects (21+) rank worse and are less popular than singles/EPs.

## 8. Recommendations
1. Back **single-led campaigns**: singles carry higher popularity and Top-10 share.
2. Plan for **longevity** – better peak position goes with more days on chart; reserve budget to extend the run of songs that reach the Top 10 rather than only funding launch week.
3. For deluxe/large albums, **focus-track** 1-2 songs; wide tracklists dilute chart success.
4. Don't gate on explicit/clean or exact duration; keep tracks tight (2-4.5 min).
5. Use **seasonal windows** (Halloween, holidays) for catalog re-entries – they produce the fastest rises.
6. Track **volatility** (std of rank) relative to song age: it rises with time on chart (ρ = {an.stats.spearmanr(sf.rank_volatility, sf.days_on_chart).statistic:.2f}), so compare songs of similar age, not raw values.

## 9. Limitations
Historical, descriptive only (no causal claims); one market; popularity is a platform-derived score;
lead-artist parsing is heuristic; {rep.missing_dates} missing calendar days affect day-over-day metrics.
"""
open(f"{OUT}/research_paper.md", "w", encoding="utf-8").write(paper)

summary = f"""# Executive Summary – US Top 50 Playlist Analysis
**Scope:** {rep.n_days} daily snapshots ({rep.date_min} → {rep.date_max}), {sf.shape[0]} unique songs, {af.shape[0]} artists.

**Headlines**
- **Stable chart:** only ~{daily_ent:.1f} of 50 slots change per day; {one_wk:.0f}% of songs last <14 days, but {long_} songs held ≥180 days.
- **Concentrated market:** the top 5 artists capture {top5_share:.1f}% of all chart "points".
- **Singles win:** avg rank {at.loc['single','avg_rank']:.1f} vs {at.loc['album','avg_rank']:.1f} for album tracks; Top-10 share {at.loc['single','top10_share']:.0f}% vs {at.loc['album','top10_share']:.0f}%.
- **Explicit content is neutral:** {df['is_explicit'].mean()*100:.0f}% of slots; same average rank as clean tracks.
- **Popularity ≠ rank:** correlation is only ρ = {cr['spearman_rho']:.2f}; use longevity & volatility alongside it.

**Actions:** prioritise single-led releases, fund sustained promotion (not just launch week), focus-track large albums, and use seasonal windows for catalog re-entry.
"""
open(f"{OUT}/executive_summary.md", "w", encoding="utf-8").write(summary)
print(paper[:600]); print("\nWrote:", sorted(os.listdir(OUT)))
