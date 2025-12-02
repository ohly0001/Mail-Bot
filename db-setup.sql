CREATE DATABASE IF NOT EXISTS Mailbot;
USE Mailbot;

CREATE TABLE address_whitelist (
    whitelisted_address VARCHAR(256) PRIMARY KEY,
    whitelisted_name VARCHAR(100),
    whitelisted_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE emails (
    email_uid INT UNSIGNED NULL, --not always available
    email_parent_id VARCHAR(255) NULL, --immediete predecessor
    email_id VARCHAR(255) NOT NULL UNIQUE,
    subject_line VARCHAR(512),
    sender_name VARCHAR(255),
    from_address VARCHAR(256),
    body_text MEDIUMTEXT,
    sent_on DATETIME,
    read_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    token_count INT UNSIGNED DEFAULT 0, --cache for recounting efficiency
    FOREIGN KEY (email_parent_id)
        REFERENCES emails(email_id)
        ON DELETE CASCADE,
    FOREIGN KEY (from_address)
        REFERENCES address_whitelist(whitelisted_address)
);

CREATE INDEX email_idx ON emails(email_id, email_parent_id);

--all predecessors
CREATE TABLE email_references (
    email_parent_id VARCHAR(255) NOT NULL,
    email_child_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (email_parent_id)
        REFERENCES emails(email_id)
        ON DELETE CASCADE,
    FOREIGN KEY (email_child_id)
        REFERENCES emails(email_id)
        ON DELETE CASCADE
);

--if part of a multiperson conversion
CREATE TABLE email_recipients (
    email_id VARCHAR(255) NOT NULL,
    recipient_address VARCHAR(256),
    isCC BOOLEAN DEFAULT FALSE, --cannot be 'from' (needed for whitelist) or 'BCC' (hidden)
    FOREIGN KEY (email_id)
        REFERENCES emails(email_id)
        ON DELETE CASCADE
);