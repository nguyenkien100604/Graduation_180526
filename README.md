# Graduation Banking — Phân tích giao dịch ngân hàng

<<<<<<< HEAD
**Graduation Banking** là hệ thống phân tích dữ liệu giao dịch ngân hàng end-to-end, xây dựng cho đồ án tốt nghiệp. Hệ thống tập trung khoảng **20.000 giao dịch** vào **SQL Server** làm nguồn dữ liệu duy nhất, cho phép **thu thập và chuẩn hóa** từ CSV, Excel, JSON hay cả văn bản Word; **phân tích hành vi** qua phân khúc RFM và khám phá đa chiều (sản phẩm, kênh, phí, phân khúc khách); **phát hiện giao dịch bất thường** bằng mô hình học máy không giám sát (Isolation Forest); và **trình bày kết quả** trên Power BI để bộ phận vận hành, rủi ro và kinh doanh theo dõi xu hướng, đánh giá rủi ro và định hướng chăm sóc khách hàng — thay vì làm việc rời rạc trên file CSV.
=======
Graduation Banking là hệ thống phân tích dữ liệu giao dịch ngân hàng end-to-end, xây dựng cho đồ án tốt nghiệp. Hệ thống tập trung khoảng 20.000 giao dịch vào SQL Server làm nguồn dữ liệu duy nhất, cho phép thu thập và chuẩn hóa từ CSV, Excel, JSON hay cả văn bản Word; phân tích hành vi qua phân khúc RFM và khám phá đa chiều (sản phẩm, kênh, phí, phân khúc khách); phát hiện giao dịch bất thường bằng mô hình học máy không giám sát (Isolation Forest); và trình bày kết quả trên Power BI để bộ phận vận hành, rủi ro và kinh doanh theo dõi xu hướng, đánh giá rủi ro và định hướng chăm sóc khách hàng — thay vì làm việc rời rạc trên file CSV.


>>>>>>> a6a0ee0b8dbb4cddf8df0ac5c746ccd7792c3e0f

---

## Tổng quan dự án

### Bối cảnh

Dataset mô phỏng hoạt động tài chính hàng ngày của khách hàng ngân hàng trên nhiều **sản phẩm** (Checking, Loan, Mortgage, Insurance, …), **kênh giao dịch** (Online, Branch, ATM, Mobile) và **chi nhánh** địa lý (các thành phố Tây Ban Nha với tọa độ GPS). Mỗi bản ghi gắn thông tin khách hàng: điểm tín dụng, thu nhập, phân khúc, sản phẩm gợi ý.

Trong môi trường ngân hàng hiện đại, khối lượng giao dịch lớn và đa dạng kênh đòi hỏi:

- Công cụ **tập trung hóa dữ liệu** (thay vì file CSV rời rạc)
- Khả năng **bổ sung dữ liệu** từ nhiều nguồn (file, form, văn bản)
- Pipeline **phân tích lặp lại được** (ETL → ML → dashboard)

Dự án giải quyết bài toán đó bằng kiến trúc **SQL Server-centric**: mọi module đọc/ghi qua database `GraduationBanking`.

### Mục tiêu

| Mục tiêu | Cách đạt được |
|----------|----------------|
| Phát hiện giao dịch **bất thường** (anomaly) | Isolation Forest, LOF, trực quan PCA |
| Phân khúc khách hàng theo **hành vi tài chính** | Phân tích RFM (Recency, Frequency, Monetary) |
| Hiểu **rủi ro & cơ hội bán hàng** | EDA theo segment, fees, channel |
| **Vận hành dữ liệu** bền vững | SQL master + backup + ingest đa định dạng |
| **Báo cáo** cho người không chuyên kỹ thuật | Power BI kết nối trực tiếp SQL |

### Phạm vi & đầu ra (deliverables)

| Deliverable | Mô tả |
|-------------|--------|
| Database `GraduationBanking` | 4 bảng, schema chuẩn hóa |
| `tools/` | Ứng dụng nhập liệu Streamlit + CLI |
| `bank_transaction.ipynb` | Notebook EDA, RFM, anomaly, biểu đồ |
| `bank_transaction.pbix` | Dashboard Power BI |
| `samples/` | Dataset gốc + file demo import |

### Công nghệ

| Lớp | Công nghệ |
|-----|-----------|
| Database | SQL Server, SSMS, ODBC Driver 17, SQLAlchemy |
| Backend / ETL | Python 3.10+, pandas, scikit-learn |
| Ingestion UI | Streamlit |
| Phân tích | Jupyter, matplotlib, seaborn, plotly |
| AI (tùy chọn) | Groq, Google Gemini |
| Báo cáo | Power BI Desktop |

---

## Cấu trúc dự án

