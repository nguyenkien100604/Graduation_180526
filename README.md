# Graduation_180526 — Banking Transaction Analytics Pipeline

Dự án này xây dựng một pipeline phân tích giao dịch ngân hàng từ dữ liệu đầu vào nhiều định dạng đến SQL Server, notebook xử lý dữ liệu và báo cáo Power BI. Mục tiêu chính là giúp người dùng có thể nhập thêm dữ liệu giao dịch mới, chuẩn hóa dữ liệu, chạy lại notebook phân tích và refresh dashboard Power BI với dữ liệu mới nhất.

## 1. Tổng quan hệ thống

Pipeline của dự án có thể được hiểu theo luồng sau:

```text
File đầu vào
CSV / TSV / JSON / XLSX / XLS / DOCX / TXT
        |
        v
tools/file_importer.py
Đọc file nhiều định dạng
        |
        v
tools/column_mapper.py
Chuẩn hóa tên cột bằng fuzzy matching hoặc AI mapping tùy chọn
        |
        v
tools/ingest_core.py
Validate dữ liệu, tự gán TransactionID nếu cần, backup và ghi vào SQL Server
        |
        v
SQL Server
Transactions / Transactions_Backup / IsolationOutput / RankRFM
        |
        v
ETL_data/bank_transaction.ipynb
Tiền xử lý, phân tích, phát hiện bất thường, RFM/segmentation
        |
        v
PowerBI/bank_transaction.pbix
Dashboard báo cáo và trực quan hóa
```

## 2. Chức năng chính

- Tạo database và các bảng phục vụ phân tích giao dịch ngân hàng trên SQL Server.
- Import dữ liệu mới vào bảng `dbo.Transactions` bằng giao diện Streamlit hoặc dòng lệnh CLI.
- Hỗ trợ nhiều định dạng đầu vào: `.csv`, `.tsv`, `.json`, `.xlsx`, `.xls`, `.docx`, `.txt`.
- Chuẩn hóa tên cột đầu vào về schema chuẩn của bảng `Transactions` bằng fuzzy matching.
- Tùy chọn dùng AI để map tên cột hoặc trích xuất giao dịch từ file văn bản/DOCX.
- Backup dữ liệu hiện có vào `dbo.Transactions_Backup` trước khi ghi thêm dữ liệu mới.
- Notebook đọc dữ liệu từ SQL Server, chạy lại các bước phân tích và ghi kết quả đầu ra về SQL.
- Power BI dashboard có thể refresh lại từ các bảng SQL sau khi dữ liệu được cập nhật.

## 3. Cấu trúc thư mục

```text
Graduation_180526/
├── ETL_data/
│   └── bank_transaction.ipynb        # Notebook xử lý ETL, phân tích và mô hình
├── PowerBI/
│   └── bank_transaction.pbix         # File dashboard Power BI
├── samples/
│   ├── RankRFM.csv                   # Bảng tra cứu RFM segment -> score
│   ├── isolation_output.csv          # Kết quả mẫu cho IsolationOutput
│   ├── mau_import_transaction.csv    # File mẫu import giao dịch
│   ├── mau_import_transaction.docx
│   ├── mau_import_transaction.json
│   ├── mau_import_transaction.txt
│   └── mau_import_transaction.xlsx
├── sql/
│   ├── 01_create_database.sql        # Tạo database GraduationBanking
│   ├── 02_create_tables.sql          # Tạo các bảng chính
│   ├── 03_huong_dan_ssms.txt         # Hướng dẫn thao tác trên SSMS
│   ├── 03_upgrade_output_tables.sql  # Nâng cấp bảng output nếu cần
│   └── 04_fix_output_tables_like_csv.sql
├── tools/
│   ├── ai_client.py                  # Client AI: Groq / Google Gemini / OpenAI
│   ├── column_mapper.py              # Map cột đầu vào về schema chuẩn
│   ├── db_config.py                  # Cấu hình kết nối SQL Server
│   ├── file_importer.py              # Đọc file CSV/JSON/Excel/DOCX/TXT
│   ├── ingest_app.py                 # Giao diện Streamlit để import dữ liệu
│   ├── ingest_cli.py                 # CLI import file vào SQL Server
│   ├── ingest_core.py                # Logic validate, backup, append SQL
│   ├── migrate_csv_to_sql.py         # Import CSV master vào SQL
│   ├── notebook_sql.py               # Helper đọc/ghi SQL cho notebook
│   ├── seed_outputs_from_csv.py      # Nạp RankRFM và IsolationOutput từ CSV mẫu
│   └── text_parser.py                # Parser cục bộ cho dữ liệu dạng văn bản
├── .env.example                      # Mẫu cấu hình môi trường
└── requirements.txt                  # Danh sách thư viện Python
```

