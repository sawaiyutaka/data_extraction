import pandas as pd

# ===== ファイル =====
a_csv = r"C:\Users\sawai\PycharmProjects\data_extraction\raisho_id_no_dup.csv"
b_csv = "age_output.csv"
output_csv = "age_data_no_duplicate.csv"

# ===== 読み込み（文字コード注意）=====
df_a = pd.read_csv(a_csv, header=None, dtype=str)
df_b = pd.read_csv(b_csv, header=None, dtype=str)

# 列名設定
df_a.columns = ["ID", "SAMPLENUMCER"]
# Bは列数不明なので1列目だけ名前付け
df_b = df_b.rename(columns={0: "ID"})

# ===== Aに含まれるIDだけ残す =====
df_b_filtered = df_b[df_b["ID"].isin(df_a["ID"])].copy()

# ===== サンプルナンバーを結合 =====
df_merged = df_b_filtered.merge(df_a, on="ID", how="left")

# ===== 保存 =====
df_merged.to_csv(output_csv, index=False, header=False, encoding="utf-8-sig")

print("処理完了")
print(f"重複削除前の件数: {len(df_b)}")
print(f"重複削除後の件数: {len(df_merged)}")