```
Graduation_test/
│
├── sql/                              # Lớp dữ liệu — khởi tạo schema
│   ├── 01_create_database.sql        #   Tạo database GraduationBanking
│   └── 02_create_tables.sql          #   4 bảng: Transactions, Backup, IsolationOutput, RankRFM
│
├── samples/                          # Dữ liệu mẫu & dataset gốc
│   ├── Banking_Transactional_Dataset.csv   # Master ~20k dòng (import lần đầu)
│   ├── RankRFM.csv                         # Lookup 11 segment RFM
│   └── mau_import_transaction.*            # Demo import đa định dạng
│
├── tools/                            # Lớp ứng dụng — ingest & kết nối SQL
│   ├── db_config.py                  #   ODBC/SQLAlchemy (.env)
│   ├── ingest_core.py                #   Validate, backup, ghi Transactions
│   ├── ingest_app.py                 #   UI Streamlit
│   ├── ingest_cli.py                 #   Import CLI
│   ├── file_importer.py              #   Parser đa định dạng
│   ├── column_mapper.py              #   Map cột → schema chuẩn
│   ├── text_parser.py                #   Trích xuất DOCX/TXT (offline)
│   ├── ai_client.py                  #   Groq / Gemini
│   └── notebook_sql.py               #   Bridge Jupyter ↔ SQL
│
├── ETL_data/                         # Lớp phân tích — pipeline ML
│   └── bank_transaction.ipynb
│
├── PowerBI/
│   └── bank_transaction.pbix
│
├── img/                              # Sơ đồ kiến trúc (README)
│   └── ChatGPT Image May 18, 2026, 10_06_04 PM.png
│
├── .env.example
├── requirements.txt
└── README.md
```

| Thư mục | Vai trò |
|---------|---------|
| `sql/` | DDL — chạy một lần khi triển khai |
| `samples/` | Dữ liệu tĩnh; nạp vào SQL rồi dùng qua pipeline |
| `tools/` | **Ingestion layer** — đưa dữ liệu vào `dbo.Transactions` |
| `ETL_data/` | **Analytics layer** — ETL, RFM, anomaly detection |
| `PowerBI/` | **Presentation layer** — đọc SQL, không ghi ngược |

---

## Kiến trúc hệ thống

### Mô hình 3 tầng

![Kiến trúc 3 tầng — Presentation, Application, Data Layer](<img/Flow.png>)

*Chú thích trên sơ đồ:* **INSERT** (ingest → `Transactions`) · **SELECT** (notebook/Power BI đọc SQL) · **UPSERT** (notebook ghi `RankRFM`, `IsolationOutput`) · **snapshot** (backup trước import) · **SELECT (Power BI)** (đọc báo cáo).

### Pipeline dữ liệu

| Pipeline | Đầu vào | Xử lý chính | Đầu ra |
|----------|---------|-------------|--------|
| **Ingestion** | CSV, JSON, XLSX, DOCX, TXT, form | Parse → map cột → validate → backup (tùy chọn) → insert | `dbo.Transactions` |
| **Analytics** | `dbo.Transactions` | Làm sạch, quy USD, EDA, RFM, Isolation Forest, PCA | `dbo.RankRFM`, `dbo.IsolationOutput` |
| **Reporting** | 3 bảng SQL | Aggregate, filter, visualize | Dashboard Power BI |

### Mô hình dữ liệu

**`dbo.Transactions`** — single source of truth (~20.004 giao dịch):

| Nhóm | Cột | Ý nghĩa |
|------|-----|---------|
| Giao dịch | `TransactionID`, `TransactionDate`, `TransactionType`, `Amount`, `Currency` | Định danh, thời gian, loại, số tiền |
| Sản phẩm | `ProductCategory`, `ProductSubcategory` | Checking, Loan, Mortgage, Insurance, … |
| Địa lý / kênh | `BranchCity`, `BranchLat`, `BranchLong`, `Channel` | Chi nhánh, GPS, Online/Branch/ATM |
| Phí | `CreditCardFees`, `InsuranceFees`, `LatePaymentAmount` | Các khoản phí liên quan |
| Khách hàng | `CustomerID`, `CustomerScore`, `MonthlyIncome`, `CustomerSegment`, `RecommendedOffer` | Hồ sơ & gợi ý sản phẩm |

**`dbo.RankRFM`** — dimension lookup (11 segment):

| Segment | Ví dụ mã RFM (`Scores`) |
|---------|-------------------------|
| Champions | 555, 554, 544, … |
| Loyal | 543, 444, 435, … |
| Potential Loyalist | 553, 551, 452, … |
| Promising | 525, 524, 425, … |
| New Customers | 512, 511, 422, … |
| Need Attention | 535, 534, 443, … |
| About To Sleep | 331, 321, 221, … |
| At Risk | 255, 254, 153, … |
| Cannot Lose Them | 155, 154, 214, … |
| Hibernating customers | 332, 322, 111, … |
| Lost customers | 111, 112, 121, … |

**`dbo.IsolationOutput`** — kết quả anomaly mỗi giao dịch:

| Cột | Mô tả |
|-----|--------|
| `TransactionID`, `CustomerID` | Khóa nối với master |
| `IsAnomaly` | 0 = bình thường, 1 = bất thường |
| `AnomalyLabel` | Nhãn mô tả (vd. Normal / Anomaly) |

**`dbo.Transactions_Backup`** — audit trail: snapshot toàn bộ bảng master trước mỗi lần import (khi bật backup).

---

## Mô tả chi tiết từng module