> Lưu ý: nếu trong thư mục `samples/` có file tạm dạng `~$...docx`, đó thường là file lock tạm của Microsoft Word và có thể xóa trước khi nộp/publish repo.

## 4. Yêu cầu hệ thống

- Python 3.10 trở lên.
- SQL Server và SQL Server Management Studio (SSMS).
- ODBC Driver 17 for SQL Server hoặc driver tương thích.
- Power BI Desktop để mở và refresh file `.pbix`.
- Git để clone repository.

## 5. Cài đặt môi trường Python

Clone repository:

```bash
git clone https://github.com/nguyenkien100604/Graduation_180526.git
cd Graduation_180526
```

Tạo môi trường ảo:

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo trên Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Cài thư viện:

```bash
pip install -r requirements.txt
```

## 6. Thiết lập SQL Server

Mở SSMS và chạy các script SQL theo thứ tự:

```text
sql/01_create_database.sql
sql/02_create_tables.sql
```

Hai script còn lại chỉ cần chạy khi bạn đang nâng cấp database cũ hoặc cần đồng bộ lại cấu trúc bảng output:

```text
sql/03_upgrade_output_tables.sql
sql/04_fix_output_tables_like_csv.sql
```

Sau khi chạy, database mặc định là:

```text
GraduationBanking
```

Các bảng chính gồm:

- `dbo.Transactions`: dữ liệu giao dịch chính.
- `dbo.Transactions_Backup`: snapshot backup trước khi import dữ liệu mới.
- `dbo.IsolationOutput`: kết quả phát hiện bất thường.
- `dbo.RankRFM`: bảng tra cứu phân khúc RFM.

## 7. Cấu hình file `.env`

Sao chép file mẫu:

```powershell
Copy-Item .env.example .env
```

Sau đó chỉnh lại nội dung `.env` theo SQL Server trên máy của bạn:

```env
DB_SERVER=YOUR_SERVER_NAME
DB_NAME=GraduationBanking
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes

DB_SCHEMA=dbo
DB_TABLE_TRANSACTIONS=Transactions
DB_TABLE_BACKUP=Transactions_Backup
DB_TABLE_ISOLATION=IsolationOutput
DB_TABLE_RFM=RankRFM
```

Nếu dùng SQL Authentication thay vì Windows Authentication:

```env
DB_TRUSTED_CONNECTION=no
DB_USER=your_username
DB_PASSWORD=your_password
```

Cấu hình AI là tùy chọn. Nếu không dùng AI mapping hoặc AI extraction, bạn có thể bỏ qua phần này.

```env
AI_PROVIDER=auto
AI_PROVIDER_ORDER=groq,google,openai

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.0-flash-lite
GEMINI_MODEL_FALLBACKS=gemini-1.5-flash-8b,gemini-2.0-flash-lite

OPENAI_API_KEY=your_openai_api_key
```

> Không commit file `.env` lên GitHub vì file này có thể chứa thông tin kết nối database và API key.

## 8. Schema dữ liệu giao dịch

Dữ liệu đầu vào sau khi chuẩn hóa sẽ được map về các cột sau:

