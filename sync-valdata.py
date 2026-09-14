#!/usr/bin/env python

"""get valdata"""

import hashlib
import urllib.request
import zipfile
from pathlib import Path


# Konfiguration
BASE_URL = "https://resultat.val.se/resultatfiler/val2026/"
INDEX_URL = BASE_URL + "index.md5"
DOWNLOAD_DIR = Path("./valdata_zip")
EXTRACT_DIR = Path("./valdata_json")


def calculate_md5(filepath: Path) -> str:
    """Beräknar MD5-hash för en lokal fil."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sync_valdata():
    """sync valdata"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Hämtar indexfil: {INDEX_URL}")
    request = urllib.request.Request(
        INDEX_URL, headers={"User-Agent": "ValdataFetcher/1.0"}
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
            print(f"[OFÖRÄNDRAD] {filename}")
            continue

        # Ladda ner ny eller ändrad fil
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
        print(f"[PACKAR UPP] {filename} -> {EXTRACT_DIR}")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)

    print("Synkronisering genomförd.")


if __name__ == "__main__":
    sync_valdata()