### 1. Ingestion (`tools/`)

Cho phép bổ sung dữ liệu vào `dbo.Transactions` mà không cần sửa notebook.

| Thành phần | Chức năng |
|------------|-----------|
| `file_importer.py` | Đọc CSV, JSON, XLSX, DOCX, TXT, TSV; tự nhận delimiter / bảng Word |
| `column_mapper.py` | Ánh xạ tên cột (fuzzy + alias EN/VI); tùy chọn AI (Groq/Gemini) |
| `text_parser.py` | Trích xuất giao dịch từ DOCX/TXT tiếng Việt — **không cần API** |
| `ingest_core.py` | Validate schema, kiểm tra trùng `TransactionID`, tự gán ID, backup, ghi SQL |
| `ingest_app.py` | Giao diện web: nhập tay + upload file |
| `ingest_cli.py` | Dòng lệnh cho automation / import hàng loạt |

**Quy tắc validate:** 19 cột bắt buộc, `TransactionDate` parse được, `TransactionID` không trùng DB (hoặc để trống để tự gán).

### 2. Analytics (`bank_transaction.ipynb`)

Pipeline phân tích chính — đọc SQL, xử lý trong memory, ghi kết quả trở lại SQL.

| Giai đoạn | Nội dung | Thư viện / kỹ thuật |
|-----------|----------|---------------------|
| **Load & clean** | Đọc `Transactions`, chuẩn hóa tên cột, giảm memory | pandas, `CFG` class |
| **EDA** | Phân bố Amount, segment, channel; ma trận tương quan; biểu đồ | matplotlib, seaborn, plotly |
| **Feature engineering** | Quy đổi USD, mã hóa categorical, flags phí | Custom transforms |
| **RFM** | Tính R/F/M theo `CustomerID`, gán `rfm_segment` | Business rules + `RankRFM` lookup |
| **Anomaly detection** | Isolation Forest (`contamination≈1.5%`), so sánh LOF | scikit-learn |
| **Visualization** | PCA 2D (normal vs anomaly), boxplot, scatter | PCA, plotly |
| **Export SQL** | `save_rank_rfm_sql()`, `save_isolation_sql()` | `notebook_sql.py` |

### 3. Reporting (`PowerBI/`)

- Kết nối **SQL Server** → database `GraduationBanking`
- Mô hình star đơn giản: `Transactions` làm fact, `RankRFM` dimension, `IsolationOutput` mở rộng fact
- **Refresh** sau mỗi lần chạy notebook hoặc import dữ liệu mới

---

## Chạy dự án từ đầu

Thực hiện **theo thứ tự**.

### Bước 0 — Môi trường

```powershell
cd D:\Graduation_test
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env`:

```env
DB_SERVER=DESKTOP-XXX
DB_NAME=GraduationBanking
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUSTED_CONNECTION=yes
```

```powershell
python -c "import sys; sys.path.insert(0,'tools'); from db_config import test_connection; print(test_connection())"
```

### Bước 1 — Tạo database (SSMS)

Chạy F5: `sql/01_create_database.sql` → `sql/02_create_tables.sql`

### Bước 2 — Import dataset gốc

```powershell
python tools/ingest_cli.py samples\Banking_Transactional_Dataset.csv --no-backup
```

```powershell
python -c "import sys; sys.path.insert(0,'tools'); from ingest_core import save_rank_rfm_lookup; print(save_rank_rfm_lookup())"
```

```sql
SELECT COUNT(*) FROM dbo.Transactions;   -- ~20004
```

**Import lại:** `TRUNCATE TABLE dbo.Transactions;` → chạy lại CLI.

### Bước 3 — Notebook ETL/ML

`ETL_data/bank_transaction.ipynb` → **Kernel Restart** → **Run All**

| Bước trong notebook | Ghi SQL |
|---------------------|---------|
| `CFG.read_sql_safe()` | Đọc `Transactions` |
| `CFG.save_rank_rfm_sql()` | Ghi `RankRFM` |
| `CFG.save_isolation_sql()` | Ghi `IsolationOutput` |

### Bước 4 — Power BI

Mở `PowerBI/bank_transaction.pbix` → Refresh dataset từ SQL Server.

---

## Chạy từng module

| Module | Lệnh |
|--------|------|
| Streamlit | `streamlit run tools/ingest_app.py` |
| CLI import | `python tools/ingest_cli.py <file>` |
| Notebook | Run All `bank_transaction.ipynb` |
| Power BI | Mở `.pbix` → Refresh |

```powershell
python tools/ingest_cli.py samples\mau_import_transaction.csv
python tools/ingest_cli.py samples\mau_import_transaction.docx
python tools/ingest_cli.py samples\mau_import_transaction.json --ai-map
```

---

## Cấu hình AI (tùy chọn)

| Provider | Đăng ký |
|----------|---------|
| **Groq** (khuyến nghị) | [console.groq.com](https://console.groq.com) |
| **Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

```env
AI_PROVIDER=auto
AI_PROVIDER_ORDER=groq,google
GROQ_API_KEY=...
GOOGLE_API_KEY=...
```

---


