"""Pack de données FICTIVES pour travailler à deux sur tous les chantiers, sans accès à Jira.
Format des tickets = celui de l'export réel (16 colonnes + une colonne Description), 2 programmes.
Tout est inventé : aucune donnée SAGEMCOM.

Fichiers produits dans data/ :
  MOCK_AVTV.csv, MOCK_BBTV.csv   un fichier par programme (comme Bug Matcher : un projet par fichier)
  MOCK_ALL.csv                   les deux ensemble (analyse inter-programmes)
  MOCK_tests.csv                 tests fonctionnels existants, liés à certains bugs
  MOCK_groundtruth.csv           réponses attendues : scénario, catégorie, module, action, précondition...
  MOCK_coverage_gaps.csv         lacunes de couverture connues (scénario x programme)
et queries_mock.csv              requêtes d'évaluation (réussite = un ticket du bon scénario dans le top-k)
"""
import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from generate_synthetic import SCENARIOS, make

# module, action utilisateur, précondition, configuration, condition d'erreur, fonctionnalité, catégorie
EXTRA = {
    "hdmi_resume": ("HDMI output", "unplug and replug the HDMI cable", "STB booted and playing a live channel", "HDMI output mode auto, HDCP 2.2", "no video after reconnection", "video playback", "Functional defect"),
    "wifi_forget": ("Network settings", "forget the Wi-Fi network then reboot", "STB connected to a Wi-Fi network", "Wi-Fi 5 GHz, auto-connect enabled", "STB reconnects to the forgotten network", "network management", "Functional defect"),
    "ott_pause": ("OTT player", "press OK on the RCU to pause", "OTT content is playing", "trick mode enabled", "audio and video not decoded after pause", "trick modes", "Functional defect"),
    "audio_preset": ("Audio settings", "open the audio profile preset", "several applications installed", "audio profile preset menu", "no default option selected", "audio profile", "User interface issue"),
    "standby_wake": ("Power management", "wake up the STB from standby with the RCU", "STB in standby for 10 minutes", "deep standby mode", "black screen or slow wake up", "power modes", "Performance issue"),
    "subtitles": ("Subtitles", "change the subtitle style during playback", "content with subtitles is playing", "subtitle size and font", "style not applied", "subtitle display", "User interface issue"),
    "parental": ("Parental control", "zap to a restricted channel", "parental control enabled with a PIN", "age rating 12+", "PIN not requested or wrong PIN accepted", "access restriction", "Security vulnerability"),
    "bluetooth_rcu": ("Bluetooth RCU", "reboot the STB", "RCU paired over Bluetooth", "Bluetooth pairing enabled", "pairing lost or keys unresponsive", "remote control", "Integration defect"),
    "energy_saving": ("Energy saving", "leave the STB idle", "energy saving timeout set to 15 minutes", "energy saver enabled", "STB does not go to standby", "energy saving", "Functional defect"),
    "translation": ("Localization", "open the settings menu in German", "menu language set to German", "language de", "untranslated or wrongly translated label", "menu localization", "User interface issue"),
    "accessibility": ("Accessibility", "increase the text scaling", "accessibility menu available", "text scaling 150 percent", "scaling or bold text not applied", "text display", "User interface issue"),
    "multicast_live": ("Live TV multicast", "zap between multicast channels", "STB on a managed IPTV network", "multicast streaming", "video freeze or slow zapping", "live zapping", "Performance issue"),
    "cleardata": ("System settings", "run a factory reset or clear the data of an app", "user data and Wi-Fi credentials stored", "factory reset", "data not removed or crash", "data reset", "Security vulnerability"),
    "crash_boot": ("Boot sequence", "reboot after a firmware upgrade", "firmware upgrade completed", "latest firmware", "crash, boot loop or freeze", "system boot", "Regression defect"),
}
ONLY_AVTV = {"bluetooth_rcu"}
ONLY_BBTV = {"multicast_live", "cleardata"}
NO_TEST = {"energy_saving", "translation", "accessibility"}  # scénarios sans aucun test : lacunes connues
FREQ = ["Reproduced 3 times out of 3.", "Intermittent, about 1 time out of 5.", "Seen once during validation.", "Reported by the customer on several boxes."]


