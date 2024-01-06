ALTER TABLE files RENAME access_count TO data_access_count;
ALTER TABLE files ADD meta_access_count INTEGER NOT NULL DEFAULT 0;
