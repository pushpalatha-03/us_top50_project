import pandas as pd
from src.data_pipeline import load_all, song_features, artist_features, lead_artist

DF, REP = load_all("data/Atlantic_United_States.csv")

def test_rank_range():            assert DF["position"].between(1, 50).all()
def test_no_dup_song_day():       assert not DF.duplicated(["date", "song_id"]).any()
def test_report_counts():         assert REP.rows_raw - REP.duplicate_song_date == REP.rows_clean
def test_lead_artist():
    assert lead_artist("Lil Durk & J. Cole") == "Lil Durk"
    assert lead_artist("Tyler, The Creator") == "Tyler, The Creator"
def test_song_features():
    sf = song_features(DF)
    assert (sf["days_on_chart"] >= 1).all() and (sf["best_rank"] <= sf["avg_rank"]).all()
def test_dominance_sums_to_100():
    assert abs(artist_features(DF)["dominance_index"].sum() - 100) < 1e-6
def test_rank_change_sign():
    r = DF.dropna(subset=["rank_change"]).iloc[0]
    assert r["rank_change"] == r["prev_position"] - r["position"]
