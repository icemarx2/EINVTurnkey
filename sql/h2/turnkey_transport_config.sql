-- DROP TABLE turnkey_transport_config;

CREATE TABLE turnkey_transport_config
(
    transport_id character varying(10) NOT NULL,
    transport_password character varying(60) NOT NULL,
    CONSTRAINT turnkey_transport_config_pk1 PRIMARY KEY (transport_id)
);