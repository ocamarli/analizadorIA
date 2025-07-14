DECLARE @newFolio INT;
SET @newFolio = (SELECT MAX(folio) + 1 FROM CatFolios);
IF NOT EXISTS (SELECT 1 FROM CatFolios WHERE folio = @newFolio)
BEGIN
    INSERT INTO CatFolios (folio) VALUES (@newFolio);
END;