def description(sc, fixver):
    module, action, pre, config, err, func, _ = EXTRA[sc]
    ver = fixver if fixver else "not specified"
    return (f"Preconditions: {pre}. Steps to reproduce: 1. Boot the STB. 2. {action}. "
            f"Expected result: {func} works normally. Actual result: {err}. "
            f"Configuration: {config}. Firmware: {ver}. {random.choice(FREQ)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400, help="nombre total de tickets (deux programmes)")
    ap.add_argument("--profile", help="profil statistique (make_profile.py), facultatif")
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--queries-out", default="queries_mock.csv")
    a = ap.parse_args()
    base = json.load(open(a.profile, encoding="utf-8")) if a.profile else {}
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    all_sc = list(SCENARIOS)
    plan = {"AVTV": ([s for s in all_sc if s not in ONLY_BBTV], int(a.n * 0.6), 7000, 12000, 42),
            "BBTV": ([s for s in all_sc if s not in ONLY_AVTV], a.n - int(a.n * 0.6), 3000, 20000, 43)}
    frames, truths = [], []
    for prog, (scs, n, key0, vt0, seed) in plan.items():
        prof = dict(base)
        prof.update({"key_prefix": prog, "key_range": [key0], "vt_start": vt0})
        df, truth = make(n, seed=seed, profile=prof, scenario_names=scs)
        random.seed(seed + 100)
        df["Description"] = [description(sc, fv) for sc, fv in zip(truth.scenario, df["Fix Version/s"])]
        # liens parent -> enfant (8 %) entre tickets du même scénario et du même programme
        seen = {}
        for i, (k, sc) in enumerate(zip(truth.Key, truth.scenario)):
            if sc in seen and random.random() < 0.08:
                df.loc[i, "Parent key"] = random.choice(seen[sc])
            seen.setdefault(sc, []).append(k)
        truth["Program"] = prog
        frames.append(df)
        truths.append(truth)
        df.to_csv(out / f"MOCK_{prog}.csv", index=False)
    allp = pd.concat(frames, ignore_index=True)
    allp.to_csv(out / "MOCK_ALL.csv", index=False)
    gt = pd.concat(truths, ignore_index=True)
    shared = set(gt[gt.Program == "AVTV"].scenario) & set(gt[gt.Program == "BBTV"].scenario)
    for j, name in enumerate(["module", "user_action", "precondition", "configuration", "error_condition", "functionality", "category"]):
        gt[name] = gt.scenario.map(lambda s: EXTRA[s][j])
    gt["in_both_programs"] = gt.scenario.isin(shared)
    gt.to_csv(out / "MOCK_groundtruth.csv", index=False)

    # tests existants, liés à une partie des bugs
    random.seed(7)
    tests, n_t = [], 1000
    for sc in all_sc:
        if sc in NO_TEST:
            continue
        progs = [p for p in plan if sc in plan[p][0]]
        module, action, pre, config, err, func, _ = EXTRA[sc]
        for j in range(2):
            tp = [p for p in progs if random.random() < (0.9 if p == progs[0] else 0.35)] or [progs[0]]
            keys = list(gt[(gt.scenario == sc) & (gt.Program.isin(tp))].Key)
            linked = random.sample(keys, max(1, int(len(keys) * random.uniform(0.15, 0.45))))
            n_t += 1
            tests.append({
                "Test ID": f"TC-{n_t}",
                "Title": f"Verify {func}: {action}" if j == 0 else f"Check the absence of: {err}",
                "Module": module,
                "Programs": "|".join(tp),
                "Preconditions": pre,
                "Steps": f"1. {pre}. 2. {action}. 3. Observe the {func}.",
                "Expected result": f"The {func} behaves as expected, without: {err}.",
                "Linked bugs": "|".join(linked),
            })
    tdf = pd.DataFrame(tests)
    tdf.to_csv(out / "MOCK_tests.csv", index=False)

    gaps = []
    for prog, (scs, *_r) in plan.items():
        for sc in scs:
            nb = int(((gt.scenario == sc) & (gt.Program == prog)).sum())
            covering = tdf[(tdf.Module == EXTRA[sc][0]) & tdf.Programs.str.contains(prog)] if len(tdf) else tdf
            gaps.append({"scenario": sc, "Program": prog, "n_bugs": nb, "n_tests": len(covering),
                         "gap": len(covering) == 0})
    pd.DataFrame(gaps).to_csv(out / "MOCK_coverage_gaps.csv", index=False)

    q = []
    for sc, (_, _, qs) in SCENARIOS.items():
        keys = "|".join(gt[gt.scenario == sc].Key)
        q += [(t, keys) for t in qs]
    pd.DataFrame(q, columns=["query", "expected_key"]).to_csv(a.queries_out, index=False)

    g = pd.DataFrame(gaps)
    print(f"{len(allp)} tickets FICTIFS ({allp.Key.str[:4].value_counts().to_dict()}), {len(tdf)} tests, "
          f"{int(g.gap.sum())} lacunes de couverture connues, {len(shared)} scénarios communs aux deux programmes")
    print(f"Fichiers dans {out}/ : MOCK_AVTV, MOCK_BBTV, MOCK_ALL, MOCK_tests, MOCK_groundtruth, MOCK_coverage_gaps ; requêtes : {a.queries_out}")


if __name__ == "__main__":
    main()
