from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAIRS_FILE = PROJECT_ROOT / "data" / "cross_program_pairs.csv"
GROUNDTRUTH_FILE = PROJECT_ROOT / "data" / "MOCK_groundtruth.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "cross_program_labeled_pairs.csv"


def normalize_text(series):
    """Normalise du texte pour comparer les scénarios sans tenir compte
    des espaces autour et des majuscules/minuscules."""
    return series.astype("string").str.strip().str.casefold()


def main():
    if not PAIRS_FILE.exists():
        raise FileNotFoundError(
            f"Fichier de paires introuvable : {PAIRS_FILE}"
        )

    if not GROUNDTRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Fichier ground truth introuvable : {GROUNDTRUTH_FILE}"
        )

    pairs = pd.read_csv(PAIRS_FILE)
    truth = pd.read_csv(GROUNDTRUTH_FILE)

    required_pair_columns = {"Key_avtv", "Key_bbtv"}
    required_truth_columns = {"Key", "Program", "scenario"}

    missing_pairs = required_pair_columns - set(pairs.columns)
    missing_truth = required_truth_columns - set(truth.columns)

    if missing_pairs:
        raise ValueError(
            f"Colonnes manquantes dans {PAIRS_FILE.name} : "
            f"{sorted(missing_pairs)}"
        )

    if missing_truth:
        raise ValueError(
            f"Colonnes manquantes dans {GROUNDTRUTH_FILE.name} : "
            f"{sorted(missing_truth)}"
        )

    # Nettoyer les clés et les noms de programme.
    pairs["Key_avtv"] = pairs["Key_avtv"].astype("string").str.strip()
    pairs["Key_bbtv"] = pairs["Key_bbtv"].astype("string").str.strip()

    truth["Key"] = truth["Key"].astype("string").str.strip()
    truth["Program"] = truth["Program"].astype("string").str.strip().str.upper()
    truth["scenario"] = truth["scenario"].astype("string").str.strip()

    # Une clé doit désigner un seul ticket dans la ground truth.
    duplicated_keys = truth.loc[truth["Key"].duplicated(), "Key"].unique()
    if len(duplicated_keys):
        raise ValueError(
            "La ground truth contient des clés de ticket en double : "
            f"{duplicated_keys[:10].tolist()}"
        )

    avtv = truth[truth["Program"] == "AVTV"]
    bbtv = truth[truth["Program"] == "BBTV"]

    if avtv.empty or bbtv.empty:
        raise ValueError(
            "La ground truth doit contenir des tickets AVTV et BBTV."
        )

    # Associer chaque clé à son scénario.
    avtv_scenarios = avtv.set_index("Key")["scenario"]
    bbtv_scenarios = bbtv.set_index("Key")["scenario"]

    pairs["scenario_avtv"] = pairs["Key_avtv"].map(avtv_scenarios)
    pairs["scenario_bbtv"] = pairs["Key_bbtv"].map(bbtv_scenarios)

    # Vérifier que chaque ticket des paires existe dans la ground truth.
    missing_avtv = pairs.loc[
        pairs["scenario_avtv"].isna(), "Key_avtv"
    ].unique()

    missing_bbtv = pairs.loc[
        pairs["scenario_bbtv"].isna(), "Key_bbtv"
    ].unique()

    if len(missing_avtv) or len(missing_bbtv):
        raise ValueError(
            "Certaines clés des paires sont absentes de la ground truth.\n"
            f"AVTV absentes (exemples) : {missing_avtv[:10].tolist()}\n"
            f"BBTV absentes (exemples) : {missing_bbtv[:10].tolist()}"
        )

    # Dans le jeu simulé, un même scénario signifie une paire positive.
    same_scenario = (
        normalize_text(pairs["scenario_avtv"])
        == normalize_text(pairs["scenario_bbtv"])
    )

    pairs["is_match"] = same_scenario.astype(int)
    pairs["label_source"] = "same_scenario_in_MOCK_groundtruth"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUTPUT_FILE, index=False)

    positives = int(pairs["is_match"].sum())
    negatives = len(pairs) - positives

    print("Étiquetage des paires terminé")
    print(f"Paires analysées : {len(pairs)}")
    print(f"Paires positives : {positives}")
    print(f"Paires négatives : {negatives}")
    print(f"Fichier créé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()