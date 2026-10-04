-- DROP TABLE schedule_config;

CREATE TABLE schedule_config
(
    task character varying(30) NOT NULL,
    enable character varying(1),
    schedule_type character varying(10),
    schedule_week character varying(15),
    schedule_time character varying(50),
    schedule_period character varying(10),
    schedule_range character varying(15),
    CONSTRAINT schedule_config_pk1 PRIMARY KEY (task)
);
