-- Chạy sau 01_create_database.sql
USE GraduationBanking;
GO

IF OBJECT_ID(N'dbo.Transactions', N'U') IS NOT NULL
    DROP TABLE dbo.Transactions;
GO

CREATE TABLE dbo.Transactions (
    TransactionID       INT             NOT NULL,
    CustomerID          INT             NOT NULL,
    TransactionDate     DATETIME2(0)    NOT NULL,
    TransactionType     NVARCHAR(50)    NOT NULL,
    Amount              DECIMAL(18, 6)  NOT NULL,
    ProductCategory     NVARCHAR(100)   NOT NULL,
    ProductSubcategory  NVARCHAR(50)    NOT NULL,
    BranchCity          NVARCHAR(100)   NOT NULL,
    BranchLat           FLOAT           NOT NULL,
    BranchLong          FLOAT           NOT NULL,
    Channel             NVARCHAR(50)    NOT NULL,
    Currency            NVARCHAR(10)    NOT NULL,
    CreditCardFees      DECIMAL(18, 6)  NOT NULL,
    InsuranceFees       DECIMAL(18, 6)  NOT NULL,
    LatePaymentAmount   DECIMAL(18, 6)  NOT NULL,
    CustomerScore       INT             NOT NULL,
    MonthlyIncome       DECIMAL(18, 6)  NOT NULL,
    CustomerSegment     NVARCHAR(100)   NOT NULL,
    RecommendedOffer    NVARCHAR(200)   NOT NULL,
    CONSTRAINT PK_Transactions PRIMARY KEY CLUSTERED (TransactionID)
);
GO

CREATE INDEX IX_Transactions_CustomerID ON dbo.Transactions (CustomerID);
CREATE INDEX IX_Transactions_TransactionDate ON dbo.Transactions (TransactionDate);
GO

IF OBJECT_ID(N'dbo.Transactions_Backup', N'U') IS NOT NULL
    DROP TABLE dbo.Transactions_Backup;
GO

CREATE TABLE dbo.Transactions_Backup (
    BackupId            BIGINT IDENTITY(1,1) NOT NULL,
    BackedUpAt          DATETIME2(0)    NOT NULL CONSTRAINT DF_Transactions_Backup_BackedUpAt DEFAULT (SYSUTCDATETIME()),
    TransactionID       INT             NOT NULL,
    CustomerID          INT             NOT NULL,
    TransactionDate     DATETIME2(0)    NOT NULL,
    TransactionType     NVARCHAR(50)    NOT NULL,
    Amount              DECIMAL(18, 6)  NOT NULL,
    ProductCategory     NVARCHAR(100)   NOT NULL,
    ProductSubcategory  NVARCHAR(50)    NOT NULL,
    BranchCity          NVARCHAR(100)   NOT NULL,
    BranchLat           FLOAT           NOT NULL,
    BranchLong          FLOAT           NOT NULL,
    Channel             NVARCHAR(50)    NOT NULL,
    Currency            NVARCHAR(10)    NOT NULL,
    CreditCardFees      DECIMAL(18, 6)  NOT NULL,
    InsuranceFees       DECIMAL(18, 6)  NOT NULL,
    LatePaymentAmount   DECIMAL(18, 6)  NOT NULL,
    CustomerScore       INT             NOT NULL,
    MonthlyIncome       DECIMAL(18, 6)  NOT NULL,
    CustomerSegment     NVARCHAR(100)   NOT NULL,
    RecommendedOffer    NVARCHAR(200)   NOT NULL,
    CONSTRAINT PK_Transactions_Backup PRIMARY KEY CLUSTERED (BackupId)
);
GO

IF OBJECT_ID(N'dbo.IsolationOutput', N'U') IS NOT NULL
    DROP TABLE dbo.IsolationOutput;
GO

-- Giống isolation_output.csv (4 cột)
CREATE TABLE dbo.IsolationOutput (
    TransactionID   INT             NOT NULL,
    CustomerID      INT             NOT NULL,
    IsAnomaly       INT             NOT NULL,
    AnomalyLabel    NVARCHAR(50)    NOT NULL,
    CONSTRAINT PK_IsolationOutput PRIMARY KEY CLUSTERED (TransactionID)
);
GO

IF OBJECT_ID(N'dbo.RankRFM', N'U') IS NOT NULL
    DROP TABLE dbo.RankRFM;
GO

-- Giống RankRFM.csv: bảng tra cứu Segment -> Scores
CREATE TABLE dbo.RankRFM (
    Segment         NVARCHAR(100)   NOT NULL,
    Scores          NVARCHAR(MAX)   NOT NULL,
    CONSTRAINT PK_RankRFM PRIMARY KEY CLUSTERED (Segment)
);
GO
