#!/usr/bin/env python
# coding: utf-8
"""Ladda ner och presentera valresultat"""

import hashlib
import json
import numpy as np
import urllib.request
import zipfile
from pathlib import Path


# Konfiguration
BASE_URL = "https://resultat.val.se/resultatfiler/val2026/"
INDEX_URL = BASE_URL + "index.md5"
DOWNLOAD_DIR = Path("./valdata_zip")
EXTRACT_DIR = Path("./valdata_json")

# 
RODGRONA = ("V", "S", "MP", "C")
GULBLA = ("L", "M", "KD", "SD")


def calculate_md5(filepath: Path) -> str:
    """Beräknar MD5-hash för en lokal fil."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sync_valdata(verbose=0):
    """sync valdata"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Hämtar indexfil: {INDEX_URL}")
    request = urllib.request.Request(
        INDEX_URL, headers={"User-Agent": "ValdataFetcher/1.0"},
    )

    try:
        with urllib.request.urlopen(request) as response:
            index_lines = response.read().decode("utf-8").strip().splitlines()
    except Exception as e:
        print(f"Kunde inte hämta indexfilen: {e}")
        return

    for line in index_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue

        expected_md5, relative_path = parts
        relative_path = relative_path.lstrip("*").strip()
        filename = Path(relative_path).name

        local_zip_path = DOWNLOAD_DIR / filename
        file_url = (
            relative_path
            if relative_path.startswith("http")
            else BASE_URL + relative_path
        )

        # Kontrollera om filen redan finns och är oförändrad
        if (
            local_zip_path.exists()
            and calculate_md5(local_zip_path) == expected_md5
        ):
            if verbose:
                print(f"[OFÖRÄNDRAD] {filename}")
            continue

        # Ladda ner ny eller ändrad fil
        if verbose:
            print(f"[HÄMTAR] {filename}...")
        try:
            urllib.request.urlretrieve(file_url, local_zip_path)
        except Exception as e:
            print(f"Misslyckades att ladda ner {filename}: {e}")
            continue

        # Validera MD5-checksumma
        actual_md5 = calculate_md5(local_zip_path)
        if actual_md5 != expected_md5:
            print(
                f"[FEL] Checksumma matchar inte för {filename}" +
                f" (Förväntad: {expected_md5}, Fick: {actual_md5})"
            )
            continue

        # Packa upp ZIP-filen
        if verbose:
            print(f"[PACKAR UPP] {filename} -> {EXTRACT_DIR}")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)

    if verbose:
        print("Synkronisering genomförd.")


def get_roster(data, verbose = 0):
    """return röster per parti"""

    # initialisera parti-variabler
    n_totalt = 0
    vansterpartiet = socialdemokraterna = miljopartiet = 0
    centern = liberalerna = moderaterna = 0
    kristdemokraterna = sverigedemokraterna = 0

    # För varje respektive parti, hämta antalet röster
    for pr in data['valomrade']['rostfordelning']['rosterPaverkaMandat']['partiRoster']:
        pb = pr['partibeteckning']
        nr = pr['antalRoster']

        if 'Socialdemokraterna' in pb:
            socialdemokraterna = nr
        if 'Vänsterpartiet' in pb:
            vansterpartiet = nr
        if 'Miljöpartiet' in pb:
            miljopartiet = nr
        if 'Centerpartiet' in pb:
            centern = nr
        if 'Moderaterna' in pb:
            moderaterna = nr
        if 'Liberalerna' in pb:
            liberalerna = nr
        if 'Kristdemokraterna' in pb:
            kristdemokraterna = nr
        if 'Sverigedemokraterna' in pb:
            sverigedemokraterna = nr
        if verbose:
            print(f"{pb}:\t{nr}")
        n_totalt += nr

    # Övriga
    (pb, n_ovriga) = (
            'Övriga',
            data['valomrade']
                ['rostfordelning']
                ['rosterPaverkaMandat']
                ['rosterOvrigaPartier']
                ['antalRoster'])
    if verbose:
        print(f"{pb}:\t{n_ovriga}")

    # Ogiltiga
    n_totalt += n_ovriga
    (pb, n_ogiltiga) = (
            'Ogiltiga',
            data['valomrade']
                ['rostfordelning']
                ['rosterEjPaverkaMandat']
                ['antalRoster'])
    if verbose:
        print(f"{pb}:\t{n_ogiltiga}")

    # distrikt
    n_distrikt_ska_raknas = data['valomrade']['antalValdistriktSomSkaRaknas']
    n_distrikt_raknade = data['valomrade']['antalValdistriktRaknade']

    return np.array([vansterpartiet,
                     socialdemokraterna,
                     miljopartiet,
                     centern,
                     liberalerna,
                     moderaterna,
                     kristdemokraterna,
                     sverigedemokraterna,
                     n_ovriga, n_ogiltiga, n_totalt,
                     n_totalt + n_ogiltiga,
                     n_distrikt_ska_raknas,
                     n_distrikt_raknade,])

