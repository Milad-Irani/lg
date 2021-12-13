-- Table: pointers

-- DROP TABLE pointers;

CREATE TABLE
IF NOT EXISTS pointers
(
    pointer_id SERIAL,
	job_id bigint NOT NULL,
	user_id bigint NOT NULL,
	video_id bigint NOT NULL,
    position_seconds integer NOT NULL,
    votes_count integer NOT NULL,
    created_at date DEFAULT now
(),
    CONSTRAINT pointers_pkey PRIMARY KEY
(pointer_id),
    CONSTRAINT pointers_job_id_8981c587_fk_streams_job_id FOREIGN KEY
(job_id)
        REFERENCES public.streams
(job_id) MATCH SIMPLE
        ON
UPDATE NO ACTION
        ON
DELETE NO ACTION
        DEFERRABLE INITIALLY
DEFERRED,
    CONSTRAINT pointers_position_seconds_check CHECK
(position_seconds >= 0),
    CONSTRAINT pointers_votes_count_check CHECK
(votes_count >= 0)
)
WITH
(
    OIDS = FALSE
)
TABLESPACE pg_default;