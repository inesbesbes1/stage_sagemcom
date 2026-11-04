"""Chargement générique d'un export de tickets (xlsx, xls, csv, json) et
détection automatique des colonnes d'un export Jira (EN ou FR).

Gère aussi le format SAGEMCOM observé : titres du type
    "[VTVAS-12531] [Gen4][DE-Prod] Playback does not resume ..."
où les crochets contiennent la référence client et des étiquettes (module, plateforme)."""
import json
import re
from pathlib import Path

import pandas as pd

# Noms de colonnes possibles pour chaque champ logique (insensible à la casse)
CANDIDATES = {
    "key": ["issue key", "key", "id", "clé", "cle", "ticket", "issue id"],
    "summary": ["summary", "titre", "resume", "résumé", "title"],
    "description": ["description", "details", "détails"],
    "status": ["status", "statut"],
    "resolution": ["resolution", "résolution"],
    "severity": ["severity", "gravité", "gravite"],
    "priority": ["priority", "priorité", "priorite"],
    "component": ["component/s", "components", "component", "composant", "composants"],
    "version": ["fix version/s", "affects version/s", "affects version", "version", "versions"],
    "sprint": ["sprint"],
    "product": ["product", "produit", "project", "projet", "program", "programme"],
    "root_cause": ["root cause", "cause racine", "cause"],
    "pr_ref": ["pr reference in customer database", "pr reference", "customer reference"],
    "created": ["created", "créé", "date de création", "creation date"],
    "updated": ["updated", "mis à jour", "date de mise à jour"],
}

_TAG = re.compile(r"\[([^\]]+)\]")
_REF = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def load_table(path):
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p)
    if ext in (".csv", ".tsv", ".txt"):
        sep = "\t" if ext == ".tsv" else None
        for enc in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(p, sep=sep, engine="python", encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError("Encodage CSV non reconnu")
    if ext == ".json":
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "issues" in data:  # export REST Jira
                rows = []
                for it in data["issues"]:
                    row = {"key": it.get("key")}
                    row.update(it.get("fields", {}))
                    rows.append(row)
                data = rows
            else:
                data = [data]
        return pd.json_normalize(data)
    raise ValueError(f"Format non géré : {ext}")


def detect_columns(df):
    """Retourne {champ_logique: nom_colonne_réel} pour les colonnes trouvées."""
    lower = {c.lower().strip(): c for c in df.columns}
    found = {}
    for field, names in CANDIDATES.items():
        for n in names:
            if n in lower:
                found[field] = lower[n]
                break
    return found


def clean_text(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = str(s)
    s = re.sub(r"\{code[^}]*\}.*?\{code\}", " ", s, flags=re.S)  # blocs de code Jira
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def split_title(summary):
    """'[VTVAS-1] [Player][OTT] Texte' -> ('Texte', ['Player','OTT'], ['VTVAS-1'])"""
    s = clean_text(summary)
    tags, refs = [], []
    for t in _TAG.findall(s):
        t = t.strip()
        (refs if _REF.match(t) else tags).append(t)
    title = re.sub(r"\s+", " ", _TAG.sub(" ", s)).strip()
    return title, tags, refs


def parse_dates(series):
    """Essaie le format américain (m/j/aaaa), puis jour d'abord, puis automatique."""
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.notna().mean() > 0.9:
            return parsed, fmt
    return pd.to_datetime(series, errors="coerce"), "auto"


def key_number(key):
    m = re.search(r"(\d+)\s*$", str(key))
    return int(m.group(1)) if m else -1


def prepare(df, cols=None, text_cols=None):
    """Ajoute des colonnes calculées (les données d'origine restent intactes) :
    _key, _num, _title (titre sans crochets), _tags, _refs, text (texte pour la recherche).
    Retourne (df, cols, text_cols_utilisées)."""
    cols = cols or detect_columns(df)
    out = df.copy()

    if "key" in cols:
        out["_key"] = out[cols["key"]].astype(str).str.strip()
    else:
        out["_key"] = [f"ROW-{i}" for i in range(len(out))]
    out["_num"] = out["_key"].map(key_number)

    if text_cols:  # colonnes imposées par l'utilisateur : texte brut nettoyé
        out["_title"] = out[text_cols].fillna("").astype(str).agg(" ".join, axis=1).map(clean_text)
        out["_tags"] = [[] for _ in range(len(out))]
        out["_refs"] = [[] for _ in range(len(out))]
        out["text"] = out["_title"]
        return out, cols, list(text_cols)

    used = []
    if "summary" in cols:
        parts = out[cols["summary"]].map(split_title)
        out["_title"] = parts.map(lambda x: x[0])
        out["_tags"] = parts.map(lambda x: x[1])
        out["_refs"] = parts.map(lambda x: x[2])
        used.append(cols["summary"])
    else:
        fallback = [c for c in df.columns if df[c].dtype == object][:1]
        out["_title"] = out[fallback].fillna("").astype(str).agg(" ".join, axis=1).map(clean_text)
        out["_tags"] = [[] for _ in range(len(out))]
        out["_refs"] = [[] for _ in range(len(out))]
        used += fallback

    desc = out[cols["description"]].map(clean_text) if "description" in cols else ""
    if "description" in cols:
        used.append(cols["description"])
    tags_txt = out["_tags"].map(lambda t: " ".join(t))
    out["text"] = (out["_title"] + " " + tags_txt + " " + desc).map(clean_text)
    return out, cols, used
