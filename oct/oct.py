#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyCharm上で直接実行できるようにしたETDRS集計スクリプト。
指定したフォルダ内のCSVファイルを一括処理し、<ETDRS> セクションの
Thickness1R / Thickness1L をまとめて1つのCSVに出力します。

出力カラム:
ID, R-Center, R-Inner_Temporal, R-Inner_Superior, R-Inner_Nasal, R-Inner_Inferior,
   R-Outer_Temporal, R-Outer_Superior, R-Outer_Nasal, R-Outer_Inferior,
   L-Center, L-Inner_Temporal, L-Inner_Superior, L-Inner_Nasal, L-Inner_Inferior,
   L-Outer_Temporal, L-Outer_Superior, L-Outer_Nasal, L-Outer_Inferior

使い方:
1. PyCharmでこのスクリプトを開く
2. 下の `input_dir` 変数にCSVが入ったフォルダのパスを指定
3. 実行ボタン（▶）を押す
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ==== 設定ここから ======================================================
# CSVファイルが入っているフォルダを指定してください（例: r"C:\\Users\\user\\Documents\\csv"）
input_dir = Path(r"D:\ttc5oct\oct20251126\乳頭")  # ←ここを書き換えてください
# "D:\ttc5oct\oct20251126\黄斑1(ILM-NFLGCL)"
# "D:\ttc5oct\oct20251126\黄斑2(NFLGCL-IPLINL)"
# "D:\ttc5oct\oct20251126\黄斑3(IPLINL-OPLONL)"
# "D:\ttc5oct\oct20251126\黄斑4(OPLONL-ISOS)"
# "D:\ttc5oct\oct20251126\黄斑5(ISOS-RPEBM)"

# 出力するCSVファイル名
output_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\p_aggregated.csv")
# "D:\ttc5oct\oct20251126\output20251125\m1_ILM-NFLGCL_aggregated.csv"
# 'D:\ttc5oct\oct20251126\output20251125\m2_NFLGCL-IPLINL_aggregated.csv
# 'D:\ttc5oct\oct20251126\output20251125\m3_IPLINL-OPLONL_aggregated.csv'
# "D:\ttc5oct\oct20251126\output20251125\m4_OPLONL-ISOS_aggregated.csv"
# "D:\ttc5oct\oct20251126\output20251125\m5_ISOS-RPEBM_aggregated.csv"
# ======================================================================

SECTORS = [
    "Center",
    "Inner Temporal",
    "Inner Superior",
    "Inner Nasal",
    "Inner Inferior",
    "Outer Temporal",
    "Outer Superior",
    "Outer Nasal",
    "Outer Inferior",
]

OUTPUT_COLUMNS = [
    "ID",
    "R-Center","R-Inner_Temporal","R-Inner_Superior","R-Inner_Nasal","R-Inner_Inferior",
    "R-Outer_Temporal","R-Outer_Superior","R-Outer_Nasal","R-Outer_Inferior",
    "L-Center","L-Inner_Temporal","L-Inner_Superior","L-Inner_Nasal","L-Inner_Inferior",
    "L-Outer_Temporal","L-Outer_Superior","L-Outer_Nasal","L-Outer_Inferior",
]

ETDRS_TAG = "<ETDRS>"
EYE_HEADER_PREFIX = ["Eye,S/N,Version(F/S),Date,SSI,SLO,Focus[D],Ref[D],Axial[mm],SQI"]


def read_csv_rows(path: Path) -> List[List[str]]:
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return [row for row in csv.reader(f)]
        except UnicodeDecodeError:
            continue
    with path.open("rb") as f:
        text = f.read().decode("utf-8", errors="replace")
    return [row for row in csv.reader(text.splitlines())]


