-- Chạy trong SSMS (SQL Server Management Studio)
-- File → New Query → Execute (F5)

IF DB_ID(N'GraduationBanking') IS NULL
BEGIN
    CREATE DATABASE GraduationBanking;
END
GO

USE GraduationBanking;
GO
