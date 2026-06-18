--
-- PostgreSQL database dump
--

\restrict 4uNaZU2tOKdtHiK0lXVwwUhbudJTkN38IWmBHEezcSLkB46Wpvz62MLxegfGj21

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analytics; Type: TABLE; Schema: public; Owner: shortener
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    short_code character varying(50),
    clicked_at double precision
);


ALTER TABLE public.analytics OWNER TO shortener;

--
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: shortener
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analytics_id_seq OWNER TO shortener;

--
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shortener
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- Name: urls; Type: TABLE; Schema: public; Owner: shortener
--

CREATE TABLE public.urls (
    id integer NOT NULL,
    long_url text NOT NULL,
    short_code character varying(20) NOT NULL
);


ALTER TABLE public.urls OWNER TO shortener;

--
-- Name: urls_id_seq; Type: SEQUENCE; Schema: public; Owner: shortener
--

CREATE SEQUENCE public.urls_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urls_id_seq OWNER TO shortener;

--
-- Name: urls_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shortener
--

ALTER SEQUENCE public.urls_id_seq OWNED BY public.urls.id;


--
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: shortener
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- Name: urls id; Type: DEFAULT; Schema: public; Owner: shortener
--

ALTER TABLE ONLY public.urls ALTER COLUMN id SET DEFAULT nextval('public.urls_id_seq'::regclass);


--
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: shortener
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- Name: urls urls_pkey; Type: CONSTRAINT; Schema: public; Owner: shortener
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT urls_pkey PRIMARY KEY (id);


--
-- Name: urls urls_short_code_key; Type: CONSTRAINT; Schema: public; Owner: shortener
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT urls_short_code_key UNIQUE (short_code);


--
-- PostgreSQL database dump complete
--

\unrestrict 4uNaZU2tOKdtHiK0lXVwwUhbudJTkN38IWmBHEezcSLkB46Wpvz62MLxegfGj21

