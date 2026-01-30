SELECT
    s.name AS SchemaName,
    t.name AS TableName,
    o.type_desc AS ObjectType,      -- e.g., 'USER_TABLE'
    t.create_date AS CreatedDate
FROM sys.tables AS t
JOIN sys.schemas AS s
    ON t.schema_id = s.schema_id
JOIN sys.objects AS o
    ON o.object_id = t.object_id
WHERE s.name = N'oml40'
  AND t.name = N'daily_field_parameters'
ORDER BY t.name;
``