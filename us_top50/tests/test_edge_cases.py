import math
import pytest
from src.data_pipeline import load_all, song_features, artist_features
from src import analytics as an

DF, _ = load_all("data/Atlantic_United_States.csv")

@pytest.mark.parametrize("subset", [
    DF.iloc[:1], DF.iloc[:2], DF[DF.date == DF.date.iloc[0]], DF[DF.position == 1],
    DF[DF.album_type == "compilation"], DF[DF.song_id == DF.song_id.iloc[0]].iloc[:1]])
def test_every_analytic_survives_tiny_selection(subset):
    sf, af = song_features(subset), artist_features(subset)
    an.daily_summary(subset); an.rank_movement_distribution(subset); an.entry_exit(subset)
    an.risers_decliners(subset); an.fast_risers(subset); an.peak_vs_longevity(sf)
    an.pop_by_tier(subset); an.pop_stability_vs_volatility(sf); an.content_correlations(subset)
    an.explicit_perf(subset); an.album_type_perf(subset); an.duration_perf(subset); an.album_size_perf(subset)
    r = an.pop_rank_corr(subset)
    assert all(math.isnan(v) or isinstance(v, float) for v in r.values())

def test_safe_corr_constant_and_short():
    assert an.safe_corr([1, 1, 1], [1, 2, 3]) is None
    assert an.safe_corr([1, 2], [1, 2]) is None
    assert an.safe_corr([1, 2, 3, 4], [1, 2, 3, 5]) is not None
