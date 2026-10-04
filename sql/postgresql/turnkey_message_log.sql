-- DROP TABLE public.turnkey_message_log;

CREATE TABLE turnkey_message_log
(
    seqno character varying(8) NOT NULL,
    subseqno character varying(5) NOT NULL,
    uuid character varying(40) DEFAULT NULL::character varying,
    message_type character varying(10) DEFAULT NULL::character varying,
    category_type character varying(5) DEFAULT NULL::character varying,
    process_type character varying(10) DEFAULT NULL::character varying,
    from_party_id character varying(10) DEFAULT NULL::character varying,
    to_party_id character varying(10) DEFAULT NULL::character varying,
    message_dts character varying(17) DEFAULT NULL::character varying,
    character_count character varying(10) DEFAULT NULL::character varying,
    status character varying(5) DEFAULT NULL::character varying,
    in_out_bound character varying(1) DEFAULT NULL::character varying,
    from_routing_id character varying(39) DEFAULT NULL::character varying,
    to_routing_id character varying(39) DEFAULT NULL::character varying,
    invoice_identifier character varying(30) DEFAULT NULL::character varying,
    CONSTRAINT turnkey_message_log_pk1 PRIMARY KEY (seqno, subseqno)
);

-- DROP INDEX turnkey_message_log_index1;

CREATE INDEX turnkey_message_log_index1 ON turnkey_message_log(message_dts ASC NULLS LAST);

-- DROP INDEX turnkey_message_log_index2;

CREATE INDEX turnkey_message_log_index2 ON turnkey_message_log(uuid ASC NULLS LAST);