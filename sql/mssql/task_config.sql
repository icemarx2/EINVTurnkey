-- DROP TABLE task_config;

CREATE TABLE task_config
(
    category_type character varying(5) NOT NULL,
    process_type character varying(10) NOT NULL,
    task character varying(15) NOT NULL,
    src_path character varying(200),
    target_path character varying(200),
    file_format character varying(20),
    version character varying(5),
    encoding character varying(15),
    trans_chinese_date character varying(1),
    CONSTRAINT task_config_pk1 PRIMARY KEY (category_type, process_type, task)
);
