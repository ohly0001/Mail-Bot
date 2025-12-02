CREATE DATABASE IF NOT EXISTS Mailbot;
USE Mailbot;

CREATE TABLE address_whitelist (
    whitelist_uid INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    whitelisted_name VARCHAR(100),
    whitelisted_address VARCHAR(255) NOT NULL UNIQUE,
    whitelisted_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE emails (
    email_uid_unique INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email_uid INT UNSIGNED NULL,
    email_parent_id VARCHAR(255) NULL,
    email_id VARCHAR(255) NOT NULL UNIQUE,
    subject_line VARCHAR(512),
    sender_name VARCHAR(255),
    sender_address VARCHAR(255),
    body_text MEDIUMTEXT,
    sent_on DATETIME,
    read_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_parent_id)
        REFERENCES emails(email_id)
        ON DELETE CASCADE,
    FOREIGN KEY (sender_address)
        REFERENCES address_whitelist(whitelisted_address)
        ON DELETE CASCADE
);

CREATE INDEX email_idx ON emails(email_id, email_parent_id);