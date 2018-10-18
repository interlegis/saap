--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: saap
--

DELETE FROM public.django_content_type;

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	easy_thumbnails	source
7	easy_thumbnails	thumbnail
8	easy_thumbnails	thumbnaildimensions
9	taggit	tag
10	taggit	taggeditem
11	core	user
12	core	municipio
13	core	nivelinstrucao
14	core	situacaomilitar
15	core	parlamentar
16	core	partido
17	core	areatrabalho
18	core	operadorareatrabalho
19	core	cep
20	core	regiaomunicipal
21	core	distrito
22	core	bairro
23	core	tipologradouro
24	core	logradouro
25	core	trecho
26	core	impressoenderecamento
27	core	filiacao
28	cerimonial	tipotelefone
29	cerimonial	tipoendereco
30	cerimonial	tipoemail
31	cerimonial	parentesco
32	cerimonial	estadocivil
33	cerimonial	pronometratamento
34	cerimonial	tipoautoridade
35	cerimonial	tipolocaltrabalho
36	cerimonial	nivelinstrucao
37	cerimonial	operadoratelefonia
38	cerimonial	contato
39	cerimonial	perfil
40	cerimonial	telefone
41	cerimonial	telefoneperfil
42	cerimonial	email
43	cerimonial	emailperfil
44	cerimonial	dependente
45	cerimonial	dependenteperfil
46	cerimonial	localtrabalho
47	cerimonial	localtrabalhoperfil
48	cerimonial	endereco
49	cerimonial	enderecoperfil
50	cerimonial	filiacaopartidaria
51	cerimonial	statusprocesso
52	cerimonial	classificacaoprocesso
53	cerimonial	topicoprocesso
54	cerimonial	assuntoprocesso
55	cerimonial	processo
56	cerimonial	processocontato
57	cerimonial	grupodecontatos
58	social_auth	usersocialauth
59	social_auth	nonce
60	social_auth	association
61	social_auth	code
62	social_django	usersocialauth
63	social_django	nonce
64	social_django	association
65	social_django	code
66	social_django	partial
67	core	estado
68	cities_light	country
69	cities_light	region
70	cities_light	city
\.


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: saap
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 70, true);


--
-- PostgreSQL database dump complete
--

