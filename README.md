# Oylut Clipping

Plataforma de monitoramento de mídia voltada para assessorias de comunicação.

O sistema pesquisa termos e suas variações em notícias, redes sociais e vídeos, preservando cada publicação encontrada como uma menção individual.

## Regra central

O Oylut Clipping **não remove duplicidades editoriais**. Publicações diferentes sobre o mesmo fato permanecem no resultado, pois cada veículo, perfil, vídeo ou postagem representa uma exposição própria.

## Escopo inicial

- cadastro de termo principal e variações;
- pesquisa nas últimas 24 horas;
- coleta futura em notícias, YouTube e fontes públicas de redes sociais;
- organização por tipo de mídia, fonte e horário;
- preservação integral das menções;
- seleção posterior para geração de clipping.

## Tecnologias

- Python 3.12+
- FastAPI
- Jinja2
- HTML, CSS e JavaScript

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows:

```bash
.venv\Scripts\activate
```

Acesse `http://127.0.0.1:8000`.

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores quando necessário.

## Estado

Sprint 1 — Fundação do produto.
