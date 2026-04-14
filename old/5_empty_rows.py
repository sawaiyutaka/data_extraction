import pandas as pd

# ===== 設定 =====
input_xlsx = r"G:\ttc6sawai\ee_n1754_251029.xlsx"
output_csv = "empty_rows_EE.csv"

# ===== 読み込み =====
df = pd.read_excel(input_xlsx, dtype=str)

# 列名の前後空白対策
df.columns = [c.strip() for c in df.columns]

if "SAMPLENUMBER" not in df.columns:
    raise ValueError("SAMPLENUMBER 列が見つかりません")

# ===== 判定処理 =====
# SAMPLENUMBER以外の列
other_cols = [c for c in df.columns if c != "SAMPLENUMBER"]

# 空判定（NaN または ""）
mask_empty = df[other_cols].apply(
    lambda row: all(pd.isna(v) or str(v).strip() == "" for v in row),
    axis=1
)

# 該当SAMPLENUMBER抽出
result = df.loc[mask_empty, "SAMPLENUMBER"].dropna().astype(str)

# ===== CSV出力 =====
result.to_csv(output_csv, index=False, encoding="utf-8-sig")

print(f"完了: {len(result)} 件を {output_csv} に出力しました")