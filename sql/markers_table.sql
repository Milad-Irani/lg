-- Table: markers

-- DROP TABLE markers;

CREATE TABLE
IF NOT EXISTS markers
(
    marker_id SERIAL,
	stream_id bigint NOT NULL,
	user_id bigint NOT NULL,
	video_id bigint NOT NULL,
    position_seconds integer NOT NULL,
    votes_count integer NOT NULL,
    created_at date DEFAULT now
(),
    CONSTRAINT markers_pkey PRIMARY KEY
(marker_id),
    CONSTRAINT markers_stream_id_8981c587_fk_streams_stream_id FOREIGN KEY
(stream_id)
        REFERENCES public.streams
(stream_id) MATCH SIMPLE
        ON
UPDATE NO ACTION
        ON
DELETE NO ACTION
        DEFERRABLE INITIALLY
DEFERRED,
    CONSTRAINT markers_position_seconds_check CHECK
(position_seconds >= 0),
    CONSTRAINT markers_votes_count_check CHECK
(votes_count >= 0)
)
WITH
(
    OIDS = FALSE
)
TABLESPACE pg_default;