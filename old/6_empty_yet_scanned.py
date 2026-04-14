import csv

# ===== 設定 =====
empty_csv = "empty_rows_EE.csv"   # 今作ったCSV（1列）
result_csv = "EE_result.csv"                  # 比較対象（例：EA_result.csv）
output_csv = "compare_empty_vs_scan_EE.csv"


def read_single_column_csv(path):
    """
    1列CSVをsetとして読み込む
    """
    result = set()

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)  # ヘッダー飛ばす

        for row in reader:
            if not row:
                continue
            val = row[0].strip()
            if val != "":
                result.add(val)

    return result


def read_only_in_compare(result_csv_path):
    """
    EA_result.csv などから only_in_compare_xlsx を取得
    """
    result = set()

    with open(result_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        header_found = False

        for row in reader:
            if not row:
                continue

            col1 = row[0].strip() if len(row) > 0 else ""
            col2 = row[1].strip() if len(row) > 1 else ""

            # ヘッダー検出
            if col1 == "only_in_flag" and col2 == "only_in_compare_xlsx":
                header_found = True
                continue

            if not header_found:
                continue

            if col2 != "":
                result.add(col2)

    return result


# ===== 読み込み =====
empty_set = read_single_column_csv(empty_csv)
compare_set = read_only_in_compare(result_csv)

# ===== 比較 =====
only_in_empty = sorted(empty_set - compare_set)
only_in_compare = sorted(compare_set - empty_set)
common = sorted(empty_set & compare_set)

# ===== 出力 =====
max_len = max(len(only_in_empty), len(only_in_compare), len(common))

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "only_in_empty",
        "only_in_only_in_compare_xlsx",
        "common"
    ])

    for i in range(max_len):
        writer.writerow([
            only_in_empty[i] if i < len(only_in_empty) else "",
            only_in_compare[i] if i < len(only_in_compare) else "",
            common[i] if i < len(common) else "",
        ])

# ===== ログ =====
print("比較完了")
print(f"empty側件数: {len(empty_set)}")
print(f"compare側件数: {len(compare_set)}")
print(f"共通: {len(common)}")
print(f"emptyのみに存在: {len(only_in_empty)}")
print(f"compareのみに存在: {len(only_in_compare)}")
print(f"出力: {output_csv}")