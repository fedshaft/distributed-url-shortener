CREATE TABLE if NOT EXISTS public.urls (
    id SERIAL PRIMARY KEY,
    long_url TEXT UNIQUE NOT NULL,
    short_code VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE if NOT EXISTS public.analytics (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(50) NOT NULL,
    stream_id TEXT NOT NULL,
    clicked_at DOUBLE PRECISION NOT NULL
);

CREATE TABLE if NOT EXISTS public.consumer_offsets (
    stream_name TEXT PRIMARY KEY NOT NULL,
    last_id TEXT NOT NULL
);