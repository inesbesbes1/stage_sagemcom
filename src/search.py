"""Recherche de tickets similaires.

Moteurs :
  tfidf       (défaut) : scikit-learn uniquement, aucun téléchargement.
  keywords    : approximation d'une recherche par mots-clés techniques (comme une requête
                Jira 'text ~ ...'), pour servir de point de comparaison. Ce n'est PAS le code
                de Bug Matcher, seulement une approche du même type.
  embeddings  : sentence-transformers (modèle à télécharger, si autorisé).

Exemples :
  python src/search.py data/tickets.csv --query "no video after zapping"
  python src/search.py data/tickets.csv --ticket AVTV-7397
  python src/search.py data/tickets.csv --eval queries.csv            # Top-1, Top-5, MRR
  python src/search.py data/tickets.csv --eval queries.csv --compare  # tfidf vs keywords (vs embeddings)
  python src/search.py data/tickets.csv --export outputs/candidats.csv --k 15
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from loader import detect_columns, load_table, prepare

# Familles de termes techniques (liste volontairement courte, à enrichir avec l'équipe)
FAMILIES = {
    "wifi": ["wifi", "wi-fi", "wireless"], "network": ["network", "ethernet", "access point"],
    "bluetooth": ["bluetooth"], "hdmi": ["hdmi", "cable"], "reboot": ["reboot", "restart", "rebooting"],
    "boot": ["boot", "booting", "startup"], "standby": ["standby", "sleep"], "crash": ["crash", "crashes", "crashing"],
    "freeze": ["freeze", "freezes", "frozen", "stuck"], "resume": ["resume", "resuming"],
    "audio": ["audio", "sound"], "video": ["video", "picture", "image"], "playback": ["playback"],
    "player": ["player"], "pause": ["pause", "paused"], "subtitle": ["subtitle", "subtitles", "caption", "captions"],
    "channel": ["channel", "channels", "zapping"], "live": ["live"], "mcast": ["mcast", "multicast"],
    "blackscreen": ["black screen"], "rcu": ["rcu", "remote"], "settings": ["settings"],
    "parental": ["parental", "pin"], "energy": ["energy", "power"], "ott": ["ott"],
    "translation": ["translated", "translation", "localization"], "reset": ["factory reset", "clear data", "cleardata"],
    "accessibility": ["accessibility", "text scaling", "bold text", "font"], "forget": ["forget", "forgotten"],
    "trick": ["trick mode"],
}


class TfidfEngine:
    name = "tfidf"

    def __init__(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode")
        self.matrix = self.vec.fit_transform(texts)

    def scores(self, query):
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity(self.vec.transform([query]), self.matrix).ravel()


class KeywordEngine:
    name = "keywords"

    def __init__(self, texts):
        self.sets = [self.terms(t) for t in texts]

    @staticmethod
    def terms(text):
        t = " " + re.sub(r"[^a-z0-9\- ]+", " ", str(text).lower()) + " "
        return {fam for fam, variants in FAMILIES.items() if any(f" {v} " in t for v in variants)}

    def scores(self, query):
        q = self.terms(query)
        if not q:
            return np.zeros(len(self.sets))
        return np.array([len(q & s) / len(q | s) if s else 0.0 for s in self.sets])


class EmbeddingEngine:
    name = "embeddings"

    def __init__(self, texts, model="paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer  # installation + modèle nécessaires
        self.model = SentenceTransformer(model)
        self.emb = self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=True)

    def scores(self, query):
        q = self.model.encode([query], normalize_embeddings=True)[0]
        return self.emb @ q


def build_engine(kind, texts, quiet=False):
    if kind == "embeddings":
        try:
            return EmbeddingEngine(texts)
        except Exception as e:  # paquet absent, modèle non téléchargeable, réseau bloqué...
            if not quiet:
                print(f"[!] Embeddings indisponibles ({type(e).__name__}). Repli sur TF-IDF.")
    if kind == "keywords":
        return KeywordEngine(texts)
    return TfidfEngine(texts)


def top_k(engine, df, query, k=5, exclude_key=None, before_num=None, min_score=0.0):
    """before_num : ne garde que les tickets de numéro inférieur (comme Bug Matcher : bugs plus anciens)."""
    s = engine.scores(query)
    res = []
    for i in np.argsort(-s):
        if s[i] <= 0 or s[i] < min_score:
            break
        if exclude_key is not None and df["_key"].iloc[i] == exclude_key:
            continue
        if before_num is not None and df["_num"].iloc[i] >= before_num:
            continue
        res.append((df["_key"].iloc[i], float(s[i]), df["_title"].iloc[i]))
        if len(res) == k:
            break
    return res


def show(results):
    if not results:
        print("  (aucun ticket pertinent)")
    for key, score, text in results:
        print(f"  {key:<12} score={score:.3f}  {text[:105]}")


def evaluate(engine, df, q, k=5, verbose=True):
    hits1 = hits5 = 0
    rr = []
    for _, r in q.iterrows():
        expected = set(str(r["expected_key"]).split("|"))
        keys = [x[0] for x in top_k(engine, df, str(r["query"]), k)]
        rank = next((i + 1 for i, kk in enumerate(keys) if kk in expected), None)
        hits1 += rank == 1
        hits5 += rank is not None and rank <= 5
        rr.append(1 / rank if rank else 0)
        if verbose:
            print(f"  [{'OK ' if rank else 'KO '}] rang={rank}  requête={str(r['query'])[:70]}")
    n = len(q)
    return {"n": n, "top1": hits1 / n, "top5": hits5 / n, "mrr": float(np.mean(rr))}


def export_matches(engine, df, cols, path, k, older_only=True, min_score=0.1):
    """Écrit un CSV au format de Bug Matcher (une ligne par candidat) + une colonne Score."""
    raw_sum = cols.get("summary")
    raw_st = cols.get("status")
    rows = []
    for _, r in df.iterrows():
        res = top_k(engine, df, r["text"], k, exclude_key=r["_key"], before_num=r["_num"] if older_only else None, min_score=min_score)
        src = r[raw_sum] if raw_sum else r["_title"]
        if not res:
            rows.append([r["_key"], src, "", "Aucun bug similaire trouvé", "", ""])
        for i, (key, score, _) in enumerate(res):
            m = df[df["_key"] == key].iloc[0]
            rows.append([r["_key"], src if i == 0 else "", key, m[raw_sum] if raw_sum else m["_title"],
                         m[raw_st] if raw_st else "", round(score, 3)])
    out = pd.DataFrame(rows, columns=["Bug_Source", "Summary_Source", "Bug_Similaire",
                                      "Summary_Bug_Similaire", "Statut_Bug_Similaire", f"Score_{engine.name}"])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False, quoting=1)
    print(f"{len(out)} lignes écrites dans {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--engine", choices=["tfidf", "keywords", "embeddings"], default="tfidf")
    ap.add_argument("--query")
    ap.add_argument("--ticket", help="clé d'un ticket : trouve ses voisins")
    ap.add_argument("--eval", help="CSV avec colonnes query,expected_key (plusieurs clés séparées par |)")
    ap.add_argument("--compare", action="store_true", help="avec --eval : compare tous les moteurs")
    ap.add_argument("--export", help="écrit les candidats de chaque ticket au format Bug Matcher")
    ap.add_argument("--all-ages", dest="all_ages", action="store_true",
                    help="avec --export : autorise aussi les tickets plus récents")
    ap.add_argument("--min-score", type=float, default=0.1, help="avec --export : score minimal d'un candidat")
    ap.add_argument("--text-cols", nargs="+", help="forcer les colonnes de texte")
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()

    raw = load_table(a.file)
    df, cols, text_cols = prepare(raw, detect_columns(raw), a.text_cols)
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    print(f"{len(df)} tickets indexés | texte construit depuis = {text_cols} | moteur = {a.engine}")
    engine = build_engine(a.engine, df["text"])

    if a.query:
        print(f"\nRequête : {a.query}")
        show(top_k(engine, df, a.query, a.k))

    if a.ticket:
        row = df[df["_key"] == a.ticket]
        if row.empty:
            sys.exit(f"Ticket {a.ticket} introuvable")
        print(f"\nTickets proches de {a.ticket} : {row['_title'].iloc[0][:100]}")
        show(top_k(engine, df, row["text"].iloc[0], a.k, exclude_key=a.ticket))

    if a.export:
        export_matches(engine, df, cols, a.export, a.k, older_only=not a.all_ages, min_score=a.min_score)

    if a.eval:
        q = pd.read_csv(a.eval)
        if a.compare:
            print(f"\n{'Moteur':<12}{'Top-1':>8}{'Top-5':>8}{'MRR':>8}   ({len(q)} requêtes)")
            for kind in ("keywords", "tfidf", "embeddings"):
                eng = build_engine(kind, df["text"], quiet=True)
                if kind == "embeddings" and eng.name != "embeddings":
                    print(f"{'embeddings':<12}  (non disponible : paquet ou modèle absent)")
                    continue
                m = evaluate(eng, df, q, verbose=False)
                print(f"{eng.name:<12}{m['top1']:>8.0%}{m['top5']:>8.0%}{m['mrr']:>8.2f}")
        else:
            print()
            m = evaluate(engine, df, q)
            print(f"\nTop-1 : {m['top1']:.0%} | Top-5 : {m['top5']:.0%} | MRR : {m['mrr']:.2f}  ({m['n']} requêtes)")

    if not (a.query or a.ticket or a.eval or a.export):
        print("\nMode interactif (ligne vide pour quitter)")
        while True:
            qq = input("Requête> ").strip()
            if not qq:
                break
            show(top_k(engine, df, qq, a.k))


if __name__ == "__main__":
    main()
