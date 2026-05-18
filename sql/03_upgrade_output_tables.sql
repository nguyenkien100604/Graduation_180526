-- Chạy nếu DB đã tạo từ bản cũ (có dbo.AnomalyResults, chưa có RankRFM / IsolationOutput)
USE GraduationBanking;
GO

IF OBJECT_ID(N'dbo.AnomalyResults', N'U') IS NOT NULL
   AND OBJECT_ID(N'dbo.IsolationOutput', N'U') IS NULL
BEGIN
    EXEC sp_rename N'dbo.AnomalyResults', N'IsolationOutput';
END
GO

IF OBJECT_ID(N'dbo.IsolationOutput', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.IsolationOutput (
        TransactionID   INT             NOT NULL,
        CustomerID      INT             NOT NULL,
        IsAnomaly       INT             NOT NULL,
        AnomalyLabel    NVARCHAR(50)    NOT NULL,
        RunAt           DATETIME2(0)    NOT NULL CONSTRAINT DF_IsolationOutput_RunAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT PK_IsolationOutput PRIMARY KEY CLUSTERED (TransactionID)
    );
END
GO

-- Nếu RankRFM sai schema (bản cũ theo CustomerID), chạy thêm: sql/04_fix_output_tables_like_csv.sql
GO
