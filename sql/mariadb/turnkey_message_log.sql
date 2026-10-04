-- DROP TABLE public.turnkey_message_log;

CREATE TABLE turnkey_message_log
(
    seqno character varying(8) NOT NULL,
    subseqno character varying(5) NOT NULL,
    uuid character varying(40) DEFAULT NULL,
    message_type character varying(10) DEFAULT NULL,
    category_type character varying(5) DEFAULT NULL,
    process_type character varying(10) DEFAULT NULL,
    from_party_id character varying(10) DEFAULT NULL,
    to_party_id character varying(10) DEFAULT NULL,
    message_dts character varying(17) DEFAULT NULL,
    character_count character varying(10) DEFAULT NULL,
    status character varying(5) DEFAULT NULL,
    in_out_bound character varying(1) DEFAULT NULL,
    from_routing_id character varying(39) DEFAULT NULL,
    to_routing_id character varying(39) DEFAULT NULL,
    invoice_identifier character varying(30) DEFAULT NULL,
    CONSTRAINT turnkey_message_log_pk1 PRIMARY KEY (seqno, subseqno)
);

-- DROP INDEX turnkey_message_log_index1;

CREATE INDEX turnkey_message_log_index1 ON turnkey_message_log(message_dts);

-- DROP INDEX turnkey_message_log_index2;

CREATE INDEX turnkey_message_log_index2 ON turnkey_message_log(uuid);