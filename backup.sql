--
-- PostgreSQL database dump
--

-- Dumped from database version 13.18 (Debian 13.18-1.pgdg120+1)
-- Dumped by pg_dump version 13.18 (Debian 13.18-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: attendance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attendance (
    id integer NOT NULL,
    date text NOT NULL,
    instructor text NOT NULL,
    training_course text NOT NULL,
    check_in text NOT NULL,
    check_out text NOT NULL,
    daily_log boolean DEFAULT false
);


ALTER TABLE public.attendance OWNER TO postgres;

--
-- Name: attendance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attendance_id_seq OWNER TO postgres;

--
-- Name: attendance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attendance_id_seq OWNED BY public.attendance.id;


--
-- Name: calendar; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.calendar (
    id integer NOT NULL,
    date text NOT NULL,
    event text NOT NULL
);


ALTER TABLE public.calendar OWNER TO postgres;

--
-- Name: calendar_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.calendar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.calendar_id_seq OWNER TO postgres;

--
-- Name: calendar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.calendar_id_seq OWNED BY public.calendar.id;


--
-- Name: issue_comments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issue_comments (
    id integer NOT NULL,
    issue_id integer NOT NULL,
    comment text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.issue_comments OWNER TO postgres;

--
-- Name: issue_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issue_comments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.issue_comments_id_seq OWNER TO postgres;

--
-- Name: issue_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issue_comments_id_seq OWNED BY public.issue_comments.id;


--
-- Name: issues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issues (
    id integer NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    resolved boolean DEFAULT false
);


ALTER TABLE public.issues OWNER TO postgres;

--
-- Name: issues_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issues_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.issues_id_seq OWNER TO postgres;

--
-- Name: issues_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issues_id_seq OWNED BY public.issues.id;


--
-- Name: notices; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notices (
    id integer NOT NULL,
    type text NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    date timestamp without time zone NOT NULL
);


ALTER TABLE public.notices OWNER TO postgres;

--
-- Name: notices_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notices_id_seq OWNER TO postgres;

--
-- Name: notices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notices_id_seq OWNED BY public.notices.id;


--
-- Name: task_checklist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_checklist (
    id integer NOT NULL,
    task_name text NOT NULL,
    is_checked boolean DEFAULT false,
    checked_date text
);


ALTER TABLE public.task_checklist OWNER TO postgres;

--
-- Name: task_checklist_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_checklist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_checklist_id_seq OWNER TO postgres;

--
-- Name: task_checklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.task_checklist_id_seq OWNED BY public.task_checklist.id;


--
-- Name: unchecked_descriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.unchecked_descriptions (
    id integer NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.unchecked_descriptions OWNER TO postgres;

--
-- Name: unchecked_descriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.unchecked_descriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.unchecked_descriptions_id_seq OWNER TO postgres;

--
-- Name: unchecked_descriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.unchecked_descriptions_id_seq OWNED BY public.unchecked_descriptions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    password text NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attendance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance ALTER COLUMN id SET DEFAULT nextval('public.attendance_id_seq'::regclass);


--
-- Name: calendar id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendar ALTER COLUMN id SET DEFAULT nextval('public.calendar_id_seq'::regclass);


--
-- Name: issue_comments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue_comments ALTER COLUMN id SET DEFAULT nextval('public.issue_comments_id_seq'::regclass);


--
-- Name: issues id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues ALTER COLUMN id SET DEFAULT nextval('public.issues_id_seq'::regclass);


--
-- Name: notices id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notices ALTER COLUMN id SET DEFAULT nextval('public.notices_id_seq'::regclass);


--
-- Name: task_checklist id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_checklist ALTER COLUMN id SET DEFAULT nextval('public.task_checklist_id_seq'::regclass);


--
-- Name: unchecked_descriptions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unchecked_descriptions ALTER COLUMN id SET DEFAULT nextval('public.unchecked_descriptions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attendance (id, date, instructor, training_course, check_in, check_out, daily_log) FROM stdin;
1	2025-02-05	1	데이터 분석 스쿨	15:55	15:57	f
3	2025-02-05	1	데이터 분석 스쿨	09:00	18:00	f
4	2025-02-05	2	클라우드 스쿨	09:30	18:30	f
5	2025-02-05	1	데이터 분석 스쿨	16:09	16:12	f
6	2025-02-05	2	데이터 분석 스쿨	16:08	16:10	f
7	2025-02-05	1	데이터 분석 스쿨	16:09	16:12	f
8	2025-02-05	2	데이터 분석 스쿨	16:08	16:10	f
9	2025-02-03	1	데이터 분석 스쿨	09:00	18:00	f
10	2025-02-05	1	과정 선택	09:00	18:00	f
11	2025-02-05	1	과정 선택	09:00	18:00	f
12	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
13	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
14	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
15	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
16	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
17	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
18	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
19	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
20	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
21	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
22	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
23	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
24	2025-02-05	2	클라우드 엔지니어링 1기	09:00	18:00	f
25	2025-02-05	1	과정 선택	09:00	18:00	f
26	2025-02-05	1	게임 스쿨	19:07	19:58	f
27	2025-02-05	2	게임 스쿨	19:00	19:59	f
28	2025-02-05	1	클라우드 엔지니어링 1기	09:00	18:00	f
29	2025-02-06	1	과정 선택	09:00	18:00	f
30	2025-02-06	2	클라우드 엔지니어링 1기	09:00	18:00	f
31	2025-02-06	1	클라우드 엔지니어링 1기	09:00	18:00	f
32	2025-02-06	2	클라우드 엔지니어링 1기	09:00	18:00	f
33	2025-02-06	1	클라우드 엔지니어링 1기	09:00	18:00	f
34	2025-02-06	1	클라우드 엔지니어링 1기	09:00	18:00	f
35	2025-02-06	2	클라우드 엔지니어링 1기	09:00	18:00	f
2	2025-02-05	2	데이터 분석 아님	15:56	15:58	f
\.


--
-- Data for Name: calendar; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.calendar (id, date, event) FROM stdin;
1	2025-02-10	워크샵
2	2025-02-15	프로젝트 발표
\.


--
-- Data for Name: issue_comments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issue_comments (id, issue_id, comment, created_at) FROM stdin;
1	8	댓글 테스트 입니다.	2025-02-05 11:56:39.76779
2	7	댓글 테스트 입니다.	2025-02-05 12:42:10.841042
3	13	ㅠㅗㅕㅝ	2025-02-06 04:29:09.370824
\.


--
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issues (id, content, created_at, resolved) FROM stdin;
2	test2	2025-02-05 07:32:36.901212	f
3	ㅁㄴㅇㄹ	2025-02-05 09:12:18.004069	f
4	강의 자료 오류 발생	2025-02-05 10:46:00.387509	f
8	asdfasdf	2025-02-05 11:06:27.483087	t
6	ㄴㅇㄹㅎㄴㅇㄹㅎ	2025-02-05 10:52:15.455122	t
5	ㄴㅇㄹㅎㄴㅇㄹㅎ	2025-02-05 10:50:55.762451	t
7	asdfasdf	2025-02-05 11:05:24.489301	t
1	test	2025-02-05 07:31:16.867527	f
9	이슈사항 테스트 1	2025-02-05 12:45:20.139818	f
10	이슈 사항 테스트 2	2025-02-05 12:45:29.89646	f
11	이슈 사항 테스트 3	2025-02-05 12:45:34.015314	f
12	미나어로마ㅓㄴ올	2025-02-06 00:52:45.258568	t
13	ㅁ널외ㅏ너ㅗㅇ리	2025-02-06 04:15:11.59024	f
14	- 클라우드 이슈사항 작성 테스트입니다.	2025-02-06 04:19:06.921841	t
15	- 이슈 작성 테스트입니다.	2025-02-06 04:37:23.409406	f
\.


--
-- Data for Name: notices; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notices (id, type, title, content, date) FROM stdin;
3	공지사항	시스템 점검 안내	시스템 점검이 예정되어 있습니다.	2025-02-05 16:05:50.970414
\.


--
-- Data for Name: task_checklist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task_checklist (id, task_name, is_checked, checked_date) FROM stdin;
1	강사 근태 관련 daily 확인	f	2025-02-05
2	보조강사 RnR 지정 및 실행 여부 확인	f	2025-02-05
3	운영 계획서와 실제 운영의 일치 여부	f	2025-02-05
4	커리큘럼 변경 시 사전 공유 진행 여부 (PA팀 / 고용센터)	f	2025-02-05
5	프로젝트 시수의 프로젝트 강사 참여 수준 및 근태 확인	f	2025-02-05
6	디스코드 상 상담 및 운영 내역의 아카이브 진행 여부	f	2025-02-05
7	DM으로 진행된 내용에 대한 팀 내 공유 여부	f	2025-02-05
8	강사 근태 관련 daily 확인	t	2025-02-05
9	보조강사 RnR 지정 및 실행 여부 확인	t	2025-02-05
10	운영 계획서와 실제 운영의 일치 여부	f	2025-02-05
11	커리큘럼 변경 시 사전 공유 진행 여부 (PA팀 / 고용센터)	f	2025-02-05
12	프로젝트 시수의 프로젝트 강사 참여 수준 및 근태 확인	t	2025-02-05
13	디스코드 상 상담 및 운영 내역의 아카이브 진행 여부	f	2025-02-05
14	DM으로 진행된 내용에 대한 팀 내 공유 여부	f	2025-02-05
15	강사 근태 관련 daily 확인	f	2025-02-05
16	보조강사 RnR 지정 및 실행 여부 확인	f	2025-02-05
17	운영 계획서와 실제 운영의 일치 여부	t	2025-02-05
18	커리큘럼 변경 시 사전 공유 진행 여부 (PA팀 / 고용센터)	f	2025-02-05
19	프로젝트 시수의 프로젝트 강사 참여 수준 및 근태 확인	t	2025-02-05
20	디스코드 상 상담 및 운영 내역의 아카이브 진행 여부	t	2025-02-05
21	DM으로 진행된 내용에 대한 팀 내 공유 여부	f	2025-02-05
22	강사 근태 관련 daily 확인	f	2025-02-05
23	보조강사 RnR 지정 및 실행 여부 확인	f	2025-02-05
24	운영 계획서와 실제 운영의 일치 여부	t	2025-02-05
25	커리큘럼 변경 시 사전 공유 진행 여부 (PA팀 / 고용센터)	f	2025-02-05
26	프로젝트 시수의 프로젝트 강사 참여 수준 및 근태 확인	t	2025-02-05
27	디스코드 상 상담 및 운영 내역의 아카이브 진행 여부	t	2025-02-05
28	DM으로 진행된 내용에 대한 팀 내 공유 여부	f	2025-02-05
\.


--
-- Data for Name: unchecked_descriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.unchecked_descriptions (id, content, created_at) FROM stdin;
1	test 중	2025-02-05 09:12:00.579018
5	미체크된 항목입니다.	2025-02-06 04:26:47.423226
6	미체크된 항목입니다.	2025-02-06 04:26:48.706754
7	미체크된 항목입니다.	2025-02-06 04:26:48.83079
8	미체크된 항목입니다.	2025-02-06 04:26:49.006662
9	미체크된 항목입니다.	2025-02-06 04:27:12.173062
10	- 미체크 항목에 대한 작성	2025-02-06 04:36:32.61607
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password) FROM stdin;
1234	1234	0000
\.


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendance_id_seq', 35, true);


--
-- Name: calendar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.calendar_id_seq', 2, true);


--
-- Name: issue_comments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issue_comments_id_seq', 3, true);


--
-- Name: issues_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issues_id_seq', 15, true);


--
-- Name: notices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notices_id_seq', 9, true);


--
-- Name: task_checklist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.task_checklist_id_seq', 28, true);


--
-- Name: unchecked_descriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.unchecked_descriptions_id_seq', 10, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: attendance attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (id);


--
-- Name: calendar calendar_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendar
    ADD CONSTRAINT calendar_pkey PRIMARY KEY (id);


--
-- Name: issue_comments issue_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue_comments
    ADD CONSTRAINT issue_comments_pkey PRIMARY KEY (id);


--
-- Name: issues issues_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issues
    ADD CONSTRAINT issues_pkey PRIMARY KEY (id);


--
-- Name: notices notices_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notices
    ADD CONSTRAINT notices_pkey PRIMARY KEY (id);


--
-- Name: task_checklist task_checklist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_checklist
    ADD CONSTRAINT task_checklist_pkey PRIMARY KEY (id);


--
-- Name: unchecked_descriptions unchecked_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.unchecked_descriptions
    ADD CONSTRAINT unchecked_descriptions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: issue_comments issue_comments_issue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue_comments
    ADD CONSTRAINT issue_comments_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES public.issues(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

