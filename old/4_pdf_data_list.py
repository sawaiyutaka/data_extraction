import csv
from pathlib import Path

# ===== 設定 =====
input_files = {
    "EA": Path("EA_result.csv"),
    "EB": Path("EB_result.csv"),
    "EE": Path("EE_result.csv"),
}

output_csv = Path("scan_input_summary.csv")


def read_result_csv(result_csv_path):
    """
    EA_result.csv などから
    - only_in_flag
    - only_in_compare_xlsx
    を読み取る

    戻り値:
        only_in_flag_set, only_in_compare_set
    """
    only_in_flag = set()
    only_in_compare = set()

    with open(result_csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)

        header_found = False
        for row in reader:
            if not row:
                continue

            row0 = row[0].strip() if len(row) > 0 else ""
            row1 = row[1].strip() if len(row) > 1 else ""

            # 差分表のヘッダー行を見つける
            if row0 == "only_in_flag" and row1 == "only_in_compare_xlsx":
                header_found = True
                continue

            if not header_found:
                continue

            val_flag = row0
            val_compare = row1

            if val_flag != "":
                only_in_flag.add(val_flag)

            if val_compare != "":
                only_in_compare.add(val_compare)

    return only_in_flag, only_in_compare


# ===== 各結果CSVを読み込む =====
status = {}   # {SAMPLENUMBER: {...各フラグ...}}

for target, file_path in input_files.items():
    if not file_path.exists():
        print(f"[警告] ファイルが見つかりません: {file_path}")
        continue

    only_in_flag, only_in_compare = read_result_csv(file_path)

    for sample in only_in_flag:
        if sample not in status:
            status[sample] = {}
        status[sample][f"{target}要データ入力"] = 1

    for sample in only_in_compare:
        if sample not in status:
            status[sample] = {}
        status[sample][f"{target}要スキャン"] = 1


# ===== 出力列 =====
columns = [
    "EA要データ入力",
    "EB要データ入力",
    "EE要データ入力",
    "EA要スキャン",
    "EB要スキャン",
    "EE要スキャン",
]

# ===== CSV出力 =====
with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)

    writer.writerow(["SAMPLENUMBER"] + columns)

    for sample in sorted(status.keys()):
        row = [sample]
        for col in columns:
            row.append(status[sample].get(col, 0))
        writer.writerow(row)

print(f"出力完了: {output_csv}")