import pandas as pd

# ===== ファイル =====
a_csv = r"C:\Users\sawai\PycharmProjects\data_extraction\raisho_id_no_dup.csv"  # 重複を削除した来所IDリスト

b_csv = r"D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\faz_masked.csv"  # 来所型IDのみのデータセット
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\m1_ILM-NFLGCL_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\m2_NFLGCL-IPLINL_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\m3_IPLINL-OPLONL_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\m4_OPLONL-ISOS_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\m5_ISOS-RPEBM_OPLONL-ISOS_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\angio_vd_masked.csv"
# "D:\ttc5oct\oct20251126\output20260415_重複_IDエラー修正\faz_masked.csv"

output_csv = r"D:\ttc5oct\データセット作成用20260415\angio_faz_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m0_ALL-LAYERS_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m1_ILM-NFLGCL_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m2_NFLGCL-IPLINL_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m3_IPLINL-OPLONL_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m4_OPLONL-ISOS_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\m5_ISOS-RPEBM_OPLONL-ISOS_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\angio_vd_no_dup.csv"
# "D:\ttc5oct\データセット作成用20260415\angio_faz_no_dup.csv"

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