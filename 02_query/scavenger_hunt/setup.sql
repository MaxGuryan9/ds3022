-- ============================================================
-- The Vanishing Dataset — setup.sql
-- Instructor script. Run once per student/team to build a fresh
-- copy of the case database before they begin the hunt.
--
--   duckdb vanishing_dataset.db < setup.sql
--
-- Standard SQL — also runs unmodified in SQLite/Postgres.
-- ============================================================

DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS alibis;
DROP TABLE IF EXISTS suspects;
DROP TABLE IF EXISTS case_log;

-- ---------------------------------------------------------
-- suspects: everyone with badge access to the server room
-- ---------------------------------------------------------
CREATE TABLE suspects (
    suspect_id INTEGER PRIMARY KEY,
    name       VARCHAR(50),
    role       VARCHAR(50),
    badge_code VARCHAR(10),
    status     VARCHAR(20)      -- 'active' or 'terminated'
);

INSERT INTO suspects VALUES (1001, 'Priya Shah',  'Data Engineer', 'PS-114', 'active');
INSERT INTO suspects VALUES (1002, 'Marcus Webb', 'Sysadmin',      'MW-207', 'active');
INSERT INTO suspects VALUES (1003, 'Dana Cho',    'Intern',        'DC-330', 'active');
INSERT INTO suspects VALUES (1004, 'Ilya Petrov', 'Contractor',    'IP-098', 'terminated');
INSERT INTO suspects VALUES (1005, 'Renee Ford',  'Data Engineer', 'RF-221', 'active');

-- ---------------------------------------------------------
-- access_logs: badge swipes recorded the night of the incident
-- (night of 2026-09-09). Note suspect 1005 has TWO swipes on record.
-- ---------------------------------------------------------
CREATE TABLE access_logs (
    log_id     INTEGER PRIMARY KEY,
    suspect_id INTEGER,
    login_time VARCHAR(20),
    terminal   VARCHAR(5)
);

INSERT INTO access_logs VALUES (1, 1001, '2026-09-09 22:10', 'A');
INSERT INTO access_logs VALUES (2, 1002, '2026-09-09 22:45', 'B');
INSERT INTO access_logs VALUES (3, 1003, '2026-09-09 23:05', 'A');
INSERT INTO access_logs VALUES (4, 1004, '2026-09-09 23:50', 'D');
INSERT INTO access_logs VALUES (5, 1005, '2026-09-09 23:41', 'C');
INSERT INTO access_logs VALUES (6, 1005, '2026-09-09 22:50', 'C');

-- ---------------------------------------------------------
-- alibis: each suspect's statement, whether it's been verified,
-- the fragment of the final message they're holding, and the
-- (possibly incorrect!) position of that fragment in the message
-- ---------------------------------------------------------
CREATE TABLE alibis (
    alibi_id      INTEGER PRIMARY KEY,
    suspect_id    INTEGER,
    statement     VARCHAR(200),
    verified      INTEGER DEFAULT 0,   -- 0 = not yet verified, 1 = verified true
    sequence      INTEGER,             -- position of fragment in final message
    clue_fragment VARCHAR(20)
);

INSERT INTO alibis VALUES (1, 1001, 'I was reviewing pipeline logs at my desk from 10:00 to 10:30pm.', 0, 1, 'SERVER');
INSERT INTO alibis VALUES (2, 1002, 'I was patching the backup server in the server room from 10:45 to 10:55pm.', 0, 3, 'CLOSET');
INSERT INTO alibis VALUES (3, 1003, 'I was finishing a report at Terminal A around 11:05pm.', 0, 4, 'MIDNIGHT');
INSERT INTO alibis VALUES (4, 1004, 'I was not in the building. I do not work there anymore.', 0, 5, 'NEVER');
INSERT INTO alibis VALUES (5, 1005, 'I was compiling a dataset at Terminal C from 11:40pm to midnight.', 0, 2, 'B');
