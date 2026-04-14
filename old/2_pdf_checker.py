import csv
from collections import defaultdict

# ===== 設定 =====
input_csv = "pdf_filenames.csv"   # 1列のCSV（拡張子なし）
output_csv = "converted.csv"

# 対象のサフィックス
targets = ["EA", "EB", "EC", "EE", "EG", "EH"]

# ===== データ読み込み =====
data = defaultdict(set)

with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    next(reader)  # ヘッダー飛ばす

    for row in reader:
        name = row[0].strip()  # 例: 999901_EA
        if "_" not in name:
            continue

        sample_id, suffix = name.split("_", 1)
        data[sample_id].add(suffix)

# ===== CSV出力 =====
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    # ヘッダー
    writer.writerow(["SAMPLENUMBER"] + targets)

    # IDごとに出力
    for sample_id in sorted(data.keys()):
        row = [sample_id]
        for t in targets:
            row.append(1 if t in data[sample_id] else 0)
        writer.writerow(row)

print(f"完了: {output_csv} を出力しました")