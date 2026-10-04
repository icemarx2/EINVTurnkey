-- DROP TABLE turnkey_sysevent_log;

CREATE TABLE turnkey_sysevent_log
(
    eventdts character varying(17) NOT NULL,
    party_id character varying(10),
    seqno character varying(8),
    subseqno character varying(5),
    errorcode character varying(4),
    uuid character varying(40),
    information1 character varying(100),
    information2 character varying(100),
    information3 character varying(100),
    message1 character varying(100),
    message2 character varying(100),
    message3 character varying(100),
    message4 character varying(100),
    message5 character varying(100),
    message6 character varying(100),
    CONSTRAINT turnkey_sysevent_log_pk1 PRIMARY KEY (eventdts)
);

-- DROP INDEX turnkey_sysevent_log_index1;

CREATE INDEX turnkey_sysevent_log_index1 ON turnkey_sysevent_log(seqno, subseqno);

-- DROP INDEX urnkey_sysevent_log_index2;

CREATE INDEX turnkey_sysevent_log_index2 ON turnkey_sysevent_log(uuid);