def safe_float(s: str) -> Optional[float]:
    if not s:
        return None
    t = str(s).strip().replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def detect_eye_presence(rows: List[List[str]]) -> Tuple[bool, bool]:
    """Eyeヘッダ直下の測定エントリから R/L の有無を検出。
    - 直後がRで、その後にLがなければ (True, False)
    - 直後がLであれば (False, True)
    - R, Lの順で並んでいれば (True, True)
    """
    eye_idx = None
    # Eyeヘッダ行の検出（厳密/ゆるめの両方）
    for i, r in enumerate(rows):
        if len(r) > 0 and r[0].strip() == "Eye":
            eye_idx = i
            break
        line = ",".join(r)
        if line.startswith("Eye,S/N,Version(F/S),Date,SSI,SLO,Focus[D],Ref[D],Axial[mm],SQI"):
            eye_idx = i
            break
    if eye_idx is None:
        return False, False

    has_r = False
    has_l = False

    # Eye行の次から、数行をチェック（空行や次セクションまで）
    j = eye_idx + 1
    while j < len(rows):
        row = rows[j]
        # 次セクションと見なせる境界
        if not row or not any(cell.strip() for cell in row):
            # 空行に到達したら打ち切り
            break
        if row[0].strip().startswith("<"):
            break

        first = (row[0] if row else "").strip().upper()
        if first.startswith("R"):
            has_r = True
        elif first.startswith("L"):
            has_l = True
        else:
            # Eyeセクションに無関係な行が来たら抜ける
            break
        j += 1
    return has_r, has_l
    return False


def find_etdrs_table(rows: List[List[str]]) -> Tuple[Optional[int], Optional[Tuple[int, int]]]:
    etdrs_idx = None
    for i, r in enumerate(rows):
        if len(r) > 0 and r[0].strip() == ETDRS_TAG:
            etdrs_idx = i
            break
    if etdrs_idx is None:
        return None, None

    header_row = rows[etdrs_idx + 1] if etdrs_idx + 1 < len(rows) else []
    r_col = next((i for i, h in enumerate(header_row) if h.strip().endswith("R")), None)
    l_col = next((i for i, h in enumerate(header_row) if h.strip().endswith("L")), None)
    return etdrs_idx, (r_col or -1, l_col or -1)


def extract_etdrs(rows: List[List[str]]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    etdrs_idx, rl_cols = find_etdrs_table(rows)
    result = {s: (None, None) for s in SECTORS}
    if etdrs_idx is None or rl_cols is None:
        return result

    r_col, l_col = rl_cols
    i = etdrs_idx + 2
    while i < len(rows):
        row = rows[i]
        if not row or (len(row) > 0 and row[0].strip().startswith("<")):
            break
        if row[0].strip() == "Size":
            i += 1
            continue
        sector_name = (row[0] if row else "").strip()
        if sector_name in result:
            r_val = safe_float(row[r_col]) if r_col < len(row) else None
            l_val = safe_float(row[l_col]) if l_col < len(row) else None
            result[sector_name] = (r_val, l_val)
        i += 1
    return result


def get_id_from_filename(path: Path) -> str:
    m = re.search(r"(EG\d{4})", path.name)
    return m.group(1) if m else path.name[:6]


def process_file(path: Path) -> Dict[str, Optional[float]]:
    rows = read_csv_rows(path)
    has_right, has_left = detect_eye_presence(rows)
    etdrs = extract_etdrs(rows)

    row_out = {c: None for c in OUTPUT_COLUMNS}
    row_out["ID"] = get_id_from_filename(path)

    for sec in SECTORS:
        r_val, l_val = etdrs.get(sec, (None, None))
        key_r = "R-" + sec.replace(" ", "_")
        key_l = "L-" + sec.replace(" ", "_")
        row_out[key_r] = r_val if has_right else None
        # ここが重要: L行が存在しない場合は L を欠損にする
        row_out[key_l] = l_val if has_left else None
    return row_out


def main():
    if not input_dir.exists():
        print(f"Error: フォルダが見つかりません → {input_dir}")
        return

    files = sorted(input_dir.glob("*.csv"))
    if not files:
        print("CSVファイルが見つかりません。")
        return

    rows_out = []
    for p in files:
        try:
            rows_out.append(process_file(p))
        except Exception as e:
            print(f"[WARN] {p.name} の処理に失敗しました: {e}")

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"完了: {len(rows_out)} 件を処理しました → {output_csv}")


if __name__ == "__main__":
    main()
