"""Testnivå 2: data. Ser datan ut som vi tror?"""

from churn.data import FEATURES, MAL, las_data, skapa_features


def test_forvantade_kolumner_finns():
    df = skapa_features(las_data())
    assert set(FEATURES + [MAL]) <= set(df.columns)


def test_malvariabeln_ar_binar():
    assert set(las_data()[MAL].unique()) <= {0, 1}


def test_kund_id_ar_unikt():
    df = las_data()
    assert df["kund_id"].is_unique


def test_alder_inom_rimligt_intervall():
    df = las_data()
    assert df["alder"].between(0, 120).all()