| Cột | Ý nghĩa |
|---|---|
| `TransactionID` | Mã giao dịch. Có thể để trống toàn bộ để hệ thống tự gán. |
| `CustomerID` | Mã khách hàng. |
| `TransactionDate` | Ngày/giờ giao dịch. |
| `TransactionType` | Loại giao dịch. |
| `Amount` | Giá trị giao dịch. |
| `ProductCategory` | Nhóm sản phẩm/dịch vụ. |
| `ProductSubcategory` | Nhóm con sản phẩm/dịch vụ. |
| `BranchCity` | Thành phố/chi nhánh. |
| `BranchLat` | Vĩ độ chi nhánh. |
| `BranchLong` | Kinh độ chi nhánh. |
| `Channel` | Kênh giao dịch. |
| `Currency` | Loại tiền tệ. |
| `CreditCardFees` | Phí thẻ tín dụng. |
| `InsuranceFees` | Phí bảo hiểm. |
| `LatePaymentAmount` | Số tiền thanh toán trễ. |
| `CustomerScore` | Điểm khách hàng. |
| `MonthlyIncome` | Thu nhập tháng của khách hàng. |
| `CustomerSegment` | Phân khúc khách hàng. |
| `RecommendedOffer` | Gợi ý ưu đãi/sản phẩm. |

## 9. Import dữ liệu bằng Streamlit

Chạy giao diện import dữ liệu:

```bash
streamlit run tools/ingest_app.py
```

Giao diện này cho phép:

- Kiểm tra kết nối SQL Server.
- Xem số dòng hiện có trong bảng `Transactions`.
- Chọn backup dữ liệu trước khi ghi thêm.
- Bật/tắt AI mapping tên cột.
- Bật/tắt AI extraction cho file DOCX/TXT.
- Import dữ liệu thủ công hoặc import từ file.
- Preview dữ liệu trước khi ghi vào database.
```

## 11. Import CSV master cũ vào SQL Server

Nếu bạn có file CSV master và muốn nạp trực tiếp vào `dbo.Transactions`, dùng:

```bash
python tools/migrate_csv_to_sql.py path\to\file.csv
```

Nếu muốn xóa dữ liệu cũ trong `Transactions` trước khi import:

```bash
python tools/migrate_csv_to_sql.py path\to\file.csv --replace
```

## 12. Nạp dữ liệu output mẫu

Để nạp `RankRFM.csv` và `isolation_output.csv` từ thư mục `samples/` vào SQL Server:

```bash
python tools/seed_outputs_from_csv.py
```

Script này sẽ ghi dữ liệu vào:

- `dbo.RankRFM`
- `dbo.IsolationOutput`

## 13. Chạy notebook ETL và phân tích

Mở notebook:

```text
ETL_data/bank_transaction.ipynb
```

Nếu cần gọi các helper SQL trong notebook, có thể thêm đoạn sau ở đầu notebook:

```python
from pathlib import Path
import sys

ROOT = Path.cwd()
TOOLS = ROOT / "tools" if (ROOT / "tools").exists() else ROOT.parent / "tools"
sys.path.insert(0, str(TOOLS))

from notebook_sql import (
    test_sql_connection,
    load_transactions,
    load_rank_rfm,
    load_isolation_output,
    save_isolation_output,
    save_rank_rfm_lookup,
    sql_table_summary,
)
```

Luồng làm việc khuyến nghị:

1. Import dữ liệu mới bằng Streamlit hoặc CLI.
2. Kiểm tra dữ liệu trong `dbo.Transactions`.
3. Mở và chạy lại notebook `bank_transaction.ipynb`.
4. Ghi lại kết quả anomaly/RFM vào SQL nếu notebook có tạo output mới.
5. Mở Power BI và refresh dashboard.

## 14. Refresh Power BI dashboard

Mở file:

```text
PowerBI/bank_transaction.pbix
```

Trong Power BI Desktop:

1. Kiểm tra lại data source đang trỏ về SQL Server đúng với `.env`.
2. Đảm bảo database là `GraduationBanking`.
3. Refresh các bảng liên quan: `Transactions`, `IsolationOutput`, `RankRFM`.
4. Kiểm tra dashboard sau khi refresh.

## 15. Kiểm tra nhanh kết nối và số dòng bảng

Có thể chạy nhanh trong Python:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path("tools").resolve()))

from db_config import test_connection
from ingest_core import table_row_count

ok, msg = test_connection()
print(ok, msg)
print("Rows in Transactions:", table_row_count())
```

## 18. Tác giả

Repository: `nguyenkien100604/Graduation_180526`

## 19. License

Dự án hiện chưa khai báo license. Nếu muốn chia sẻ công khai, nên bổ sung file `LICENSE` phù hợp với mục đích sử dụng.