def get_mandat(data, verbose = 0):
    """return mandat per parti"""
    # initialisera parti-variabler
    nm_totalt = 0
    m_V = m_S = m_MP = m_C = 0
    m_L = m_M = m_KD = m_SD = 0
    m_RG = m_GB = 0
    # hämta antal mandat
    for parti in data['valomrade']['mandatfordelning']['partiLista']:
        pfk = parti['partiforkortning']
        nm = parti['antalMandat']
        if pfk == "S": 
            m_S = nm
        if pfk == "V":
            m_V = nm
        if pfk == "MP":
            m_MP = nm
        if pfk == "C":
            m_C = nm
        if pfk == "M":
            m_M = nm
        if pfk == "L":
            m_L = nm
        if pfk == "KD":
            m_KD = nm
        if pfk == "SD":
            m_SD = nm
        if verbose:
            print(f"{pfk}:\t{nm}")
        nm_totalt += nm

        if pfk in RODGRONA:
            m_RG += nm
        if pfk in GULBLA:
            m_GB += nm
    return np.array([m_V, m_S, m_MP, m_C,
                     m_L, m_M, m_KD, m_SD,
                     m_RG, m_GB
                   ])


if __name__ == '__main__':

    # get updated valdata from Valmyndigheten
    sync_valdata()

    # VALNATT
    print("VALNATT:")
    try:
        with open(
                "valdata_json/Val_2026_preliminar_mandatfordelning_00_RD.json",
                "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise SystemExit(1) from e

    roster = get_roster(data, verbose=0)
    [V, S, MP, C,
     L, M, KD, SD,
     OVR, OG, 
     TOT_G, TOT,
     N_DISTRIKT, 
     N_DISTRIKT_RAKNADE] = roster
    # make a dict with partinamn as keys
    namn = ['V', 'S', 'MP', 'C', 'L', 'M', 'KD', 'SD',
            'Övriga', 'Ogiltiga', 'Totalt giltiga', 'Totalt',]
    res = dict(zip(namn, roster))
    for key, val in res.items():
        if key in ("Ogiltiga", "Totalt", "Totalt giltiga"):
            continue
        # print(f"{key}:\t\t {(100 * val / TOT_G).round(precision):>6.2f} %")
        print(f"{key}:\t\t{val:>10_d}\t\t{(100 * val / TOT_G):>6.1f} %")
    print(f"Totalt giltiga:\t{TOT_G:10_d}")
    print(f"Totalt:\t\t{TOT:10_d}")
    RG = V + S + MP + C
    GB = L + M + KD + SD
    RG_PROC = RG / TOT_G
    GB_PROC = GB / TOT_G
    print(f"Rödgröna:\t{RG:10_d}\t\t{(100 * RG / TOT_G):>6.2f} %")
    print(f"Gulblåa:\t{GB:10_d}\t\t{(100 * GB / TOT_G):>6.2f} %")
    print(f"Differens:\t{RG - GB:10_d}\t\t{100 * (RG_PROC - GB_PROC):>6.2f} %")
    # Antal räknade distrikt
    print(f"""Antal räknade distrikt: {N_DISTRIKT_RAKNADE} """
          f"""av {N_DISTRIKT} ({N_DISTRIKT_RAKNADE / N_DISTRIKT * 100:.2f}%)""")
    # Mandat
    mandat_fordelning = get_mandat(data, verbose=0)
    print("Rödgröna vs. Blågula: ", end="")
    print(f"{mandat_fordelning[-2]} - ", end="")
    print(f"{mandat_fordelning[-1]} mandat")
    print()

    # SLUTLIG
    print("SLUTLIG:")
    try:
        with open(
                "valdata_json/Val_2026_slutlig_mandatfordelning_00_RD.json",
                "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise SystemExit(1) from e

    roster = get_roster(data, verbose=0)
    [V, S, MP, C,
     L, M, KD, SD,
     OVR, OG, 
     TOT_G, TOT,
     N_DISTRIKT, 
     N_DISTRIKT_RAKNADE] = roster
    # make a dict with partinamn as keys
    namn = ['V', 'S', 'MP', 'C', 'L', 'M', 'KD', 'SD',
            'Övriga', 'Ogiltiga', 'Totalt giltiga', 'Totalt',]
    res = dict(zip(namn, roster))
    for key, val in res.items():
        if key in ("Ogiltiga", "Totalt", "Totalt giltiga"):
            continue
        # print(f"{key}:\t\t {(100 * val / TOT_G).round(precision):>6.2f} %")
        print(f"{key}:\t\t{val:>10_d}\t\t{(100 * val / TOT_G):>6.1f} %")
    print(f"Totalt giltiga:\t{TOT_G:10_d}")
    print(f"Totalt:\t\t{TOT:10_d}")
    RG = V + S + MP + C
    GB = L + M + KD + SD
    RG_PROC = RG / TOT_G
    GB_PROC = GB / TOT_G
    print(f"Rödgröna:\t{RG:10_d}\t\t{(100 * RG / TOT_G):>6.2f} %")
    print(f"Gulblåa:\t{GB:10_d}\t\t{(100 * GB / TOT_G):>6.2f} %")
    print(f"Differens:\t{RG - GB:10_d}\t\t{100 * (RG_PROC - GB_PROC):>6.2f} %")
    # Antal räknade distrikt
    print(f"""Antal räknade distrikt: {N_DISTRIKT_RAKNADE} """
          f"""av {N_DISTRIKT} ({N_DISTRIKT_RAKNADE / N_DISTRIKT * 100:.2f}%)""")
    # Mandat
    # mandat_fordelning = get_mandat(data, verbose=0)
    # print("Rödgröna vs. Blågula: ", end="")
    # print(f"{mandat_fordelning[-2]} - ", end="")
    # print(f"{mandat_fordelning[-1]} mandat")
