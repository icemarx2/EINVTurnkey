-- DROP TABLE from_config;

CREATE TABLE from_config
(
    transport_id character varying(10),
    transport_password character varying(45),
    party_id character varying(10) NOT NULL,
    party_description character varying(200),
    routing_id character varying(39),
    routing_description character varying(200),
    sign_id character varying(4),
    substitute_party_id character varying(10),
    CONSTRAINT from_config_pk1 PRIMARY KEY (party_id)
);

CREATE INDEX from_config_index1 ON from_config(substitute_party_id);