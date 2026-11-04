"""Génère de FAUX tickets au même format que input_sample.csv (16 colonnes,
titres '[VTVAS-n] [étiquettes] texte', dates m/j/aaaa), pour tester le code en volume.
Aucune donnée SAGEMCOM : les scénarios sont inventés à partir du vocabulaire général des STB.

Produit aussi :
  - data/SYNTHETIC_groundtruth.csv : le scénario de chaque ticket
  - queries_synthetic.csv          : requêtes de test (query,expected_key avec clés séparées par |)
"""
import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SCENARIOS = {
    "hdmi_resume": (["HDMI", "Player"], [
        "Playback does not resume after removing and reinserting the HDMI cable post boot",
        "No picture after the HDMI cable is unplugged and plugged back in",
        "HDMI hot plug: video not restored when the cable is reconnected",
        "Black screen when HDMI cable is reinserted during playback"],
        ["video does not come back after replugging the HDMI cable", "TV shows nothing when the cable is connected again"]),
    "wifi_forget": (["Network", "Settings"], [
        "The STB reconnects to the previous network upon booting, even after the network has been forgotten",
        "Forgotten Wi-Fi network is automatically joined again after reboot",
        "Saved wireless network cannot be removed, STB reconnects after restart",
        "Forget network option has no effect after standby wake up"],
        ["wifi network still used after being forgotten", "STB joins an old access point after restart"]),
    "ott_pause": (["Player", "OTT", "Trick mode"], [
        "Audio and video are not decoded when user presses the RCU OK key for pause content",
        "Pressing OK on remote during OTT pause freezes the player",
        "Trick mode pause then resume gives no audio nor video",
        "OTT content stuck after pause with the remote OK key"],
        ["pause with the remote then no sound and no image", "OTT player frozen after pressing OK to pause"]),
    "audio_preset": (["Audio", "Settings"], [
        "Some of the applications do not have a default option selected in the audio profile preset",
        "Audio profile preset shows no selected value for several apps",
        "Default audio profile missing in application settings",
        "No default choice highlighted in the audio preset menu"],
        ["audio profile has no default selection", "nothing selected by default in sound presets"]),
    "standby_wake": (["Power", "Boot"], [
        "Black screen after waking up from standby",
        "STB does not wake from standby with the RCU power key",
        "Resume from standby takes more than 30 seconds",
        "Video missing after standby exit"],
        ["no image when the box leaves standby", "box slow to turn back on from sleep"]),
    "subtitles": (["Player", "Settings"], [
        "Subtitle style settings are not applied during playback",
        "Subtitle font size changes are ignored in the player",
        "Caption style is not saved after reboot",
        "Subtitle language reset to default after channel change"],
        ["subtitle appearance options do nothing", "captions font not kept after restart"]),
    "parental": (["Parental", "Settings"], [
        "Parental control PIN not requested for restricted channel",
        "Parental lock bypassed after reboot",
        "Wrong PIN accepted when parental control is enabled",
        "Restricted content playable without PIN in live"],
        ["child lock not asking for the code", "restricted channel opens without PIN"]),
    "bluetooth_rcu": (["RCU", "Bluetooth"], [
        "RCU Bluetooth pairing lost after reboot",
        "Remote control must be paired again after standby",
        "Bluetooth remote not detected at first boot",
        "RCU keys unresponsive after Bluetooth reconnect"],
        ["remote control has to be paired again after restart", "bluetooth remote unresponsive after reconnection"]),
    "energy_saving": (["Power", "Settings"], [
        "Energy saving mode does not switch the STB to standby after timeout",
        "Auto standby timer ignored in power mode settings",
        "Power consumption too high in standby mode",
        "Energy saver setting reset after factory reset"],
        ["box never goes to sleep automatically", "power saving timer not respected"]),
    "translation": (["UI", "Translation"], [
        "Menu label wrongly translated in German",
        "Missing translation for the settings menu in French",
        "Untranslated string displayed in the accessibility menu",
        "Localization issue in the parental control screen"],
        ["text shown in English instead of German", "wrong translation in the menu"]),
    "accessibility": (["Accessibility", "UI"], [
        "Text scaling is not applied in the settings menu",
        "Bold text option has no effect on subtitles",
        "Large text overlaps buttons in the home screen",
        "Accessibility font size resets after update"],
        ["bigger font option does not change the screen", "text size setting lost after upgrade"]),
    "multicast_live": (["Live", "Mcast"], [
        "Live channel zapping freezes video on multicast streams",
        "Channel change stuck on black screen for mcast channels",
        "Multicast stream lost after network reconnection",
        "Zapping between multicast channels takes more than 5 seconds"],
        ["switching live channels freezes the picture", "slow zapping on multicast TV"]),
    "cleardata": (["Settings", "Cleardata"], [
        "Factory reset does not remove user data",
        "Clear data leaves Wi-Fi credentials stored",
        "STB boots into previous state after factory reset",
        "Clear data of an app crashes the STB"],
        ["reset to factory leaves personal data", "wiping app data makes the box crash"]),
    "crash_boot": (["Boot", "Crash"], [
        "STB crashes during boot animation",
        "Boot loop after firmware upgrade",
        "Random reboot while playing OTT content",
        "System freeze at boot screen"],
        ["box restarts by itself during streaming", "device stuck at startup logo"]),
}
PLATFORMS = ["", "[Gen3]", "[Gen4]", "[Gen4][DE-Prod]", "[AVSB]"]
COMPONENTS = ["UI", "Player", "Network", "Audio", "Settings"]
SPRINTS = ["STB37X Android 14 Sprint 45.2", "M378 Sprint 46", "AVSB3930 Sprint 45"]
FIXVER = ["[FW][M378] 4.2404.62", "[FW][AVSB] 2.2405.18", "[FW][STB37X] 5.2406.10"]
PEOPLE = ["Engineer A", "Engineer B", "Engineer C", "Engineer D"]


