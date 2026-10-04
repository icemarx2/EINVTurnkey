-- DROP TABLE sign_config;

CREATE TABLE sign_config 
(
    sign_id character varying(4) NOT NULL,
    sign_type character varying(10) DEFAULT NULL,
    pfx_path character varying(100) DEFAULT NULL,
    sign_password character varying(60) NOT NULL,
    CONSTRAINT sign_config_pk1 PRIMARY KEY (sign_id)
);