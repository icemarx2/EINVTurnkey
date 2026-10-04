-- DROP TABLE to_config;

CREATE TABLE to_config
(
    party_id character varying(10) NOT NULL,
    party_description character varying(200),
    routing_id character varying(39),
    routing_description character varying(200),
    from_party_id character varying(10) NOT NULL,
    CONSTRAINT to_config_pk1 PRIMARY KEY (from_party_id, party_id)
);