-- Table: public.jobs

-- DROP TABLE public.jobs;

CREATE TABLE
IF NOT EXISTS streams
(
    stream_id bigint NOT NULL,
    video_id bigint NOT NULL,
    user_id bigint NOT NULL,
    game_id bigint NOT NULL,
    game_name character varying
(100) COLLATE pg_catalog."default",
    title character varying
(400) COLLATE pg_catalog."default",
    thumbnail_url character varying
(400) COLLATE pg_catalog."default",
    video_description text COLLATE pg_catalog."default",
    view_count integer DEFAULT 0,
    created_at date DEFAULT now
(),
    published_at date,
    video_url character varying
(400) COLLATE pg_catalog."default",
    status character varying
(10) COLLATE pg_catalog."default" NOT NULL,
    failure_count integer NOT NULL DEFAULT 0,
    failure_reason text COLLATE pg_catalog."default",
    CONSTRAINT streams_pkey PRIMARY KEY
(stream_id)

)
WITH
(
    OIDS = FALSE
)
TABLESPACE pg_default;