def draw(profile, field, values, weights):
    """Tire une valeur selon le profil réel s'il existe, sinon selon les valeurs par défaut."""
    cat = ((profile or {}).get("categorical") or {}).get(field)
    if cat is None:
        return random.choices(values, weights)[0]
    if random.random() < cat.get("empty_rate", 0) or not cat.get("values"):
        return ""
    return random.choices(cat["values"], cat["weights"])[0]


def profile_tags(profile):
    t = (profile or {}).get("tags") or {}
    if not t.get("values"):
        return None
    dist = t.get("tags_per_title") or {"0": 0.2, "1": 0.5, "2": 0.3}
    n = int(random.choices(list(dist), [float(v) for v in dist.values()])[0])
    n = min(n, len(t["values"]))
    chosen = []
    while len(chosen) < n:
        x = random.choices(t["values"], t["weights"])[0]
        if x not in chosen:
            chosen.append(x)
    return "".join(f"[{x}]" for x in chosen)


def fmt(d):
    return f"{d.month}/{d.day}/{d.year}"


def make(n, seed=42, profile=None, scenario_names=None):
    random.seed(seed)
    names = list(scenario_names or SCENARIOS)
    plan = [names[i % len(names)] for i in range(n)]
    random.shuffle(plan)
    rows, truth = [], []
    prefix = (profile or {}).get("key_prefix", "AVTV")
    key = ((profile or {}).get("key_range") or [7000])[0]
    vt = (profile or {}).get("vt_start", 12000)
    dates = (profile or {}).get("dates") or {}
    start = date.fromisoformat(dates["min"]) if dates.get("min") else date(2025, 1, 2)
    end = date.fromisoformat(dates["max"]) if dates.get("max") else start + timedelta(days=280)
    span = max(1, (end - start).days)
    delta = dates.get("update_delta_days")
    for i, sc in enumerate(plan):
        tags, titles, _ = SCENARIOS[sc]
        key += random.randint(1, 4)
        vt += random.randint(1, 3)
        created = start + timedelta(days=int(i * span / n) + random.randint(0, 2))
        d_up = int(random.triangular(delta["p10"], max(delta["p90"], delta["p10"] + 1), delta["p50"])) if delta else random.randint(5, 200)
        updated = created + timedelta(days=d_up)
        ptags = profile_tags(profile)
        if ptags is not None:
            pre = f"[VTVAS-{vt}] {ptags}".strip()
        else:
            t_used = "".join(f"[{t}]" for t in random.sample(tags, random.randint(0, min(2, len(tags)))))
            plat = random.choice(PLATFORMS)
            pre = " ".join(x for x in (f"[VTVAS-{vt}]", plat + t_used if (plat or t_used) else "") if x)
        status = draw(profile, "status", ["CLOSED", "OPEN", "IN PROGRESS"], [0.8, 0.12, 0.08])
        if "resolution" in ((profile or {}).get("categorical") or {}):
            res = draw(profile, "resolution", [], [])
        else:
            res = random.choice(["FIXED", "FIXED", "WONTFIX", "DUPLICATE"]) if status == "CLOSED" else ""
        rows.append({
            "Key": f"{prefix}-{key}",
            "PR reference in Customer Database": f"{prefix}:VTVAS-{vt}",
            "Severity": draw(profile, "severity", ["Major", "Critical", "Minor"], [0.7, 0.1, 0.2]),
            "Priority": draw(profile, "priority", ["Low", "Medium", "High"], [0.5, 0.25, 0.25]),
            "Summary": f"{pre} {random.choice(titles)}",
            "Status": status,
            "Resolution": res,
            "Component/s": draw(profile, "component", ["ToBeDefined"] + COMPONENTS, [0.7] + [0.06] * len(COMPONENTS)),
            "Labels": "",
            "Whiteboard": "",
            "Assignee": random.choice(PEOPLE),
            "Sprint": draw(profile, "sprint", SPRINTS + [""], [0.17, 0.17, 0.16, 0.5]),
            "Fix Version/s": draw(profile, "version", FIXVER + [""], [0.17, 0.17, 0.16, 0.5]),
            "Created": fmt(created),
            "Updated": fmt(updated),
            "Parent key": "",
        })
        truth.append((f"{prefix}-{key}", sc))
    return pd.DataFrame(rows), pd.DataFrame(truth, columns=["Key", "scenario"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", default="data/SYNTHETIC_input_like.csv")
    ap.add_argument("--queries-out", default="queries_synthetic.csv")
    ap.add_argument("--profile", help="profil statistique (src/make_profile.py) pour imiter les proportions du vrai fichier")
    a = ap.parse_args()
    profile = json.load(open(a.profile, encoding="utf-8")) if a.profile else None
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df, truth = make(a.n, profile=profile)
    df.to_csv(a.out, index=False)
    truth.to_csv(Path(a.out).parent / "SYNTHETIC_groundtruth.csv", index=False)
    q = []
    for sc, (_, _, queries) in SCENARIOS.items():
        keys = "|".join(truth[truth.scenario == sc].Key)
        for text in queries:
            q.append((text, keys))
    pd.DataFrame(q, columns=["query", "expected_key"]).to_csv(a.queries_out, index=False)
    print(f"{len(df)} tickets SYNTHÉTIQUES -> {a.out}" + (f" (proportions du profil {a.profile})" if profile else ""))
    print(f"{len(q)} requêtes de test -> {a.queries_out} (réussite = un ticket du bon scénario dans le top-k)")
