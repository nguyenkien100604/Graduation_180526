# Graduation Banking — Phân tích giao dịch ngân hàng

Dự án đồ án tốt nghiệp: lưu trữ dữ liệu giao dịch trên **SQL Server (SSMS)**, phân tích bằng **Jupyter notebook**, nhập liệu qua **Streamlit/CLI**, và trực quan hóa bằng **Power BI**.

---

## Tính năng chính

| Thành phần | Mô tả |
|------------|--------|
| **SQL Server** | Database `GraduationBanking` — master, backup, kết quả ETL |
| **Notebook ETL** | RFM, Isolation Forest, PCA, biểu đồ — đọc/ghi SQL |
| **Import đa định dạng** | CSV, JSON, XLSX, DOCX, TXT → `dbo.Transactions` |
| **Map cột tự động** | Fuzzy + alias; tùy chọn AI (Groq / Gemini) |
| **DOCX văn bản** | Parser cục bộ (không cần API) hoặc AI trích xuất |
| **Power BI** | Kết nối trực tiếp các bảng `dbo.*` |

---

## Cấu trúc thư mục

```
Graduation_test/
├── ETL_data/
│   └── bank_transaction.ipynb    # Pipeline phân tích chính
├── sql/
│   ├── 01_create_database.sql
│   └── 02_create_tables.sql
├── PowerBI/
│   └── bank_transaction.pbix
├── tools/
│   ├── db_config.py              # Kết nối SQL (.env)
│   ├── ingest_core.py            # Validate, backup, ghi SQL
│   ├── ingest_app.py             # Giao diện Streamlit
│   ├── ingest_cli.py             # Import dòng lệnh
│   ├── file_importer.py          # Đọc CSV/JSON/XLSX/DOCX/TXT
│   ├── column_mapper.py          # Map cột → schema Transactions
│   ├── text_parser.py            # Trích xuất DOCX/TXT (không AI)
│   ├── ai_client.py              # Groq / Gemini
│   └── notebook_sql.py           # Helper đọc/ghi cho notebook
├── samples/                      # File mẫu import + RankRFM lookup
├── .env.example                  # Mẫu cấu hình (sao chép thành .env)
├── requirements.txt
└── README.md
```

---

## Yêu cầu hệ thống

- **Windows** (khuyến nghị) với SQL Server + **SSMS**
- **ODBC Driver 17 for SQL Server**
- **Python 3.10+**
- (Tùy chọn) API key **Groq** hoặc **Google AI Studio** cho tính năng AI

---

## Cài đặt nhanh

### 1. SQL Server

1. Cài [SQL Server](https://www.microsoft.com/sql-server/sql-server-downloads) và [SSMS](https://aka.ms/ssmsfullsetup).
2. Trong SSMS, mở và chạy lần lượt (F5):
   - `sql/01_create_database.sql`
   - `sql/02_create_tables.sql`

### 2. Python

```powershell
cd D:\Graduation_test
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. File `.env`

```powershell
copy .env.example .env
```

Chỉnh các biến quan trọng:

```env
DB_SERVER=DESKTOP-XXX          # Tên instance trong SSMS
DB_NAME=GraduationBanking
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes

# AI (tùy chọn) — free: https://console.groq.com
AI_PROVIDER=auto
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_gemini_key
```

> **Lưu ý:** Không commit file `.env` lên Git (chứa mật khẩu / API key).

---

## Cơ sở dữ liệu

| Bảng | Vai trò |
|------|---------|
| `dbo.Transactions` | Dữ liệu giao dịch master (19 cột, ~20k dòng) |
| `dbo.Transactions_Backup` | Snapshot trước mỗi lần import |
| `dbo.IsolationOutput` | Kết quả Isolation Forest: `TransactionID`, `CustomerID`, `IsAnomaly`, `AnomalyLabel` |
| `dbo.RankRFM` | Bảng tra cứu 11 dòng: `Segment` → `Scores` (không phải RFM từng khách) |

---

## Sử dụng

### Nhập dữ liệu (Streamlit)

```powershell
streamlit run tools/ingest_app.py
```

- Tab **Nhập tay** hoặc **Import file**
- Hỗ trợ: `.csv`, `.json`, `.xlsx`, `.xls`, `.docx`, `.txt`, `.tsv`
- Tùy chọn: backup trước khi ghi, AI map cột, AI trích xuất văn bản

File mẫu trong `samples/`:

| File | Ghi chú |
|------|---------|
| `mau_import_transaction.csv` | Cột chuẩn |
| `mau_import_transaction.json` | Nested `transactions` |
| `mau_import_transaction.xlsx` | Excel |
| `mau_import_transaction.txt` | Pipe-delimited, tiếng Việt |
| `mau_import_transaction.docx` | Văn bản tự do (parser cục bộ hoặc AI) |

### Nhập dữ liệu (CLI)

```powershell
python tools/ingest_cli.py samples\mau_import_transaction.csv
python tools/ingest_cli.py samples\mau_import_transaction.docx --ai-extract
python tools/ingest_cli.py samples\mau_import_transaction.json --ai-map
```

### Notebook ETL

1. Mở `ETL_data/bank_transaction.ipynb`.
2. **Kernel → Restart** rồi **Run All** (hoặc chạy lần lượt từ đầu).
3. Cell import tự thêm `tools/` vào `sys.path`; `CFG.read_sql_safe()` đọc `dbo.Transactions`.
4. Sau RFM / Isolation Forest: `CFG.save_rank_rfm_sql()`, `CFG.save_isolation_sql()`.

### Power BI

1. **Get Data** → **SQL Server**
2. Server: tên instance (giống `DB_SERVER`), Database: `GraduationBanking`
3. Chọn: `dbo.Transactions`, `dbo.IsolationOutput`, `dbo.RankRFM`

---

## Cấu hình AI

| Provider | Free? | Cấu hình |
|----------|-------|----------|
| **Groq** | Có (khuyến nghị) | `GROQ_API_KEY` — [console.groq.com](https://console.groq.com) |
| **Google Gemini** | Có (giới hạn) | `GOOGLE_API_KEY` — [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

```env
AI_PROVIDER=auto
AI_PROVIDER_ORDER=groq,google
```

- `AI_PROVIDER=auto`: thử lần lượt khi một provider hết quota.
- DOCX mẫu văn bản: **tắt** «AI trích xuất» vẫn import được (module `text_parser.py`).

---

## Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|-----|------------|
| Không kết nối SQL | Kiểm tra SQL Server đang chạy, `DB_SERVER` trong `.env`, ODBC Driver 17 |
| `ModuleNotFoundError: notebook_sql` | Chạy lại cell import và cell `CFG` trong notebook (đã fix `sys.path`) |
| Gemini `429 quota` | Dùng Groq, đổi `GEMINI_MODEL=gemini-2.0-flash-lite`, hoặc tắt AI |
| SQL `07002` khi insert nhiều dòng | Giảm `chunksize` khi `to_sql` (tối đa ~2100 tham số/câu lệnh) |

---

## Kiểm tra kết nối

```powershell
python -c "import sys; sys.path.insert(0,'tools'); from db_config import test_connection; print(test_connection())"
```

Kết quả mong đợi: `(True, 'DESKTOP-... / GraduationBanking')`.

---

## Tác giả & ghi chú

- Dữ liệu master và kết quả ETL nằm trên **SQL Server**; `samples/RankRFM.csv` là bảng tra cứu segment (11 dòng).
- `dbo.IsolationOutput` được notebook ghi sau khi chạy Isolation Forest.
