-- Table: markers

-- DROP TABLE clips;

CREATE TABLE
IF NOT EXISTS clips
(
    clip_id SERIAL,
    marker_id bigint NOT NULL,
    stream_id bigint NOT NULL,
    clip_url character varying
(400) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT clips_pkey PRIMARY KEY
(clip_id),
    CONSTRAINT "clip-conflict" UNIQUE
(marker_id),
    CONSTRAINT clips_marker_id_7c8f2e48_fk_markers_marker_id FOREIGN KEY
(marker_id)
        REFERENCES public.markers
(marker_id) MATCH SIMPLE
        ON
UPDATE NO ACTION
        ON
DELETE NO ACTION
        DEFERRABLE INITIALLY
DEFERRED,
    CONSTRAINT clips_stream_id_438e8d8d_fk_streams_stream_id FOREIGN KEY
(stream_id)
        REFERENCES public.streams
(stream_id) MATCH SIMPLE
        ON
UPDATE NO ACTION
        ON
DELETE NO ACTION
        DEFERRABLE INITIALLY
DEFERRED
)
WITH
(
    OIDS = FALSE
)
TABLESPACE pg_default;