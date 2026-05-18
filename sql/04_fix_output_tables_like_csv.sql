-- Đồng bộ schema với file CSV gốc (isolation_output.csv, RankRFM.csv)
USE GraduationBanking;
GO

IF OBJECT_ID(N'dbo.IsolationOutput', N'U') IS NOT NULL
    DROP TABLE dbo.IsolationOutput;
GO

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

CREATE TABLE dbo.RankRFM (
    Segment         NVARCHAR(100)   NOT NULL,
    Scores          NVARCHAR(MAX)   NOT NULL,
    CONSTRAINT PK_RankRFM PRIMARY KEY CLUSTERED (Segment)
);
GO
