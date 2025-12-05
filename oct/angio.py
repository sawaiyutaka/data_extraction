#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyCharm上で直接実行できるようにした「ETDRS 9 Sector Density 集計」スクリプト。
指定したフォルダ内のCSVファイルを一括処理し、
<ETDRS 9 Sector Density> セクションから「血管密度（VD）」を抽出して
1つのCSVに出力します。

対象となるセクタ（9領域）:
Center,
Inner Temporal, Inner Superior, Inner Nasal, Inner Inferior,
Outer Temporal, Outer Superior, Outer Nasal, Outer Inferior

出力カラム:
ID, R_Center, R_Inner_Temporal, R_Inner_Superior, R_Inner_Nasal, R_Inner_Inferior,
   R_Outer_Temporal, R_Outer_Superior, R_Outer_Nasal, R_Outer_Inferior,
   L_Center, L_Inner_Temporal, L_Inner_Superior, L_Inner_Nasal, L_Inner_Inferior,
   L_Outer_Temporal, L_Outer_Superior, L_Outer_Nasal, L_Outer_Inferior

使い方:
1. PyCharmでこのスクリプトを開く
2. 下の `input_dir` 変数にCSVが入ったフォルダのパスを指定
3. `output_csv` に出力ファイルのパスを指定
4. 実行ボタン（▶）を押す
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

# ==== 設定ここから ======================================================
# CSVファイルが入っているフォルダを指定してください（例: r"C:\\Users\\user\\Documents\\csv"）
input_dir = Path(r"D:\ttc5oct\oct20251126\アンギオ")  # ←ここを書き換えてください

# 出力するCSVファイル名
output_csv = Path(r"D:\ttc5oct\oct20251126\output20251125\vd_aggregated_merged.csv")
# ======================================================================

# 9セクタ
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

# 出力列
OUTPUT_COLUMNS = [
    "ID",
    "R_Center", "R_Inner_Temporal", "R_Inner_Superior", "R_Inner_Nasal", "R_Inner_Inferior",
    "R_Outer_Temporal", "R_Outer_Superior", "R_Outer_Nasal", "R_Outer_Inferior",
    "L_Center", "L_Inner_Temporal", "L_Inner_Superior", "L_Inner_Nasal", "L_Inner_Inferior",
    "L_Outer_Temporal", "L_Outer_Superior", "L_Outer_Nasal", "L_Outer_Inferior",
]

# 対象セクションのタグ
ETDRS_DENSITY_TAG = "<ETDRS 9 Sector Density>"

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
    # どうしてもダメなときは置換モードで読む
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

    例:
    Eye,S/N,Version(F/S),Date,SSI,SLO,Focus[D],Ref[D],Axial[mm],SQI
    L,611167,22100/2.22.00,2022/09/13 15:25:17,10,Wide,-0.50,,0.00,5

    -> 'L' を返す
    """
    eye_idx = None
    for i, r in enumerate(rows):
        if not r:
            continue
        if r[0].strip() == "Eye":
            eye_idx = i
            break
        # 1セルに全部入っているパターンも考慮
        line = ",".join(r)
        if line.startswith(EYE_HEADER_PREFIX):
            eye_idx = i
            break

    if eye_idx is None:
        return None

    # Eye行の次から最初に出てくる R / L を採用
    for j in range(eye_idx + 1, len(rows)):
        row = rows[j]
        if not row or not any(cell.strip() for cell in row):
            continue
        first = (row[0] or "").strip().upper()
        if first.startswith("R"):
            return "R"
        if first.startswith("L"):
            return "L"
        # 別セクションっぽいものが来たら終了
        if first.startswith("<"):
            break

    return None


def find_etdrs_density_index(rows: List[List[str]]) -> Optional[int]:
    """<ETDRS 9 Sector Density> 行のインデックスを返す"""
    for i, r in enumerate(rows):
        if r and r[0].strip() == ETDRS_DENSITY_TAG:
            return i
    return None


def extract_etdrs_vd(rows: List[List[str]]) -> Dict[str, Optional[float]]:
    """
    <ETDRS 9 Sector Density> セクションから
    9セクタのVD（2列目の数字）を取り出す。

    想定フォーマット:
    <ETDRS 9 Sector Density>
    Size,直径0.5/1.5/3.0mm
    Sector,網膜表層
    Type,VD,PD
    Whole,10.52,25.17
    Inner,7.99,17.59
    Outer,15.68,39.03
    Center,0.00,0.00
    Inner Temporal,10.81,25.24
    ...
    Outer Inferior,12.97,33.34
    """
    result: Dict[str, Optional[float]] = {s: None for s in SECTORS}

    idx = find_etdrs_density_index(rows)
    if idx is None:
        return result

    # タグ行の次の行から下方向へ走査
    for i in range(idx + 1, len(rows)):
        row = rows[i]
        if not row or not any(cell.strip() for cell in row):
            # 空行はスキップ
            continue
        if row[0].strip().startswith("<"):
            # 次のセクションに達したら終了
            break

        sector_name = (row[0] or "").strip()
        if sector_name in result and len(row) > 1:
            # 2列目(インデックス1)をVDとして採用
            result[sector_name] = safe_float(row[1])

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
    1つのCSVファイルを読み込み、ID と 9セクタVD を
    R_ / L_ カラムに入れた辞書を返す。
    """
    rows = read_csv_rows(path)
    eye_side = detect_eye_side(rows)  # 'R', 'L', もしくは None
    vd_dict = extract_etdrs_vd(rows)

    row_out: Dict[str, Optional[float]] = {c: None for c in OUTPUT_COLUMNS}
    row_out["ID"] = get_id_from_filename(path)

    for sec in SECTORS:
        val = vd_dict.get(sec)
        col_suffix = sec.replace(" ", "_")
        if eye_side == "R":
            row_out[f"R_{col_suffix}"] = val
        elif eye_side == "L":
            row_out[f"L_{col_suffix}"] = val
        else:
            # 目が判定できなければ何もしない（全てNoneのまま）
            pass

    return row_out


def main():
    if not input_dir.exists():
        print(f"Error: フォルダが見つかりません → {input_dir}")
        return

    files = sorted(input_dir.glob("*.csv"))
    if not files:
        print("CSVファイルが見つかりません。")
        return

    # まず全ファイルを処理
    rows_tmp: List[Dict[str, Optional[float]]] = []
    for p in files:
        try:
            rows_tmp.append(process_file(p))
        except Exception as e:
            print(f"[WARN] {p.name} の処理に失敗しました: {e}")

    # ==== ★ ここからIDでマージする処理を追加 ★ ====

    merged: Dict[str, Dict[str, Optional[float]]] = {}

    for row in rows_tmp:
        id_ = row["ID"]
        if id_ not in merged:
            # 初回は全部Noneで初期化
            merged[id_] = {col: None for col in OUTPUT_COLUMNS}
            merged[id_]["ID"] = id_

        # R/L の列だけ更新
        for col, val in row.items():
            if col == "ID":
                continue
            if val is not None:
                merged[id_][col] = val

    # リストに戻す
    rows_out = list(merged.values())

    # ==== ★ ここまで追加 ★ ====

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"完了: {len(rows_out)} 件のIDを処理しました → {output_csv}")



if __name__ == "__main__":
    main()
