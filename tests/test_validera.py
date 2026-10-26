"""Tester för CSV-validering, felkoder och begripliga felmeddelanden."""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from kontroller.validera import main

PROJEKTROT = Path(__file__).resolve().parents[1]


@pytest.fixture
def csv_data():
    return pd.DataFrame(
        {
            "kund_id": [1, 2],
            "alder": [25, 40],
            "region": ["Stockholm", "Väst"],
            "manader_som_kund": [12, 24],
            "abonnemang": ["Bas", "Premium"],
            "manadskostnad": [199.0, 399.0],
            "data_gb_per_manad": [5.0, 20.0],
            "supportarenden_12m": [0, 2],
            "avslutat": [0, 1],
        }
    )


def kor_validering(fil):
    return subprocess.run(
        [sys.executable, "-B", "-m", "kontroller.validera", str(fil)],
        cwd=PROJEKTROT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_giltig_csv_godkanns(tmp_path, capsys, csv_data):
    fil = tmp_path / "giltig.csv"
    csv_data.to_csv(fil, index=False)

    resultat = main(str(fil))
    utskrift = capsys.readouterr().out

    assert resultat == 0
    assert "OK:" in utskrift
    assert "2 rader" in utskrift


def test_ogiltig_csv_stoppas(tmp_path, capsys, csv_data):
    fil = tmp_path / "ogiltig.csv"
    csv_data.loc[0, "alder"] = 15
    csv_data.to_csv(fil, index=False)

    resultat = main(str(fil))
    utskrift = capsys.readouterr().out

    assert resultat == 1
    assert "STOPP:" in utskrift
    assert "alder" in utskrift


def test_giltig_kundfil_godkanns():
    fil = PROJEKTROT / "data" / "kundbas.csv"
    resultat = kor_validering(fil)

    assert resultat.returncode == 0
    assert f"OK: {fil}" in resultat.stdout
    assert "Traceback" not in resultat.stderr


@pytest.mark.parametrize(
    ("fall", "orsak", "vagledning"),
    [
        ("saknad", "saknas", "Kontrollera filnamnet och sökvägen"),
        ("tom", "är tom", "Leverera en CSV med rubriker och datarader"),
        ("bara_rubriker", "innehåller inga datarader", "Leverera en CSV med kundrader"),
        ("trasig", "oläsbart CSV-format", "Kontrollera citattecken och avgränsare"),
    ],
)
def test_felaktig_leverans_stoppas_med_tydligt_meddelande(tmp_path, fall, orsak, vagledning):
    fil = tmp_path / f"{fall}.csv"
    if fall == "tom":
        fil.write_text("", encoding="utf-8")
    elif fall == "bara_rubriker":
        with (PROJEKTROT / "data" / "kundbas.csv").open(encoding="utf-8") as kundfil:
            fil.write_text(kundfil.readline(), encoding="utf-8")
    elif fall == "trasig":
        fil.write_text('kund_id,alder\n100001,"75\n', encoding="utf-8")
    # Ingen fil skapas i fallet "saknad".

    resultat = kor_validering(fil)

    assert resultat.returncode == 1
    assert f"STOPP: {fil}" in resultat.stdout
    assert orsak in resultat.stdout
    assert vagledning in resultat.stdout
    assert "Traceback" not in resultat.stderr
