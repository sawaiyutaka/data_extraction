from pathlib import Path
import re
import pandas as pd

# PDFのページ数取得用
# 未インストールなら: pip install pypdf
from pypdf import PdfReader

# =========================
# 設定
# =========================
root_dir = Path(r"G:\第5期調査票")   # ← PDFが入っている親フォルダ
output_csv = Path("pdf_page_summary.csv")

# 出力したい列順
target_types = ["EA", "EB", "EC", "EE", "EG", "EH"]

# ファイル名パターン:
# 6桁数字 + "_" + EまたはR + 英字1文字 + ".pdf"
# 例: 100001_EA.pdf / 100021_RH.pdf
pattern = re.compile(r"^(\d{6})_([ER][A-Z])\.pdf$", re.IGNORECASE)

# =========================
# PDFを再帰的に探索して情報取得
# =========================
records = []
skipped_files = []

for pdf_path in root_dir.rglob("*.pdf"):
    m = pattern.match(pdf_path.name)
    if not m:
        skipped_files.append(str(pdf_path))
        continue

    sample_number = m.group(1)
    exam_type = m.group(2).upper()

    # 必要な種別だけ対象にする
    if exam_type not in target_types:
        skipped_files.append(str(pdf_path))
        continue

    try:
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
    except Exception as e:
        print(f"PDF読み取りエラー: {pdf_path} -> {e}")
        page_count = pd.NA

    records.append({
        "SAMPLENUMBER": sample_number,
        "TYPE": exam_type,
        "PAGES": page_count,
        "FILEPATH": str(pdf_path),
    })

# =========================
# データフレーム化
# =========================
df_long = pd.DataFrame(records)

if df_long.empty:
    print("条件に合うPDFが見つかりませんでした。")
else:
    # 同じSAMPLENUMBER, TYPE が複数ある場合に備えて先に確認
    dup = df_long.groupby(["SAMPLENUMBER", "TYPE"]).size().reset_index(name="n")
    dup = dup[dup["n"] > 1]

    if not dup.empty:
        print("同じ SAMPLENUMBER × TYPE のPDFが複数あります。最初の1件を採用します。")
        print(dup)

        # 最初の1件を残す
        df_long = df_long.drop_duplicates(subset=["SAMPLENUMBER", "TYPE"], keep="first")

    # 横持ちに変換
    df_wide = (
        df_long.pivot(index="SAMPLENUMBER", columns="TYPE", values="PAGES")
        .reindex(columns=target_types)
        .reset_index()
        .sort_values("SAMPLENUMBER")
    )

    # CSV出力
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_wide.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("出力完了:", output_csv)
    print(df_wide)

# =========================
# スキップしたファイルの一覧も必要なら表示
# =========================
if skipped_files:
    print("\nファイル名パターン不一致または対象外のためスキップしたPDF:")
    for f in skipped_files:
        print(f)