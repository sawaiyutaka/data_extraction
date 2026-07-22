import pandas as pd

# ファイルパス
input_file = r"D:/ttc2d4d/171227A子2D4D.xlsx"
output_file = "finger_2d4d.csv"

# 「解析」シートから指定した列のみ読み込む
df = pd.read_excel(
    input_file,
    sheet_name="解析",
    usecols=["SAMPLENUMBER", "AE62D4DR", "AE62D4DL"]
)

# CSVファイルとして保存
# utf-8-sigにすると、Excelで開いた際にも文字化けしにくくなります
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"CSVファイルを出力しました: {output_file}")