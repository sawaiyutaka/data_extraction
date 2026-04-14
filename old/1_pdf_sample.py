from pathlib import Path
import csv

# ===== 設定 =====
input_folder = Path(r"F:\20260323")   # 対象フォルダに変更
output_csv = Path(r"pdf_filenames.csv")       # 出力CSV名

# ===== PDFファイルを再帰的に取得 =====
pdf_files = sorted(input_folder.rglob("*.pdf"))

# ===== CSVに保存（1列） =====
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["filename"])  # ヘッダー
    for pdf in pdf_files:
        writer.writerow([pdf.stem])

print(f"完了: {len(pdf_files)} 件のPDFファイル名を {output_csv} に保存しました。")