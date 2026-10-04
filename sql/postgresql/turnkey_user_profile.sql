-- DROP TABLE turnkey_user_profile;

CREATE TABLE turnkey_user_profile
(
    user_id character varying(10) NOT NULL,
    user_password character varying(100) NOT NULL,
    user_role character varying(2) ,
    CONSTRAINT turnkey_user_profile_pk1 PRIMARY KEY (user_id)
);