BEGIN TRANSACTION;

CREATE TABLE new_files (
    id INTEGER PRIMARY KEY NOT NULL,
    uploader_id REFERENCES users(id) NOT NULL,
    uploader_hidden BOOLEAN NOT NULL,
    upload_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expiration_datetime TIMESTAMP NULL,
    filename VARCHAR NULL,
    data BLOB NOT NULL,
    decrypted_data_hash CHAR(32) NULL,
    mime_type VARCHAR NOT NULL DEFAULT 'application/octet-stream'
);

INSERT INTO new_files SELECT * FROM files;

DROP TABLE files;
ALTER TABLE new_files RENAME TO files;

COMMIT;
