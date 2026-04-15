#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyCharm上で直接実行できるようにした「FAZ Parameter 集計」スクリプト。
指定したフォルダ内のCSVファイルを一括処理し、
<FAZ Parameter> セクションから4項目を抽出して
1つのCSVに出力します。

抽出項目:
Area[mm2]
Perimeter[mm]
Circularity
Axis Ratio

出力カラム:
ID, R_Area, R_Perimeter, R_Circularity, R_AxisRatio,
    L_Area, L_Perimeter, L_Circularity, L_AxisRatio
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

# ==== 設定ここから ======================================================
input_dir = Path(r"G:\アンギオデータベース作成用\アンギオ")  # ←ここを書き換えてください
output_csv = Path(r"G:\アンギオデータベース作成用\faz_aggregated_merged.csv")
# ======================================================================

# 抽出対象項目
FAZ_ITEMS = [
    "Area[mm2]",
    "Perimeter[mm]",
    "Circularity",
    "Axis Ratio",
]

# 出力列
OUTPUT_COLUMNS = [
    "ID",
    "R_Area", "R_Perimeter", "R_Circularity", "R_AxisRatio",
    "L_Area", "L_Perimeter", "L_Circularity", "L_AxisRatio",
]

# 対象セクションのタグ
FAZ_PARAMETER_TAG = "<FAZ Parameter>"

# Eyeヘッダ（ゆるめ判定用）
EYE_HEADER_PREFIX = "Eye,S/N,Version(F/S),Date,SSI,SLO,Focus[D],Ref[D],Axial[mm],SQI"


def read_csv_rows(path: Path) -> List[List[str]]:
    """エンコーディングを自動判定しつつCSVを行ごとに読み込む"""
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
    if s is None:
        return None
    t = str(s).strip().replace(",", "")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def detect_eye_side(rows: List[List[str]]) -> Optional[str]:
    """
    ファイル上部の Eye セクションから R / L を判定する。
    """
    eye_idx = None
    for i, r in enumerate(rows):
        if not r:
            continue
        if r[0].strip() == "Eye":
            eye_idx = i
            break
        line = ",".join(r)
        if line.startswith(EYE_HEADER_PREFIX):
            eye_idx = i
            break

    if eye_idx is None:
        return None

    for j in range(eye_idx + 1, len(rows)):
        row = rows[j]
        if not row or not any(cell.strip() for cell in row):
            continue
        first = (row[0] or "").strip().upper()
        if first.startswith("R"):
            return "R"
        if first.startswith("L"):
            return "L"
        if first.startswith("<"):
            break

    return None


def find_faz_parameter_index(rows: List[List[str]]) -> Optional[int]:
    """<FAZ Parameter> 行のインデックスを返す"""
    for i, r in enumerate(rows):
        if r and r[0].strip() == FAZ_PARAMETER_TAG:
            return i
    return None


def extract_faz_parameters(rows: List[List[str]]) -> Dict[str, Optional[float]]:
    """
    <FAZ Parameter> セクションから4項目を取り出す。

    想定フォーマット:
    <FAZ Parameter>
    Area[mm2], x.xx
    Perimeter[mm], x.xx
    Circularity, x.xx
    Axis Ratio, x.xx
    """
    result: Dict[str, Optional[float]] = {item: None for item in FAZ_ITEMS}

    idx = find_faz_parameter_index(rows)
    if idx is None:
        return result

    for i in range(idx + 1, len(rows)):
        row = rows[i]
        if not row or not any(cell.strip() for cell in row):
            continue
        if row[0].strip().startswith("<"):
            break

        item_name = (row[0] or "").strip()
        if item_name in result and len(row) > 1:
            result[item_name] = safe_float(row[1])

    return result


def get_id_from_filename(path: Path) -> str:
    """
    ファイル名から ID を抽出。
    例: EG0001_xxx.csv -> EG0001
    """
    m = re.search(r"(EG\d{4})", path.name)
    return m.group(1) if m else path.name[:6]


def process_file(path: Path) -> Dict[str, Optional[float]]:
    """
    1つのCSVファイルを読み込み、ID と FAZ 4項目を
    R_ / L_ カラムに入れた辞書を返す。
    """
    rows = read_csv_rows(path)
    eye_side = detect_eye_side(rows)
    faz_dict = extract_faz_parameters(rows)

    row_out: Dict[str, Optional[float]] = {c: None for c in OUTPUT_COLUMNS}
    row_out["ID"] = get_id_from_filename(path)

    mapping = {
        "Area[mm2]": "Area",
        "Perimeter[mm]": "Perimeter",
        "Circularity": "Circularity",
        "Axis Ratio": "AxisRatio",
    }

    for src_name, dst_suffix in mapping.items():
        val = faz_dict.get(src_name)
        if eye_side == "R":
            row_out[f"R_{dst_suffix}"] = val
        elif eye_side == "L":
            row_out[f"L_{dst_suffix}"] = val

    return row_out


def main():
    if not input_dir.exists():
        print(f"Error: フォルダが見つかりません → {input_dir}")
        return

    files = sorted(input_dir.glob("*.csv"))
    if not files:
        print("CSVファイルが見つかりません。")
        return

    rows_tmp: List[Dict[str, Optional[float]]] = []
    for p in files:
        try:
            rows_tmp.append(process_file(p))
        except Exception as e:
            print(f"[WARN] {p.name} の処理に失敗しました: {e}")

    merged: Dict[str, Dict[str, Optional[float]]] = {}

    for row in rows_tmp:
        id_ = row["ID"]
        if id_ not in merged:
            merged[id_] = {col: None for col in OUTPUT_COLUMNS}
            merged[id_]["ID"] = id_

        for col, val in row.items():
            if col == "ID":
                continue
            if val is not None:
                merged[id_][col] = val

    rows_out = list(merged.values())

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"完了: {len(rows_out)} 件のIDを処理しました → {output_csv}")


if __name__ == "__main__":
    main()