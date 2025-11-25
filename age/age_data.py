import csv
import glob
import math
import re
from pathlib import Path
from collections import defaultdict

# ===== 設定 =====
INPUT_DIR = Path(r"E:\age_test")   # ← CSVフォルダのパスに変更してください
OUTPUT_CSV = Path("output_scores.csv")

# ===== ユーティリティ =====
def to_float_safe(s):
    try:
        return float(str(s).strip())
    except Exception:
        return math.nan

def pick_score(scores):
    """
    スコア配列に対し、規則に従って1値を求める。
    - 2件: 単純平均
    - 3件以上: 値が最も近い2つを選んで平均
    """
    vals = [v for v in scores if isinstance(v, (int, float)) and math.isfinite(v)]
    if len(vals) < 2:
        return None
    if len(vals) == 2:
        return sum(vals) / 2.0
    vals_sorted = sorted(vals)
    best_pair = (vals_sorted[0], vals_sorted[1])
    best_diff = abs(vals_sorted[1] - vals_sorted[0])
    for i in range(1, len(vals_sorted) - 1):
        a, b = vals_sorted[i], vals_sorted[i + 1]
        d = abs(b - a)
        if d < best_diff:
            best_diff = d
            best_pair = (a, b)
    return sum(best_pair) / 2.0

# ===== データ収集構造 =====
scores_by_valid_id = defaultdict(list)   # 有効ID(=EG+4桁) → スコア一覧
invalid_id_files    = defaultdict(set)   # 無効ID(=計算対象外) → 出現ファイル名集合

# 【追加済みの報告用】サフィックス付きの元IDを記録（計算は正規化IDで実施）
stripped_id_files   = defaultdict(set)   # 例: 'EG0002-1' → 報告用（計算は 'EG0002' で実施）

# ===== CSVファイル列挙 =====
csv_paths = sorted(glob.glob(str(INPUT_DIR / "*.csv")))
if not csv_paths:
    print(f"[警告] CSVが見つかりません: {INPUT_DIR.resolve()}")

# ===== CSV読み込み =====
for path in csv_paths:
    p = Path(path)
    # 日本語Windowsの「ANSI」（Shift_JIS）想定
    with open(p, "r", encoding="cp932") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        continue

    header = rows[0]

    # --- 列位置は完全一致のみ ---
    def find_col_exact(name: str):
        for i, h in enumerate(header):
            if str(h) == name:
                return i
        return None

    idx_id    = find_col_exact("ID")
    idx_score = find_col_exact("スコア")

    # 必須列が無ければこのファイルはスキップ（警告のみ）
    if idx_id is None or idx_score is None:
        print(f"[警告] 必須列が見つかりません: {p.name} (ID列: {idx_id}, Score列: {idx_score})")
        continue

    # データ行処理
    for row in rows[1:]:
        if not row or all(not str(x).strip() for x in row):
            continue

        raw_id = row[idx_id].strip() if idx_id < len(row) else ""
        score  = to_float_safe(row[idx_score]) if idx_score < len(row) else math.nan
        if not raw_id:
            continue

        # ==============================
        # ID処理の分岐ロジック
        # ==============================

        # 1) 数字4桁のみ（例: "0001"）
        #    - 数値が 3171 以下 → "EG" を付けて "EG0001" として計算に回す
        #    - 数値が 3172 以上 → 計算せず invalid としてファイル名を出力対象に
        if re.fullmatch(r"\d{4}", raw_id):
            num = int(raw_id)
            if num <= 3171:
                canonical_id = f"EG{raw_id}"
                scores_by_valid_id[canonical_id].append(score)
            else:
                invalid_id_files[raw_id].add(p.name)
            continue  # 次の行へ

        # 2) 【変更】"EGdddd-<正の整数>" をすべて対象に（-1/-2/-3 だけでなく -4, -5, ... も）
        #    - 元IDは報告（print）対象に登録
        #    - サフィックス（-<n>）を取り除いた "EGdddd" を計算に使用
        if re.fullmatch(r"EG\d{4}-(?:[1-9]\d*)", raw_id):  # 【変更】ここを拡張
            stripped_id_files[raw_id].add(p.name)                    # 報告用
            canonical_id = raw_id.split("-")[0]                      # "EGdddd" に正規化
            scores_by_valid_id[canonical_id].append(score)           # 計算は正規化IDで
            continue  # 次の行へ

        # 3) 正規の "EGdddd"（例: "EG1111"）→ そのまま計算
        if re.fullmatch(r"EG\d{4}", raw_id):
            scores_by_valid_id[raw_id].append(score)
            continue

        # 4) 上記いずれにも該当しない → 計算せず invalid として報告対象へ
        invalid_id_files[raw_id].add(p.name)

# ===== 【変更】サフィックス付きIDの報告メッセージを一般化（-数字 全般） =====
if stripped_id_files:
    print("[サフィックス検出] '-数字' を含むIDを検出しました。これらはサフィックスを除去して計算しています。")
    for sid in sorted(stripped_id_files.keys()):
        files = ", ".join(sorted(stripped_id_files[sid]))
        print(f"  - ID: {sid} | ファイル: {files}")

# ===== 無効IDの報告（スコア計算なし） =====
if invalid_id_files:
    print("[無効ID検出] ルール外のIDが見つかりました。これらはスコア計算しません。")
    for bad_id in sorted(invalid_id_files.keys()):
        files = ", ".join(sorted(invalid_id_files[bad_id]))
        print(f"  - ID: {bad_id} | ファイル: {files}")

# ===== スコア集計（有効IDのみ） =====
result_rows = []
for valid_id, scores in scores_by_valid_id.items():
    score_val = pick_score(scores)
    if score_val is None:
        # 有効なスコアが2件未満なら出力なし
        continue
    score_out = round(score_val, 4)
    result_rows.append((valid_id, score_out))

# IDでソート
result_rows.sort(key=lambda t: t[0])

# ===== CSV出力 =====
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_CSV, "w", encoding="cp932", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Score"])  # 列名は「Score」に統一
    for rid, sc in result_rows:
        writer.writerow([rid, f"{sc:.4f}"])

print(f"[完了] 出力ファイル: {OUTPUT_CSV.resolve()}")
