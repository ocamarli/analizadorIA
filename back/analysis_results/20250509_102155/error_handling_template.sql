BEGIN TRY
    -- Main logic here
END TRY
BEGIN CATCH
    -- Error handling logic here
    PRINT ERROR_MESSAGE();
END CATCH;