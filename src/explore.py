"""Exploration rapide d'un export de tickets.
Usage : python src/explore.py data/fichier.xlsx
Produit un rapport texte dans outputs/exploration_report.md (statistiques agrégées,
sans copie des tickets : plus facile à sortir du poste si c'est autorisé)."""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from loader import detect_columns, load_table, prepare


def guess_lang(text):
    t = f" {text.lower()} "
    fr = sum(t.count(w) for w in (" le ", " la ", " les ", " des ", " est ", " pas ", " sur ", " une "))
    en = sum(t.count(w) for w in (" the ", " and ", " is ", " not ", " after ", " when ", " with "))
    if fr == en == 0:
        return "inconnue"
    return "fr" if fr > en else "en"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--sheet-top", type=int, default=10)
    ap.add_argument("--out", default="outputs/exploration_report.md")
    a = ap.parse_args()

    df = load_table(a.file)
    cols = detect_columns(df)
    prepared, cols, text_cols = prepare(df, cols)
    L = []
    add = L.append

    add(f"# Rapport d'exploration : {Path(a.file).name}\n")
    add(f"- Lignes : **{len(df)}**  |  Colonnes : **{df.shape[1]}**")
    add(f"- Colonnes détectées : {cols}")
    add(f"- Colonnes utilisées pour le texte : {text_cols}\n")

    add("## Colonnes : type et taux de vide\n")
    add("| Colonne | Type | % vide | Valeurs distinctes |")
    add("|---|---|---|---|")
    for c in df.columns:
        add(f"| {c} | {df[c].dtype} | {df[c].isna().mean()*100:.1f} | {df[c].nunique(dropna=True)} |")

    add("\n## Doublons\n")
    add(f"- Lignes strictement identiques : {int(df.duplicated().sum())}")
    if "key" in cols:
        add(f"- Clés de ticket dupliquées : {int(df[cols['key']].duplicated().sum())}")
    dup_txt = prepared["text"][prepared["text"].str.len() > 0].duplicated().sum()
    add(f"- Textes identiques (résumé+description) : {int(dup_txt)}")

    add("\n## Texte\n")
    lens = prepared["text"].str.split().str.len()
    add(f"- Mots par ticket : moyenne {lens.mean():.0f}, médiane {lens.median():.0f}, max {lens.max()}")
    add(f"- Tickets sans texte exploitable : {int((prepared['text'].str.len() == 0).sum())}")
    sample = prepared["text"].sample(min(300, len(prepared)), random_state=0)
    langs = sample.map(guess_lang).value_counts()
    add(f"- Langues (estimation sur échantillon) : {langs.to_dict()}")

    add("\n## Valeurs les plus fréquentes\n")
    for field in ("product", "component", "version", "sprint", "status", "resolution", "severity", "priority", "root_cause"):
        if field in cols:
            vc = df[cols[field]].value_counts(dropna=False).head(a.sheet_top)
            add(f"**{cols[field]}** : " + ", ".join(f"{k} ({v})" for k, v in vc.items()))

    add("\n## Étiquettes entre crochets dans les titres\n")
    from collections import Counter
    tagc = Counter(t for tags in prepared["_tags"] for t in tags)
    with_ref = int(prepared["_refs"].map(len).gt(0).sum())
    add(f"- Titres contenant une référence client [XXX-123] : {with_ref}/{len(prepared)}")
    add(f"- Titres avec au moins une étiquette : {int(prepared['_tags'].map(len).gt(0).sum())}/{len(prepared)}")
    if tagc:
        add("- Étiquettes les plus fréquentes : " + ", ".join(f"{k} ({v})" for k, v in tagc.most_common(a.sheet_top)))

    if "created" in cols:
        from loader import parse_dates
        d, fmt_used = parse_dates(df[cols["created"]])
        if d.notna().any():
            add("\n## Dates\n")
            add(f"- Format détecté : {fmt_used} | création du {d.min():%d/%m/%Y} au {d.max():%d/%m/%Y}")

    add("\n## À vérifier avec le tuteur\n")
    add("- Les champs ci-dessus correspondent-ils à ce que l'équipe utilise vraiment ?")
    add("- Où sont les tests fonctionnels liés (champ Jira, lien, autre outil) ?")
    add("- Données anonymisées ? Informations sensibles dans les descriptions ?")

    report = "\n".join(L)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n>>> Rapport enregistré : {a.out}")


if __name__ == "__main__":
    main()
