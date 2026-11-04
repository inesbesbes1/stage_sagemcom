"""Construit un PROFIL STATISTIQUE d'un export de tickets, pour rendre les faux tickets
plus proches des vrais. Le profil ne contient AUCUN titre, AUCUNE description, AUCUN nom de personne :
seulement des fréquences (gravité, statut, composant, étiquettes...), des taux de cases vides,
la longueur des titres et la période des dates.

Usage (sur le poste SAGEMCOM, sur le vrai fichier) :
    python src/make_profile.py data/FICHIER.csv
Résultat : outputs/profile.json  -> à faire valider avant de l'emporter, puis :
    python src/generate_synthetic.py --profile outputs/profile.json

Les valeurs vues moins de --min-count fois sont ignorées (elles pourraient identifier un ticket).
Sur un petit fichier, baisser --min-count (ex. 1).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from loader import detect_columns, load_table, parse_dates, prepare

CATEGORICAL = ["severity", "priority", "status", "resolution", "component", "sprint", "version"]


def freq(series, min_count, max_values=25):
    n = len(series)
    s = series.dropna().astype(str).str.strip()
    s = s[s != ""]
    vc = s.value_counts()
    keep = vc[vc >= min_count].head(max_values)
    return {
        "empty_rate": round(1 - len(s) / n, 3) if n else 0,
        "values": [str(v) for v in keep.index],
        "weights": [int(v) for v in keep.values],
        "ignored_rare_values": int(len(vc) - len(keep)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", default="outputs/profile.json")
    ap.add_argument("--min-count", type=int, default=3)
    a = ap.parse_args()

    raw = load_table(a.file)
    cols = detect_columns(raw)
    df, cols, _ = prepare(raw, cols)
    prof = {
        "privacy_note": "Profil statistique : aucun texte de ticket, aucun nom de personne. À faire valider avant de le sortir du poste.",
        "source_file": Path(a.file).name,
        "n_tickets": int(len(df)),
        "categorical": {},
    }

    for field in CATEGORICAL:
        if field in cols:
            prof["categorical"][field] = freq(raw[cols[field]], a.min_count)

    prefixes = Counter(re.match(r"^([A-Za-z0-9]+)-\d+", k).group(1) for k in df["_key"] if re.match(r"^([A-Za-z0-9]+)-\d+", k))
    if prefixes:
        prof["key_prefix"] = prefixes.most_common(1)[0][0]
        nums = df["_num"][df["_num"] >= 0]
        prof["key_range"] = [int(nums.min()), int(nums.max())]

    words = df["_title"].str.split().str.len()
    prof["title_words"] = {"mean": round(float(words.mean()), 1), "p10": float(words.quantile(0.1)),
                           "p50": float(words.quantile(0.5)), "p90": float(words.quantile(0.9))}

    tag_counts = Counter(t for tags in df["_tags"] for t in tags)
    per_title = Counter(min(len(t), 3) for t in df["_tags"])
    kept = [(t, c) for t, c in tag_counts.most_common(30) if c >= a.min_count]
    prof["tags"] = {
        "values": [t for t, _ in kept],
        "weights": [c for _, c in kept],
        "tags_per_title": {str(k): round(v / len(df), 3) for k, v in sorted(per_title.items())},
        "titles_with_customer_ref": round(float(df["_refs"].map(len).gt(0).mean()), 3),
    }

    if "created" in cols:
        created, fmt = parse_dates(raw[cols["created"]])
        if created.notna().any():
            prof["dates"] = {"format": fmt, "min": f"{created.min():%Y-%m-%d}", "max": f"{created.max():%Y-%m-%d}"}
            if "updated" in cols:
                upd, _ = parse_dates(raw[cols["updated"]])
                delta = (upd - created).dt.days.dropna().clip(lower=0)
                if len(delta):
                    prof["dates"]["update_delta_days"] = {"p10": float(delta.quantile(0.1)),
                                                          "p50": float(delta.quantile(0.5)),
                                                          "p90": float(delta.quantile(0.9))}

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(prof, ensure_ascii=False, indent=2))
    print(f"\n>>> Profil enregistré : {a.out}  (à faire valider avant de l'emporter)")


if __name__ == "__main__":
    main()
