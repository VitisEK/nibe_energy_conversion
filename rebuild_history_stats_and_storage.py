#!/usr/bin/env python3
import sqlite3
import json
import glob
import os
import sys
import math
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone

# =========================
# Defaults (edit if needed)
# =========================
DEFAULT_DB_PATH = "/config/home-assistant_v2.db"
DEFAULT_STORAGE_DIR = "/config/.storage"

SHORT_TERM_DAYS_DEFAULT = 10
UNIT_DEFAULT = "kWh"
SOURCE_TAG_DEFAULT = "rebuild_wizard"

# Default INPUTS (hourly "past hour" sensors)
DEFAULT_INPUTS = {
    "prod_cooling": "sensor.energy_log_energy_produced_for_cooling_during_past_hour_32290",
    "prod_heating": "sensor.energy_log_energy_produced_for_heat_during_past_hour_32284",
    "prod_hot_water": "sensor.energy_log_energy_produced_for_hot_water_during_past_hour_32286",
    "aux_heat": "sensor.energy_log_energy_used_by_additional_heater_for_heat_during_past_hour_32300",
    "aux_hot_water": "sensor.energy_log_energy_used_by_additional_heater_for_hot_water_during_past_hour_32302",
    "used_cooling": "sensor.energy_log_energy_used_for_cooling_during_past_hour_32298",
    "used_heating": "sensor.energy_log_energy_used_for_heat_during_past_hour_32292",
    "used_hot_water": "sensor.energy_log_energy_used_for_hot_water_during_past_hour_32294",
}

# Default OUTPUTS (cumulative totals)
DEFAULT_OUTPUTS = {
    "dohrev_topeni": "sensor.energy_conversion_dohrev_topeni_kwh",
    "dohrev_tuv": "sensor.energy_conversion_dohrev_tuv_kwh",
    "spotreba_energie_celkem": "sensor.energy_conversion_spotreba_energie_celkem_kwh",
    "spotreba_chlazeni": "sensor.energy_conversion_spotreba_chlazeni_kwh",
    "spotreba_topeni": "sensor.energy_conversion_spotreba_topeni_kwh",
    "spotreba_tuv": "sensor.energy_conversion_spotreba_tuv_kwh",
    "vyrobena_energie_celkem": "sensor.energy_conversion_vyrobena_energie_celkem_kwh",
    "vyrobeno_chlazeni": "sensor.energy_conversion_vyrobeno_chlazeni_kwh",
    "vyrobeno_topeni": "sensor.energy_conversion_vyrobeno_topeni_kwh",
    "vyrobeno_tuv": "sensor.energy_conversion_vyrobeno_tuv_kwh",
}

# Storage totals keys used by your integration
STORAGE_TOTAL_KEYS = [
    "prod_cooling_total",
    "prod_heating_total",
    "prod_hot_water_total",
    "used_cooling_total",
    "used_heating_total",
    "used_hot_water_total",
    "aux_used_heating_total",
    "aux_used_hot_water_total",
]

# =========================
# Wizard helpers
# =========================
def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ask_yes_no(question: str) -> bool:
    while True:
        s = input(f"{question} (Y/N): ").strip().lower()
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Please type Y or N.")

def ask_path_until_exists(prompt_text: str, must_be_file: bool = True) -> str:
    while True:
        p = input(prompt_text).strip()
        if not p:
            print("Path cannot be empty.")
            continue
        if must_be_file:
            if os.path.isfile(p):
                return p
            print("File does not exist. Please try again.")
        else:
            if os.path.isdir(p):
                return p
            print("Directory does not exist. Please try again.")

def ask_int(prompt_text: str, default: int) -> int:
    while True:
        s = input(f"{prompt_text} [{default}]: ").strip()
        if not s:
            return default
        try:
            v = int(s)
            if v >= 0:
                return v
        except:
            pass
        print("Please enter a non-negative integer.")

def ask_str(prompt_text: str, default: str) -> str:
    s = input(f"{prompt_text} [{default}]: ").strip()
    return s if s else default

def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")

def parse_num(v):
    if v is None:
        return None
    try:
        f = float(v)
        if math.isfinite(f):
            return f
    except:
        return None
    return None

def table_cols(cur, table: str):
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]

