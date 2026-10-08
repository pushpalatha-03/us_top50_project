# United States Top 50 Playlist Performance & Song Popularity Trend Analysis
*Atlantic Recording Corporation – Research Paper*

## 1. Data & validation
27,800 daily rows, 2024-05-18 → 2025-11-27 (555 snapshots, 4 calendar days absent).
Checks: invalid ranks = 0; missing values = 0; duplicate song-day rows = 48
(collapsed to best rank); 1 day(s) with ≠50 rows. Songs are keyed on *title + artist string*
because titles repeat across artists. Dates are `dd-mm-yyyy`. Popularity = 0 appears on brand-new releases (API not yet populated).

## 2. Feature engineering
Days on chart, average rank, best rank, Rank Volatility Index (std of rank), Popularity Trend Score (7-day rolling mean),
duration (min), day-over-day rank change, entry flag, rank tier, Artist Dominance Index (share of total rank points, where points = 51 − rank).
Lead artist = first name in collaboration strings (protected-name list for e.g. "Tyler, The Creator").

## 3. Playlist dynamics
Average **3.5 entries and exits per day** – the chart turns over ~7% daily, so it is very stable.
Of day-over-day moves, 32% are unchanged and 4.9% are jumps larger than 10 places.
66% of songs chart fewer than 14 days, yet 35 songs stayed ≥180 days.
Fast risers (enter below #20, Top 10 within a week) mix seasonal songs (Halloween) with major releases:
FUK SUMN (Kanye West & Ty Dolla $ign), This Is Halloween (Various Artists), Monster Mash (Bobby "Boris" Pickett & The Crypt-Kickers).

## 4. Song-level performance
| song                                          | artist             |   days_on_chart |   avg_rank |   best_rank |   rank_volatility |
|:----------------------------------------------|:-------------------|----------------:|-----------:|------------:|------------------:|
| Something in the Orange                       | Zach Bryan         |             536 |      26.29 |           9 |              9.35 |
| Last Night                                    | Morgan Wallen      |             492 |      22.61 |           1 |             14.55 |
| I Remember Everything (feat. Kacey Musgraves) | Zach Bryan         |             446 |      13.90 |           1 |              9.89 |
| See You Again (feat. Kali Uchis)              | Tyler, The Creator |             444 |      29.38 |           4 |             11.81 |
| Stick Season                                  | Noah Kahan         |             414 |      18.29 |           1 |             11.36 |
| Cruel Summer                                  | Taylor Swift       |             388 |      16.92 |           1 |             13.63 |
| Lose Control                                  | Teddy Swims        |             329 |      23.50 |           5 |              8.65 |
| Thinkin’ Bout Me                              | Morgan Wallen      |             324 |      39.02 |          21 |              7.14 |

Peak rank vs longevity: Spearman ρ = -0.58 (better peak ↔ more days). Longevity, not only peak, separates catalog "evergreens" from spikes.

## 5. Artist performance
| artist             |   unique_songs |   days_present |   total_appearances |   avg_rank |   dominance_index |
|:-------------------|---------------:|---------------:|--------------------:|-----------:|------------------:|
| Taylor Swift       |             96 |            438 |                2015 |      24.55 |              7.53 |
| Zach Bryan         |             38 |            546 |                1882 |      25.66 |              6.74 |
| Morgan Wallen      |             10 |            540 |                1669 |      30.61 |              4.81 |
| Sabrina Carpenter  |             14 |            316 |                 967 |      17.61 |              4.56 |
| Chappell Roan      |              6 |            232 |                 794 |      20.65 |              3.41 |
| Billie Eilish      |             12 |            333 |                 729 |      20.36 |              3.16 |
| Drake              |             38 |            326 |                 881 |      26.28 |              3.08 |
| Travis Scott       |             32 |            338 |                 795 |      25.45 |              2.87 |
| Tyler, The Creator |             16 |            445 |                 706 |      25.29 |              2.56 |
| Olivia Rodrigo     |             19 |            283 |                 600 |      22.38 |              2.43 |

Top 5 artists hold **27.0%** and top 10 **41.1%** of all rank points across 244 artists.
Two dominance models appear: *breadth* (many songs – Taylor Swift, Zach Bryan, Drake) vs *depth* (few songs, high rank – Sabrina Carpenter, Chappell Roan, Billie Eilish).

## 6. Popularity analytics
Pearson r (rank vs popularity) = -0.094; Spearman ρ = -0.245 – a **weak-to-moderate** link.
Mean popularity: Top 10 = 89.6, 11-20 = 87.6, 21-50 = 87.0.
Popularity is high everywhere on the chart (≈87-90) so it separates tiers poorly; dispersion is largest in the Top 10 (std 13.5) partly because a few low/zero scores sit at high ranks (e.g. new releases whose API score has not populated).
Songs with volatile popularity also have volatile rank (ρ = 0.36).

## 7. Content attributes
| content      |   rows |   songs |   avg_rank |   avg_popularity |   top10_share |
|:-------------|-------:|--------:|-----------:|-----------------:|--------------:|
| Explicit     |  13305 |     523 |      25.39 |            87.30 |         20.54 |
| Non-explicit |  14447 |     466 |      25.60 |            87.99 |         19.50 |

| album_type   |   rows |   songs |   avg_rank |   avg_popularity |   top10_share |
|:-------------|-------:|--------:|-----------:|-----------------:|--------------:|
| album        |  19709 |     758 |      26.10 |            86.68 |         17.96 |
| compilation  |     42 |       9 |      33.19 |            78.38 |          7.14 |
| single       |   8001 |     243 |      23.99 |            90.13 |         25.08 |

| duration_band   |   rows |   songs |   avg_rank |   avg_popularity |   top10_share |
|:----------------|-------:|--------:|-----------:|-----------------:|--------------:|
| <2              |    756 |      41 |      31.55 |            85.27 |         10.58 |
| 2-2.5           |   2637 |      90 |      23.91 |            88.67 |         23.13 |
| 2.5-3           |   7203 |     195 |      26.01 |            87.79 |         22.56 |
| 3-3.5           |   6038 |     228 |      27.11 |            87.55 |         14.11 |
| 3.5-4           |   6352 |     206 |      24.68 |            88.30 |         20.25 |
| 4-5             |   4073 |     170 |      23.44 |            87.01 |         24.40 |
| 5+              |    693 |      48 |      25.34 |            83.87 |         14.86 |

| album_size   |   rows |   songs |   avg_rank |   avg_popularity |   top10_share |
|:-------------|-------:|--------:|-----------:|-----------------:|--------------:|
| 1 (single)   |   6233 |     191 |      24.12 |            90.30 |         26.38 |
| 2-5          |   1724 |      51 |      23.11 |            89.76 |         20.94 |
| 6-12         |   4025 |     155 |      24.05 |            88.03 |         26.14 |
| 13-20        |  11159 |     398 |      25.98 |            87.22 |         16.88 |
| 21-40        |   4592 |     219 |      28.30 |            84.02 |         13.26 |
| 40+          |     19 |       3 |      41.79 |            89.26 |          0.00 |

* **Explicit** content share is ~48% of slots; rank is essentially identical (25.4 vs 25.6) → explicit flag is not a success driver.
* **Singles** outperform album tracks: avg rank 24.0 vs 26.1; popularity 90.1 vs 86.7; Top-10 share 25% vs 18%.
* **Duration**: <2 min and 5+ min tracks under-perform; 2-3 min and 4-5 min have the highest Top-10 share (no linear relationship).
* **Album size**: tracks from larger projects (21+) rank worse and are less popular than singles/EPs.

## 8. Recommendations
1. Back **single-led campaigns**: singles carry higher popularity and Top-10 share.
2. Plan for **longevity** – better peak position goes with more days on chart; reserve budget to extend the run of songs that reach the Top 10 rather than only funding launch week.
3. For deluxe/large albums, **focus-track** 1-2 songs; wide tracklists dilute chart success.
4. Don't gate on explicit/clean or exact duration; keep tracks tight (2-4.5 min).
5. Use **seasonal windows** (Halloween, holidays) for catalog re-entries – they produce the fastest rises.
6. Track **volatility** (std of rank) relative to song age: it rises with time on chart (ρ = 0.55), so compare songs of similar age, not raw values.

## 9. Limitations
Historical, descriptive only (no causal claims); one market; popularity is a platform-derived score;
lead-artist parsing is heuristic; 4 missing calendar days affect day-over-day metrics.
