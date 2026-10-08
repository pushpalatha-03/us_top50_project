"""Layer 3 - Streamlit dashboard: US Top 50 Playlist Performance & Song Popularity Trends."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_pipeline import load_all, song_features, artist_features
from src import analytics as an

BASE_DIR = Path(__file__).resolve().parent            # folder that contains app.py
DATA_PATH = str(BASE_DIR / "data" / "Atlantic_United_States.csv")
st.set_page_config(page_title="US Top 50 Analytics", page_icon="🎵", layout="wide")


@st.cache_data(show_spinner="Loading & validating data...")
def get_data():
    df, rep = load_all(DATA_PATH)
    return df, rep


try:
    df_all, report = get_data()
except FileNotFoundError:
    data_dir = BASE_DIR / "data"
    found = sorted(p.name for p in data_dir.glob("*")) if data_dir.exists() else []
    st.error(f"Data file not found: `{DATA_PATH}`.\n\n"
             "Make sure `data/Atlantic_United_States.csv` is committed to the repository next to `app.py` "
             "(file names are case-sensitive on Linux servers). "
             f"Files found in the data folder: {found if found else 'the data folder does not exist'}.")
    st.stop()
except Exception as exc:
    st.error(f"Could not load the data: {exc}")
    st.stop()

# ------------------------------------------------------------------ sidebar filters
st.sidebar.title("🎛️ Filters")
dmin, dmax = df_all["date"].min().date(), df_all["date"].max().date()
ALBUMS = sorted(df_all["album_type"].unique())
DEFAULTS = {"f_date": (dmin, dmax), "f_rank": (1, 50), "f_album": ALBUMS, "f_content": "All",
            "f_artist": [], "f_song": []}
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


def reset_filters():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


st.sidebar.button("🔄 Reset all filters", on_click=reset_filters, width="stretch")
dr = st.sidebar.date_input("Date range", min_value=dmin, max_value=dmax, key="f_date")
d0, d1 = (dr if isinstance(dr, (tuple, list)) and len(dr) == 2 else (dmin, dmax))
rank_rng = st.sidebar.slider("Rank range", 1, 50, key="f_rank")
album_types = st.sidebar.multiselect("Album type", ALBUMS, key="f_album")
content = st.sidebar.radio("Content", ["All", "Explicit only", "Non-explicit only"], key="f_content")
artists = st.sidebar.multiselect("Artist (lead artist)", sorted(df_all["lead_artist"].unique()), key="f_artist")
pool = df_all[df_all["lead_artist"].isin(artists)] if artists else df_all
_opts = sorted(pool["song_id"].unique())
st.session_state["f_song"] = [x for x in st.session_state["f_song"] if x in _opts]   # drop stale picks
songs = st.sidebar.multiselect("Song", _opts, key="f_song")

df = df_all[(df_all["date"].dt.date >= d0) & (df_all["date"].dt.date <= d1)
            & df_all["position"].between(*rank_rng) & df_all["album_type"].isin(album_types)]
if content != "All":
    df = df[df["is_explicit"] == (content == "Explicit only")]
if artists:
    df = df[df["lead_artist"].isin(artists)]
if songs:
    df = df[df["song_id"].isin(songs)]

st.title("🎵 US Top 50 Playlist Performance & Song Popularity Trends")
st.caption("Atlantic Recording Corporation · historical playlist analytics")
if df.empty:
    st.warning("No data for the selected filters. Widen the date/rank range, or click **🔄 Reset all filters** "
               "in the sidebar.")
    st.stop()

sf, af = song_features(df), artist_features(df)

# ------------------------------------------------------------------ KPIs
k = st.columns(6)
k[0].metric("Chart rows", f"{len(df):,}")
k[1].metric("Unique songs", f"{df['song_id'].nunique():,}")
k[2].metric("Avg days on chart", f"{sf['days_on_chart'].mean():.1f}")
k[3].metric("Avg rank", f"{df['position'].mean():.1f}")
k[4].metric("Avg rank volatility", f"{sf['rank_volatility'].mean():.1f}")
k[5].metric("Explicit share", f"{df['is_explicit'].mean() * 100:.1f}%")

tabs = st.tabs(["📅 Timeline Explorer", "📈 Song Trends", "🏆 Artist Leaderboard",
                "🔬 Popularity vs Rank", "🔞 Content Attributes", "🔁 Movement", "🧪 Data Quality"])

# ------------------------------------------------------------------ 1. timeline explorer
with tabs[0]:
    st.subheader("Playlist snapshot")
    day = st.select_slider("Pick a day", options=sorted(df["date"].dt.date.unique()),
                           value=sorted(df["date"].dt.date.unique())[-1])
    snap = df[df["date"].dt.date == day].sort_values("position")
    c1, c2 = st.columns([3, 2])
    c1.dataframe(snap[["position", "song", "artist", "popularity", "rank_change", "album_type", "is_explicit"]]
                 .rename(columns={"rank_change": "Δ vs prev day"}), hide_index=True, width="stretch")
    fig = px.bar(snap.sort_values("position", ascending=False), x="popularity", y="song", orientation="h",
                 color="album_type", height=max(350, 18 * len(snap)), title=f"Popularity by rank – {day}")
    c2.plotly_chart(fig, width="stretch")
    ds = an.daily_summary(df)
    st.plotly_chart(px.line(ds, x="date", y="avg_popularity", title="Average popularity of charting songs per day"),
                    width="stretch")
    heat = df.assign(day=df["date"].dt.date).pivot_table(index="song_id", columns="day", values="position")
    top_ids = df.groupby("song_id")["date"].nunique().nlargest(25).index
    st.plotly_chart(px.imshow(heat.loc[top_ids], aspect="auto", color_continuous_scale="Viridis_r",
                    title="Rank heatmap – 25 longest-charting songs (darker = better rank)"),
                    width="stretch")

# ------------------------------------------------------------------ 2. song trends
with tabs[1]:
    st.subheader("Song ranking trend")
    default = sf.nlargest(5, "days_on_chart")["song_id"].tolist()
    pick = st.multiselect("Songs to plot", sorted(sf["song_id"]), default=default)
    sub = df[df["song_id"].isin(pick)]
    f = px.line(sub, x="date", y="position", color="song_id", title="Daily rank (1 = top)")
    f.update_yaxes(autorange="reversed", range=[50, 1]); st.plotly_chart(f, width="stretch")
    st.plotly_chart(px.line(sub, x="date", y="pop_trend", color="song_id",
                            title="Popularity Trend Score (7-day rolling mean)"), width="stretch")
    c1, c2 = st.columns(2)
    c1.markdown("**Longest presence**")
    c1.dataframe(sf.nlargest(15, "days_on_chart")[["song", "artist", "days_on_chart", "avg_rank", "best_rank",
                 "rank_volatility"]].round(2), hide_index=True)
    c2.markdown("**Highest avg popularity (≥14 days)**")
    c2.dataframe(sf[sf.days_on_chart >= 14].nlargest(15, "avg_popularity")[["song", "artist", "avg_popularity",
                 "days_on_chart", "best_rank"]].round(2), hide_index=True)
    sc = px.scatter(sf, x="best_rank", y="days_on_chart", color="album_type", hover_data=["song", "artist"],
                    title="Peak rank vs longevity")
    sc.update_xaxes(autorange="reversed"); st.plotly_chart(sc, width="stretch")
    rho = an.peak_vs_longevity(sf)
    if rho is not None:
        st.info(f"Spearman ρ (best rank vs days on chart) = **{rho.statistic:.2f}** – better peaks tend to chart longer.")

# ------------------------------------------------------------------ 3. artists
with tabs[2]:
    st.subheader("Artist dominance leaderboard")
    n = st.slider("Top N artists", 5, 30, 15)
    lb = af.head(n)
    st.plotly_chart(px.bar(lb.sort_values("dominance_index"), x="dominance_index", y="artist", orientation="h",
                    color="unique_songs", title="Artist Dominance Index (% of all rank points)"),
                    width="stretch")
    st.dataframe(lb.round(2), hide_index=True, width="stretch")
    top_a = lb["artist"].head(6).tolist()
    monthly = (df[df["lead_artist"].isin(top_a)].assign(month=lambda d: d["date"].dt.to_period("M").dt.to_timestamp())
               .groupby(["month", "lead_artist"]).size().reset_index(name="appearances"))
    st.plotly_chart(px.area(monthly, x="month", y="appearances", color="lead_artist",
                            title="Dominance over time – monthly chart slots (top 6 artists)"),
                    width="stretch")

# ------------------------------------------------------------------ 4. popularity vs rank
with tabs[3]:
    st.subheader("Popularity vs rank")
    cr = an.pop_rank_corr(df)
    c = st.columns(2)
    fmt = lambda v: "n/a" if v != v else f"{v:.3f}"
    c[0].metric("Pearson r", fmt(cr["pearson_r"])); c[1].metric("Spearman ρ", fmt(cr["spearman_rho"]))
    if cr["pearson_r"] != cr["pearson_r"]:
        st.info("Too few rows (or no variation) in this selection to compute a correlation.")
    sample = df.sample(min(6000, len(df)), random_state=1)
    st.plotly_chart(px.scatter(sample, x="position", y="popularity", color="tier", opacity=.4,
                    title="Popularity vs rank (sample)"), width="stretch")
    st.plotly_chart(px.box(df, x="tier", y="popularity", color="tier", title="Popularity by rank tier"),
                    width="stretch")
    s, r = an.pop_stability_vs_volatility(sf)
    if r is None:
        st.info("Not enough songs with 14+ days in this selection for the stability chart.")
    else:
        st.plotly_chart(px.scatter(s, x="pop_volatility", y="rank_volatility", hover_data=["song", "artist"],
                        title=f"Popularity stability vs chart volatility (ρ={r.statistic:.2f})"),
                        width="stretch")

# ------------------------------------------------------------------ 5. content
with tabs[4]:
    st.subheader("Explicit vs non-explicit")
    e = an.explicit_perf(df); st.dataframe(e.round(2), hide_index=True)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(e, x="content", y=["avg_rank", "avg_popularity"], barmode="group",
                    title="Avg rank & popularity"), width="stretch")
    c2.plotly_chart(px.line(an.explicit_share_trend(df), x="date", y="explicit_share",
                    title="Explicit share of chart slots by month (%)"), width="stretch")
    st.subheader("Single vs album")
    a = an.album_type_perf(df); st.dataframe(a.round(2), hide_index=True)
    st.subheader("Duration & album size")
    d, s_ = an.duration_perf(df), an.album_size_perf(df)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(d, x="duration_band", y="top10_share", title="Top-10 share by duration (min)"),
                    width="stretch")
    c2.plotly_chart(px.bar(s_, x="album_size", y="avg_popularity", title="Avg popularity by album size"),
                    width="stretch")
    cm = an.content_correlations(df)
    if not cm.empty:
        st.plotly_chart(px.imshow(cm.round(2), text_auto=True,
                        title="Spearman correlation matrix"), width="stretch")

# ------------------------------------------------------------------ 6. movement
with tabs[5]:
    st.subheader("Rank movement, entries & exits")
    mv = an.rank_movement_distribution(df)
    st.plotly_chart(px.bar(mv, x="movement", y="count", title="Day-over-day rank movement"),
                    width="stretch")
    ee = an.entry_exit(df)
    st.plotly_chart(px.line(ee.set_index("date").rolling(7).mean().reset_index(), x="date", y=["entries", "exits"],
                    title="Entries vs exits (7-day avg)"), width="stretch")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(an.entry_position_profile(df), x="position", y="entries",
                    title="Where songs enter / re-enter"), width="stretch")
    c2.plotly_chart(px.bar(an.exit_position_profile(df), x="position", y="exits",
                    title="Last rank before leaving"), width="stretch")
    rise, fall = an.risers_decliners(df)
    if rise.empty:
        st.info("Risers/decliners need songs with at least 7 days in the current selection.")
    else:
        c1, c2 = st.columns(2)
        c1.markdown("**Steady climbers**")
        c1.dataframe(rise[["song", "artist", "days", "entry_rank", "best_rank", "slope_per_day"]].round(2), hide_index=True)
        c2.markdown("**Slow decliners**")
        c2.dataframe(fall[["song", "artist", "days", "entry_rank", "best_rank", "slope_per_day"]].round(2), hide_index=True)
    st.markdown("**Fast risers** (entered below #20, hit Top 10 within 7 days)")
    st.dataframe(an.fast_risers(df).round(2), hide_index=True)

# ------------------------------------------------------------------ 7. data quality
with tabs[6]:
    st.subheader("Validation report"); st.dataframe(report.as_frame().astype(str), hide_index=True)
    st.caption("Duplicate song-date rows are collapsed to the best rank. Popularity = 0 occurs for brand-new "
               "releases whose API score has not populated yet.")
    st.download_button("⬇️ Download filtered data", df.to_csv(index=False), "filtered_top50.csv")