CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY NOT NULL,
    name VARCHAR(32) UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash CHAR(128) NOT NULL,
    creation_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY NOT NULL,
    owner_id REFERENCES users(id) NOT NULL,
    creation_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expiration_datetime TIMESTAMP NULL
);


CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY NOT NULL,
    uploader_id REFERENCES users(id) NOT NULL,
    uploader_hidden BOOLEAN NOT NULL,
    upload_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expiration_datetime TIMESTAMP NULL,
    filename VARCHAR NULL,
    encrypted_data BLOB NOT NULL,
    encrypted_data_hash CHAR(32) NOT NULL
);
