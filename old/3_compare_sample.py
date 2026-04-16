import csv
from pathlib import Path
import pandas as pd

# ===== 設定 =====
flags_csv = Path("converted.csv")   # SAMPLENUMBER,EA,EB,EC,EE,EG,EH が入ったCSV

# 各フラグに対応する比較用xlsx
compare_files = {
    "EA": Path(r"D:\ttc_data_extract\ea_n3171.xlsx"),
    "EB": Path(r"D:\ttc_data_extract\eb_n3171.xlsx"),
    "EC": Path(r"D:\ttc_data_extract\ec_n2113_PIなし.xlsx"),
    "EE": Path(r"D:\ttc_data_extract\ee_n3171.xlsx"),
    "EG": Path(r"D:\ttc_data_extract\eg_n91.xlsx"),
    "EH": Path(r"D:\ttc_data_extract\eh_n66.xlsx"),
}


def read_first_column_as_set(file_path):
    """
    xlsxの1列目を集合として読み込む。
    ヘッダーが SAMPLENUMBER の場合は除外する。
    """
    result = set()

    df = pd.read_excel(file_path, dtype=str, header=0)

    for value in df.iloc[:, 0]:
        if pd.isna(value):
            continue

        value = str(value).strip()

        if value == "":
            continue

        if value.upper() == "SAMPLENUMBER":
            continue

        result.add(value)

    return result


def read_flag_sets(flags_csv_path, targets):
    """
    converted.csv から、各フラグ列が1の SAMPLENUMBER を抽出する。
    """
    result = {target: set() for target in targets}

    with open(flags_csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("flags_csv のヘッダーが読み取れません。")

        fieldnames = [name.strip() for name in reader.fieldnames]

        if "SAMPLENUMBER" not in fieldnames:
            raise ValueError("flags_csv に 'SAMPLENUMBER' 列がありません。")

        for target in targets:
            if target not in fieldnames:
                raise ValueError(f"flags_csv に '{target}' 列がありません。")

        for row in reader:
            sample_number = row["SAMPLENUMBER"].strip()
            if sample_number == "":
                continue

            for target in targets:
                value = row[target].strip()
                if value == "1":
                    result[target].add(sample_number)

    return result


# ===== メイン処理 =====
targets = list(compare_files.keys())
flag_sets = read_flag_sets(flags_csv, targets)

for target, compare_file in compare_files.items():
    if not compare_file.exists():
        print(f"[警告] {target} 用のファイルが見つかりません: {compare_file}")
        continue

    flag_set = flag_sets[target]
    other_set = read_first_column_as_set(compare_file)

    only_in_flag = sorted(flag_set - other_set)
    only_in_other = sorted(other_set - flag_set)
    common = sorted(flag_set & other_set)

    output_file = f"{target}_result.csv"

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([f"{target}_flag_count", len(flag_set)])
        writer.writerow([f"{target}_xlsx_count", len(other_set)])
        writer.writerow([f"common_count", len(common)])
        writer.writerow([f"only_in_flag_count", len(only_in_flag)])
        writer.writerow([f"only_in_xlsx_count", len(only_in_other)])
        writer.writerow([])

        writer.writerow(["only_in_flag", "only_in_compare_xlsx", "common"])

        max_len = max(len(only_in_flag), len(only_in_other), len(common))
        for i in range(max_len):
            writer.writerow([
                only_in_flag[i] if i < len(only_in_flag) else "",
                only_in_other[i] if i < len(only_in_other) else "",
                common[i] if i < len(common) else "",
            ])

    print(f"[{target}] 結果を出力しました: {output_file}")
    print(f"  converted.csv 側 ({target}=1) : {len(flag_set)}")
    print(f"  比較xlsx側                   : {len(other_set)}")
    print(f"  共通                         : {len(common)}")
    print(f"  converted.csv側のみに存在    : {len(only_in_flag)}")
    print(f"  比較xlsx側のみに存在         : {len(only_in_other)}")
    print()