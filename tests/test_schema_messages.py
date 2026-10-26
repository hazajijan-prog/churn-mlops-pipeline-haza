"""Kontrollerar återkoppling om schemaförändringar via valideringskommandot."""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJEKTROT = Path(__file__).resolve().parents[1]
KOLUMNER = [
    "kund_id", "alder", "region", "manader_som_kund", "abonnemang",
    "manadskostnad", "data_gb_per_manad", "supportarenden_12m", "avslutat",
]


@pytest.fixture
def kunddata():
    return pd.read_csv(PROJEKTROT / "data" / "kundbas.csv").head(5)


def kor_validering(df, tmp_path):
    fil = tmp_path / "leverans.csv"
    df.to_csv(fil, index=False)
    return subprocess.run(
        [sys.executable, "-B", "-m", "kontroller.validera", str(fil)],
        cwd=PROJEKTROT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("kolumn", KOLUMNER)
def test_saknad_obligatorisk_kolumn_forklaras(kunddata, tmp_path, kolumn):
    resultat = kor_validering(kunddata.drop(columns=[kolumn]), tmp_path)

    assert resultat.returncode == 1
    assert f"Obligatoriska kolumner saknas: {kolumn}." in resultat.stdout
    assert "Åtgärd: Återställ kolumnerna med rätt namn och innehåll." in resultat.stdout
    assert "Traceback" not in resultat.stderr


@pytest.mark.parametrize("extra", [["start"], ["kundsegment"], ["start", "ny_kolumn"]])
def test_ovantade_kolumner_forklaras(kunddata, tmp_path, extra):
    for kolumn in extra:
        kunddata[kolumn] = "extra information"
    resultat = kor_validering(kunddata, tmp_path)

    assert resultat.returncode == 1
    assert f"Oväntade kolumner: {', '.join(extra)}." in resultat.stdout
    assert "Åtgärd: Ta bort oväntade kolumner eller stäm av schemaändringen." in resultat.stdout
    assert "Traceback" not in resultat.stderr


def test_extra_kolumn_doljer_inte_ogiltig_alder(kunddata, tmp_path):
    kunddata["kundsegment"] = "extra information"
    kunddata.loc[0, "alder"] = 150
    resultat = kor_validering(kunddata, tmp_path)

    assert resultat.returncode == 1
    assert "Oväntade kolumner: kundsegment." in resultat.stdout
    assert "alder" in resultat.stdout
    assert "in_range(18, 110)" in resultat.stdout
    assert "150" in resultat.stdout


def test_flera_saknade_och_extra_kolumner_visas(kunddata, tmp_path):
    kunddata = kunddata.drop(columns=["alder", "region"])
    kunddata["start"] = "extra information"
    resultat = kor_validering(kunddata, tmp_path)

    assert resultat.returncode == 1
    assert "Obligatoriska kolumner saknas: alder, region." in resultat.stdout
    assert "Oväntade kolumner: start." in resultat.stdout
    assert "Åtgärd: Återställ" in resultat.stdout
    assert "Åtgärd: Ta bort" in resultat.stdout


def test_giltig_data_godkanns_utan_schemafel(kunddata, tmp_path):
    resultat = kor_validering(kunddata, tmp_path)

    assert resultat.returncode == 0
    assert "OK:" in resultat.stdout
    assert "STOPP:" not in resultat.stdout
    assert "Åtgärd:" not in resultat.stdout
