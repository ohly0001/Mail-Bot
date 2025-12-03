CREATE DATABASE IF NOT EXISTS Mailbot2;
USE Mailbot2;

CREATE TABLE registered_users (
    user_id INT UNSIGNED AUTO_INCREMENT,
    email_address VARCHAR(256),
    alias_name VARCHAR(100),
    registered_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id),
    UNIQUE KEY (email_address)
);

CREATE TABLE email_thread (
    thread_id INT UNSIGNED AUTO_INCREMENT,
    thread_subject VARCHAR(512),
    bot_reply_mode ENUM('natural', 'lazy', 'eager', 'idle') DEFAULT 'lazy', --TODO switch to natural when feature add
    bot_filter_mode ENUM('none', 'exclude', 'include', 'all') DEFAULT 'all', 
    started_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(thread_id)
);

CREATE TABLE email_correspondants (
    thread_id INT UNSIGNED,
    user_id INT UNSIGNED,
    isCC BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (thread_id, user_id),
    FOREIGN KEY (thread_id) REFERENCES email_thread(thread_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES registered_users(user_id) ON DELETE CASCADE
);

CREATE TABLE email_thread_bot_filter (
    thread_id INT UNSIGNED,
    user_id INT UNSIGNED,
    PRIMARY KEY (thread_id, user_id),
    FOREIGN KEY (thread_id) REFERENCES email_thread(thread_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES registered_users(user_id) ON DELETE CASCADE
);

CREATE TABLE thread_message (
    message_id INT UNSIGNED AUTO_INCREMENT,
    predecessor_message_id INT UNSIGNED NULL,
    thread_id INT UNSIGNED,
    content MEDIUMTEXT,
    sent_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(message_id),
    FOREIGN KEY (thread_id) REFERENCES email_thread(thread_id) ON DELETE CASCADE,
    FOREIGN KEY (predecessor_message_id) REFERENCES thread_message(message_id) ON DELETE SET NULL
);

CREATE TABLE thread_message_smtp_data (
    message_id INT UNSIGNED,
    email_id VARCHAR(255),
    email_uid INT UNSIGNED NULL,
    PRIMARY KEY (message_id),
    FOREIGN KEY (message_id) REFERENCES thread_message(message_id) ON DELETE CASCADE
);
