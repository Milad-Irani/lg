-- Table: users

-- DROP TABLE public.users;

CREATE TABLE
IF NOT EXISTS users
(
    id bigint NOT NULL PRIMARY KEY,
    login VARCHAR
(50) COLLATE pg_catalog."default" NOT NULL,
    display_name VARCHAR
(50) COLLATE pg_catalog."default" NOT NULL,
	profile_image_url VARCHAR
(256) COLLATE pg_catalog."default" NOT NULL,
	access_token VARCHAR
(256) COLLATE pg_catalog."default" NOT NULL,
	refresh_token VARCHAR
(256) COLLATE pg_catalog."default" NOT NULL
)
WITH
(
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE users
    OWNER to postgres;