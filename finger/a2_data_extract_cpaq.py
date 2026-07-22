import pandas as pd

# ファイルパス
input_file = r"D:/ttc2d4d/171227A子2D4D.xlsx"
output_file = "finger_2d4d.csv"

import pandas as pd

# ============================================================
# ファイル設定
# ============================================================
input_file = r"D:\ttc2d4d\150212A子CPAQ.xlsx"
output_file = r"D:\ttc2d4d\CPAQ_variables.csv"

# 出力する列（この順番で出力されます）
columns_to_extract = [
    "SAMPLENUMBER",
    "AD36CPAQm_Total",
    "AD36CPAQm_Ave",
    "AD36CPAQm_NA",
    "AD36CPAQm_Imp",
    "AD36CPAQf_Total",
    "AD36CPAQf_Ave",
    "AD36CPAQf_NA",
    "AD36CPAQf_Imp",
    "AD36CPAQa_Total",
    "AD36CPAQa_Ave",
    "AD36CPAQa_NA",
    "AD36CPAQa_Imp"
]

# ============================================================
# Excelファイルの「解析」シートから指定列のみ読み込む
# ============================================================
df = pd.read_excel(
    input_file,
    sheet_name="解析",
    usecols=columns_to_extract
)

# 念のため、指定した順番に列を並べる
df = df[columns_to_extract]

# ============================================================
# CSVファイルとして保存
# ============================================================
df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print(f"CSVファイルを出力しました: {output_file}")
print(f"出力人数: {len(df)}")
print(f"出力列数: {len(df.columns)}")