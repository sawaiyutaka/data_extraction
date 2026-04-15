#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
faz_aggregated_merged.csv に対して、ノイズ記録CSVを参照し、
L_Center または R_Center が 1 のとき、対応するFAZ指標を空欄にするスクリプト。
"""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# ===== パス設定 ============================================================
merged_csv_path = Path(r"D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\faz_aggregated_merged.csv")
noise_csv_path  = Path(r"D:\ttc5oct\oct20251126\oct20angio_noise260414.csv")
output_csv_path = Path(r"D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\faz_masked.csv")
# ==========================================================================

ENCODINGS = ("utf-8-sig", "cp932", "utf-8")

# Centerノイズ → 空欄にする対象列
TARGETS = {
    "L_Center": ["L_Area", "L_Perimeter", "L_Circularity", "L_AxisRatio"],
    "R_Center": ["R_Area", "R_Perimeter", "R_Circularity", "R_AxisRatio"],
}


def read_csv_any(path: Path) -> Tuple[List[str], List[List[str]]]:
    for enc in ENCODINGS:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                rows = list(csv.reader(f))
                if not rows:
                    return [], []
                return rows[0], rows[1:]
        except UnicodeDecodeError:
            continue

    with path.open("rb") as f:
        text = f.read().decode("utf-8", errors="replace")
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def to_dicts(header: List[str], data: List[List[str]]) -> List[Dict[str, str]]:
    idx = {i: h for i, h in enumerate(header)}
    out: List[Dict[str, str]] = []
    for row in data:
        d: Dict[str, str] = {idx[i]: (row[i] if i < len(row) else "") for i in idx}
        out.append(d)
    return out


def index_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {r.get("ID", "").strip(): r for r in rows if r.get("ID", "").strip()}


def is_noise(val: str) -> bool:
    v = (val or "").strip()
    return v == "1" or v == "１"


def apply_noise_mask(merged_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> int:
    by_id = index_by_id(merged_rows)
    masked_cells = 0

    for n in noise_rows:
        pid = (n.get("ID", "") or "").strip()
        if not pid or pid not in by_id:
            continue

        tgt_row = by_id[pid]

        for key, targets in TARGETS.items():
            if key in n and is_noise(n[key]):
                for col in targets:
                    if col in tgt_row and tgt_row[col] != "":
                        tgt_row[col] = ""
                        masked_cells += 1

    return masked_cells


def ensure_all_columns(rows: List[Dict[str, str]], header: List[str]) -> List[str]:
    cols = [c for c in header if c]
    for r in rows:
        for k in r.keys():
            if k and k not in cols:
                cols.append(k)
    return cols


def main():
    if not merged_csv_path.exists():
        print(f"Error: 統合CSVが見つかりません → {merged_csv_path}")
        return
    if not noise_csv_path.exists():
        print(f"Error: ノイズCSVが見つかりません → {noise_csv_path}")
        return

    m_header, m_data = read_csv_any(merged_csv_path)
    n_header, n_data = read_csv_any(noise_csv_path)

    merged_dicts = to_dicts(m_header, m_data)
    noise_dicts = to_dicts(n_header, n_data)

    masked = apply_noise_mask(merged_dicts, noise_dicts)

    out_header = ensure_all_columns(merged_dicts, m_header)

    with output_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_header)
        writer.writeheader()
        for r in merged_dicts:
            writer.writerow({c: r.get(c, "") for c in out_header})

    print(f"OK: masked {masked} cells → {output_csv_path}")

    # ===== 記述統計の出力 =========================================
    import math

    def to_float_safe(x):
        try:
            return float(x)
        except:
            return math.nan

    # 数値列だけ抽出
    numeric_cols = []
    for col in out_header:
        vals = [to_float_safe(r.get(col, "")) for r in merged_dicts]
        vals = [v for v in vals if not math.isnan(v)]
        if len(vals) > 0:
            numeric_cols.append(col)

    print("\n=== 記述統計 ===")
    for col in numeric_cols:
        vals = [to_float_safe(r.get(col, "")) for r in merged_dicts]
        vals = [v for v in vals if not math.isnan(v)]
        if len(vals) == 0:
            continue

        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        mean = sum(vals_sorted) / n
        median = vals_sorted[n // 2] if n % 2 == 1 else (vals_sorted[n//2 - 1] + vals_sorted[n//2]) / 2
        vmin = vals_sorted[0]
        vmax = vals_sorted[-1]

        # IQR
        q1 = vals_sorted[int(n * 0.25)]
        q3 = vals_sorted[int(n * 0.75)]
        iqr = q3 - q1

        print(f"{col}: n={n}, mean={mean:.3f}, median={median:.3f}, min={vmin:.3f}, max={vmax:.3f}, Q1={q1:.3f}, Q3={q3:.3f}, IQR={iqr:.3f}")

    # ===== IQR外れ値のIDリストアップ =====================================
    print("\n=== IQR外れ値（ID） ===")

    for col in numeric_cols:
        vals_with_id = []
        for r in merged_dicts:
            v = to_float_safe(r.get(col, ""))
            if not math.isnan(v):
                vals_with_id.append((r.get("ID", ""), v))

        if len(vals_with_id) == 0:
            continue

        vals_sorted = sorted([v for _, v in vals_with_id])
        n = len(vals_sorted)

        q1 = vals_sorted[int(n * 0.25)]
        q3 = vals_sorted[int(n * 0.75)]
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = [pid for pid, v in vals_with_id if v < lower or v > upper]

        if outliers:
            print(f"{col}: {len(outliers)}件 → {sorted(set(outliers))}")


if __name__ == "__main__":
    main()