def floor_to(ts: float, step_s: int) -> int:
    return int(ts // step_s) * step_s

def value_from_stats_row(row):
    for k in ("mean", "state", "sum"):
        if k in row.keys():
            v = parse_num(row[k])
            if v is not None:
                return float(v)
    return None

def run_cmd(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print("Command failed:", " ".join(cmd))
        if p.stdout:
            print("STDOUT:\n", p.stdout)
        if p.stderr:
            print("STDERR:\n", p.stderr)
        raise SystemExit(p.returncode)

def backup_file(src_path: str) -> str:
    src = Path(src_path)
    dst = src.with_name(src.name + f".bak_{now_stamp()}")
    shutil.copy2(src, dst)
    return str(dst)

def backup_dir(src_dir: str) -> str:
    src = Path(src_dir)
    dst = src.parent / (src.name + f".bak_{now_stamp()}")
    shutil.copytree(src, dst, dirs_exist_ok=False)
    return str(dst)

# =========================
# DB validation helpers
# =========================
def statistic_id_exists(cur, stat_id: str) -> bool:
    cur.execute("SELECT 1 FROM statistics_meta WHERE statistic_id = ? LIMIT 1", (stat_id,))
    return cur.fetchone() is not None

# =========================
# Storage discovery
# =========================
def storage_candidates(storage_dir: str):
    cands = []
    for p in glob.glob(os.path.join(storage_dir, "*")):
        try:
            if os.path.isdir(p):
                continue
            txt = Path(p).read_text(encoding="utf-8")
            obj = json.loads(txt)
            totals = obj.get("data", {}).get("totals", {})
            if not isinstance(totals, dict):
                continue
            hits = sum(1 for k in STORAGE_TOTAL_KEYS if k in totals)
            if hits >= 6:
                cands.append((p, obj, hits))
        except:
            continue
    cands.sort(key=lambda x: x[2], reverse=True)
    return cands

def pick_storage_file(storage_dir: str) -> str:
    cands = storage_candidates(storage_dir)
    if cands:
        print("\nFound these storage candidates:\n")
        for i, (p, obj, hits) in enumerate(cands, 1):
            lp = obj.get("data", {}).get("last_processed", "n/a")
            key = obj.get("key", Path(p).name)
            print(f"  {i}) {Path(p).name}  | key={key} | last_processed={lp} | totals_match={hits}/8")
        print("")
        pick = cands[0][0]
        if ask_yes_no(f"Use this storage file? {pick}"):
            return pick

    while True:
        manual = ask_path_until_exists("Enter full path to the storage file: ", must_be_file=True)
        try:
            obj = json.loads(Path(manual).read_text(encoding="utf-8"))
            totals = obj.get("data", {}).get("totals", {})
            if not isinstance(totals, dict):
                print("File exists but does not contain data.totals dict. Please choose another file.")
                continue
            return manual
        except:
            print("File exists but is not valid JSON. Please choose another file.")
            continue

# =========================
# Main rebuild logic
# =========================
def resolve_meta_ids(cur, stat_id: str) -> list[int]:
    cur.execute("SELECT id FROM statistics_meta WHERE statistic_id = ?", (stat_id,))
    return [int(r[0]) for r in cur.fetchall()]

def delete_all_for_statistic_id(cur, stat_id: str, have_sts: bool):
    meta_ids = resolve_meta_ids(cur, stat_id)
    if not meta_ids:
        return (0, 0, 0)
    cur.execute(f"DELETE FROM statistics WHERE metadata_id IN ({','.join(['?']*len(meta_ids))})", tuple(meta_ids))
    n_stats = cur.rowcount
    n_sts = 0
    if have_sts:
        cur.execute(f"DELETE FROM statistics_short_term WHERE metadata_id IN ({','.join(['?']*len(meta_ids))})", tuple(meta_ids))
        n_sts = cur.rowcount
    cur.execute(f"DELETE FROM statistics_meta WHERE id IN ({','.join(['?']*len(meta_ids))})", tuple(meta_ids))
    n_meta = cur.rowcount
    return (n_stats, n_sts, n_meta)

def create_meta(cur, meta_cols, stat_id: str, unit: str, source_tag: str, name: str):
    base = {
        "statistic_id": stat_id,
        "source": source_tag,
        "unit_of_measurement": unit,
        "has_mean": 0,
        "has_sum": 1,
        "name": name or stat_id,
    }
    keys = [k for k in base.keys() if k in meta_cols]
    q = f"INSERT INTO statistics_meta ({','.join(keys)}) VALUES ({','.join(['?']*len(keys))})"
    cur.execute(q, tuple(base[k] for k in keys))
    return int(cur.lastrowid)

def build_insert(cur, table: str, tgt_meta_id: int, now_iso: str, now_ts: float):
    cols = table_cols(cur, table)
    base_row = {}
    if "created" in cols: base_row["created"] = now_iso
    if "created_ts" in cols: base_row["created_ts"] = now_ts
    if "metadata_id" in cols: base_row["metadata_id"] = tgt_meta_id
    if "mean" in cols: base_row["mean"] = None
    if "min" in cols: base_row["min"] = None
    if "max" in cols: base_row["max"] = None
    if "last_reset" in cols: base_row["last_reset"] = None
    if "last_reset_ts" in cols: base_row["last_reset_ts"] = None
    if "mean_weight" in cols: base_row["mean_weight"] = 0

    needed = [c for c in ["start","start_ts","state","sum"] if c in cols]
    insert_cols = list(base_row.keys()) + needed
    sql = f"INSERT OR REPLACE INTO {table} ({','.join(insert_cols)}) VALUES ({','.join(['?']*len(insert_cols))})"
    return sql, base_row, insert_cols

def insert_point(cur, sql, base_row, cols, start_ts, value):
    row = dict(base_row)
    if "start" in cols: row["start"] = utc_iso(start_ts)
    if "start_ts" in cols: row["start_ts"] = float(start_ts)
    if "state" in cols: row["state"] = float(value)
    if "sum" in cols: row["sum"] = float(value)
    cur.execute(sql, [row.get(c) for c in cols])

def main():
    print("\n=== Home Assistant Statistics Rebuilder Wizard (English) ===\n")

    db_path = ask_str("Database path", DEFAULT_DB_PATH)
    if not os.path.isfile(db_path):
        print("DB file not found.")
        db_path = ask_path_until_exists("Enter full path to the DB file: ", must_be_file=True)

    storage_dir = ask_str("Storage directory", DEFAULT_STORAGE_DIR)
    if not os.path.isdir(storage_dir):
        print(".storage directory not found.")
        storage_dir = ask_path_until_exists("Enter full path to the .storage directory: ", must_be_file=False)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    meta_cols = table_cols(cur, "statistics_meta")
    stats_cols = table_cols(cur, "statistics")
    sts_cols = table_cols(cur, "statistics_short_term")
    have_sts = ("metadata_id" in sts_cols and "start_ts" in sts_cols)

    if not ("metadata_id" in stats_cols and "start_ts" in stats_cols):
        raise SystemExit("DB schema error: 'statistics' table does not contain metadata_id/start_ts columns.")

    # Step 1: Find storage file
    print("\nStep 1/7: Locate storage file\n")
    storage_file = pick_storage_file(storage_dir)
    print(f"Selected storage file: {storage_file}\n")

    # Step 2: Inputs
    print("Step 2/7: Configure INPUT sensors (must exist in DB statistics_meta)\n")
    inputs = {}
    for key, default_id in DEFAULT_INPUTS.items():
        while True:
            use_def = ask_yes_no(f"Input '{key}': use default '{default_id}'?")
            candidate = default_id if use_def else input(f"Enter statistic_id for input '{key}': ").strip()
            if not candidate:
                print("Value cannot be empty.")
                continue
            if statistic_id_exists(cur, candidate):
                inputs[key] = candidate
                print(f"OK: {key} -> {candidate}\n")
                break
            print(f"Not found in DB (statistics_meta): {candidate}. Please try again.\n")

    # Step 3: Outputs
    print("Step 3/7: Configure OUTPUT sensors (must exist in DB statistics_meta)\n")
    outputs = {}
    for key, default_id in DEFAULT_OUTPUTS.items():
        while True:
            use_def = ask_yes_no(f"Output '{key}': use default '{default_id}'?")
            candidate = default_id if use_def else input(f"Enter statistic_id for output '{key}': ").strip()
            if not candidate:
                print("Value cannot be empty.")
                continue
            if statistic_id_exists(cur, candidate):
                outputs[key] = candidate
                print(f"OK: {key} -> {candidate}\n")
                break
            print(f"Not found in DB (statistics_meta): {candidate}. Please try again.\n")

    # Step 4: Confirm start
    print("Step 4/7: Ready to start\n")
    while True:
        if ask_yes_no("Everything validated. Start calculation now?"):
            break
        print("OK, not starting yet. I will ask again.")

    # Step 5: Stop Core confirmation
    print("\nStep 5/7: Stop Home Assistant Core\n")
    while True:
        if ask_yes_no("Stop Home Assistant Core now (ha core stop)?"):
            break
        print("Cannot proceed safely without stopping Core. I will ask again.")

    # Stop Core
    run_cmd(["ha", "core", "stop"])
    print("Home Assistant Core stopped.\n")

    # Step 6: Backups (DB + chosen storage file; optional whole .storage)
    print("Step 6/7: Create backups\n")
    db_bak = backup_file(db_path)
    storage_bak = backup_file(storage_file)
    print(f"DB backup created:       {db_bak}")
    print(f"Storage backup created:  {storage_bak}")

    if ask_yes_no("Also backup the entire .storage directory? (can be large)"):
        storage_dir_bak = backup_dir(storage_dir)
        print(f".storage directory backup created: {storage_dir_bak}")
    print("")

    # Settings
    short_term_days = ask_int("Short-term (5-min) backfill window in days", SHORT_TERM_DAYS_DEFAULT)
    unit = ask_str("Unit of measurement", UNIT_DEFAULT)
    source_tag = ask_str("statistics_meta.source tag", SOURCE_TAG_DEFAULT)

    # Load sources from LTS
    print("\nLoading source long-term statistics (hourly)...\n")
    sel = ["start_ts"]
    if "mean" in stats_cols: sel.append("mean")
    if "state" in stats_cols: sel.append("state")
    if "sum" in stats_cols: sel.append("sum")

    src_points = {}
    all_ts = set()

    for in_key, stat_id in inputs.items():
        cur.execute("SELECT id FROM statistics_meta WHERE statistic_id = ? LIMIT 1", (stat_id,))
        m = cur.fetchone()
        if not m:
            raise SystemExit(f"Unexpected: source disappeared from statistics_meta: {stat_id}")
        mid = int(m["id"])

        cur.execute(f"""
            SELECT {",".join(sel)}
            FROM statistics
            WHERE metadata_id = ?
            ORDER BY start_ts ASC
        """, (mid,))
        rows = cur.fetchall()

        d = {}
        for r in rows:
            ts = parse_num(r["start_ts"])
            v = value_from_stats_row(r)
            if ts is None or v is None:
                continue
            if v < 0:
                continue
            ts = float(ts)
            d[ts] = float(v)
            all_ts.add(ts)

        if len(d) < 2:
            raise SystemExit(f"Not enough usable points for input '{in_key}' ({stat_id}).")
        src_points[in_key] = d
        print(f"Loaded {len(d)} points for {in_key}")

    timeline = sorted(all_ts)
    t_start, t_end = timeline[0], timeline[-1]
    print(f"\nTimeline hours: {len(timeline)} | {utc_iso(t_start)} .. {utc_iso(t_end)}\n")

    def getv(in_key, ts):
        return src_points.get(in_key, {}).get(ts, 0.0)

    # Compute hourly per rules
    out_hourly = {stat_id: {} for stat_id in outputs.values()}

    for ts in timeline:
        prod_cooling = getv("prod_cooling", ts)
        prod_heating = getv("prod_heating", ts)
        prod_hot_water = getv("prod_hot_water", ts)

        aux_heat = getv("aux_heat", ts)
        aux_hot_water = getv("aux_hot_water", ts)

        used_cooling = getv("used_cooling", ts)
        used_heating = getv("used_heating", ts)
        used_hot_water = getv("used_hot_water", ts)

        out_hourly[outputs["dohrev_topeni"]][ts] = aux_heat
        out_hourly[outputs["dohrev_tuv"]][ts] = aux_hot_water

        out_hourly[outputs["spotreba_chlazeni"]][ts] = used_cooling
        out_hourly[outputs["spotreba_topeni"]][ts] = used_heating + aux_heat
        out_hourly[outputs["spotreba_tuv"]][ts] = used_hot_water + aux_hot_water
        out_hourly[outputs["spotreba_energie_celkem"]][ts] = used_cooling + used_heating + used_hot_water + aux_heat + aux_hot_water

        out_hourly[outputs["vyrobeno_chlazeni"]][ts] = prod_cooling
        out_hourly[outputs["vyrobeno_topeni"]][ts] = prod_heating
        out_hourly[outputs["vyrobeno_tuv"]][ts] = prod_hot_water
        out_hourly[outputs["vyrobena_energie_celkem"]][ts] = prod_cooling + prod_heating + prod_hot_water

    # Cumulative points
    out_points = {}
    last_cum = {}
    for stat_id, hourly_map in out_hourly.items():
        cum = 0.0
        pts = []
        for ts in timeline:
            h = float(hourly_map.get(ts, 0.0))
            if h < 0:
                h = 0.0
            cum += h
            pts.append((ts, cum))
        out_points[stat_id] = pts
        last_cum[stat_id] = cum

    # Raw cumulatives WITHOUT aux for storage used_* totals
    raw_used_heating_cum = 0.0
    raw_used_hot_water_cum = 0.0
    for ts in timeline:
        raw_used_heating_cum += max(0.0, getv("used_heating", ts))
        raw_used_hot_water_cum += max(0.0, getv("used_hot_water", ts))

    # Rebuild outputs in DB
    print("\nRebuilding output statistics in DB...\n")
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    now_iso = utc_iso(now_ts)

    for out_key, out_stat_id in outputs.items():
        ds, dsts, dm = delete_all_for_statistic_id(cur, out_stat_id, have_sts)
        tgt_meta_id = create_meta(cur, meta_cols, out_stat_id, unit, source_tag, out_stat_id)

        sql_lts, base_lts, cols_lts = build_insert(cur, "statistics", tgt_meta_id, now_iso, now_ts)
        for ts, v in out_points[out_stat_id]:
            insert_point(cur, sql_lts, base_lts, cols_lts, ts, v)

        sts_count = 0
        if have_sts and short_term_days > 0:
            st_from = max(t_start, t_end - short_term_days * 86400)
            pts2 = [(ts, v) for ts, v in out_points[out_stat_id] if ts >= st_from]
            if pts2:
                sql_sts, base_sts, cols_sts = build_insert(cur, "statistics_short_term", tgt_meta_id, now_iso, now_ts)
                STEP = 300
                t0 = floor_to(st_from, STEP)
                t1 = floor_to(t_end, STEP)
                i = 0
                current_v = pts2[0][1]
                for t_tick in range(t0, t1 + 1, STEP):
                    while i < len(pts2) and pts2[i][0] <= t_tick:
                        current_v = pts2[i][1]
                        i += 1
                    insert_point(cur, sql_sts, base_sts, cols_sts, t_tick, current_v)
                    sts_count += 1

        print(f"OUT {out_key}: deleted stats={ds} sts={dsts} meta={dm} | inserted LTS={len(out_points[out_stat_id])} STS={sts_count}")

    con.commit()

    # Patch storage
    print("\nPatching storage file totals + last_processed...\n")
    storage_path = Path(storage_file)
    obj = json.loads(storage_path.read_text(encoding="utf-8"))
    totals = obj.get("data", {}).get("totals", {})
    if not isinstance(totals, dict):
        raise SystemExit("Storage file does not contain data.totals dict.")

    last_ts = timeline[-1]
    obj["data"]["last_processed"] = utc_iso(last_ts)

    mapping = {
        "prod_cooling_total": outputs["vyrobeno_chlazeni"],
        "prod_heating_total": outputs["vyrobeno_topeni"],
        "prod_hot_water_total": outputs["vyrobeno_tuv"],
        "used_cooling_total": outputs["spotreba_chlazeni"],
        "aux_used_heating_total": outputs["dohrev_topeni"],
        "aux_used_hot_water_total": outputs["dohrev_tuv"],
    }

    for k, out_stat_id in mapping.items():
        if k in totals:
            totals[k] = round(float(last_cum[out_stat_id]), 3)

    if "used_heating_total" in totals:
        totals["used_heating_total"] = round(float(raw_used_heating_cum), 3)
    if "used_hot_water_total" in totals:
        totals["used_hot_water_total"] = round(float(raw_used_hot_water_cum), 3)

    obj["data"]["totals"] = totals
    storage_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Storage patched:")
    print("  last_processed =", obj["data"]["last_processed"])
    for k in STORAGE_TOTAL_KEYS:
        if k in totals:
            print(f"  {k} = {totals[k]}")

    con.close()

    # Start Core
    print("\nStep 7/7: Start Home Assistant Core\n")
    run_cmd(["ha", "core", "start"])
    print("Home Assistant Core started.\nDONE.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(1)
