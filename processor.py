import os
import subprocess
import json
import pandas as pd
import shutil

def run_inspector(replay_dir: str, result_dir: str, exe_path: str):
    os.makedirs(result_dir, exist_ok=True)
    replay_files = [
        f for f in os.listdir(replay_dir)
        if f.endswith(".tbreplay") or f.endswith(".wotbreplay")
    ][:100]

    for file in replay_files:
        replay_path = os.path.join(replay_dir, file)
        output_path = os.path.join(result_dir, file.rsplit(".", 1)[0] + ".json")

        with open(output_path, "w", encoding="utf-8") as out:
            subprocess.run(
                [exe_path, "battle-results", replay_path],
                stdout=out,
                stderr=subprocess.DEVNULL,
                check=True
            )

def run_redactor(result_dir: str, excel_dir: str):
    rows = []
    for fname in os.listdir(result_dir):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(result_dir, fname), encoding="utf-8") as f:
            data = json.load(f)

        id_to_name = {
            p["account_id"]: {
                "nickname": p["info"]["nickname"],
                "team": "Союзники" if p["info"]["team"] == 1 else "Противники"
            }
            for p in data["players"]
        }

        for r in data["player_results"]:
            info = r["info"]
            acc_id = info["account_id"]
            p = id_to_name.get(acc_id, {"nickname": "Unknown", "team": "?"})
            rows.append({
                "replay": fname,
                "nickname": p["nickname"],
                "team": p["team"],
                "damage": info["damage_dealt"],
                "kills": info["n_enemies_destroyed"],
                "touch": info["n_enemies_damaged"],
                "shots": info["n_shots"],
                "hits": info["n_hits_dealt"],
                "pens": info["n_penetrations_dealt"],
                "assist": info["damage_assisted_1"] + info["damage_assisted_2"],
                "blocked": info["damage_blocked"],
                "points earned": info["victory_points_earned"],
                "points seized": info["victory_points_seized"]
            })

    df = pd.DataFrame(rows)
    os.makedirs(excel_dir, exist_ok=True)
    df.to_excel(os.path.join(excel_dir, "combined.xlsx"), index=False)

def run_calculator(excel_dir: str):
    df = pd.read_excel(os.path.join(excel_dir, "combined.xlsx"))
    agg = df.groupby("nickname").agg({
        "replay": "count",
        "damage": "mean",
        "kills": "mean",
        "assist": "mean",
        "blocked": "mean",
        "shots": "mean",
        "hits": "mean",
        "pens": "mean",
        "touch": "mean",
        "points earned": "mean",
        "points seized": "mean",
    }).rename(columns={"replay": "battles"})
    agg = agg.round(1).sort_values("damage", ascending=False)
    result_path = os.path.join(excel_dir, "averages.xlsx")
    agg.to_excel(result_path)
    return result_path
