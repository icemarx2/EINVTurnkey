-- DROP TABLE turnkey_message_log_detail;

CREATE TABLE turnkey_message_log_detail
(
    seqno character varying(8) NOT NULL,
    subseqno character varying(5) NOT NULL,
    process_dts character varying(17),
    task character varying(30) NOT NULL,
    status character varying(5),
    filename character varying(300),
    uuid character varying(40),
    CONSTRAINT turnkey_message_log_detail_pk1 PRIMARY KEY (seqno, subseqno, task)
);

-- DROP INDEX turnkey_message_log_detail_index1;

CREATE INDEX turnkey_message_log_detail_index1 ON turnkey_message_log_detail(filename ASC NULLS LAST);