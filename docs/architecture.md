# Arquitetura do núcleo — Sprint 2.0

O Oylut Clipping adota o **Modelo A**: toda pesquisa acontece dentro de um cliente.

## Relações principais

```text
Cliente
  └── Monitoramentos
        └── Termos
              └── Pesquisas
                    └── Resultados
```

## Cliente

Representa a instituição, empresa, marca, pessoa ou projeto acompanhado por uma assessoria.

Campos principais:

- `id`
- `name`
- `slug`
- `logo_url`
- `is_active`
- `created_at`
- `updated_at`

## Monitoramento

Representa um assunto monitorado dentro de um cliente.

Exemplo: cliente `TCE-PB`; monitoramento `Menções institucionais`.

Campos principais:

- `id`
- `client_id`
- `name`
- `is_active`
- `created_at`
- `updated_at`

## Termo

Representa uma forma textual usada na busca.

Exemplos:

- `TCE-PB`
- `Tribunal de Contas da Paraíba`
- `Tribunal de Contas do Estado da Paraíba`

Campos principais:

- `id`
- `monitoring_id`
- `text`
- `is_primary`
- `is_active`
- `created_at`

## Pesquisa

Cada execução manual ou automática gera uma pesquisa.

Campos principais:

- `id`
- `monitoring_id`
- `period_hours`
- `status`
- `started_at`
- `finished_at`
- `result_count`
- `error_message`

## Resultado

Cada publicação encontrada é preservada individualmente.

Campos principais:

- `id`
- `search_id`
- `media_type`
- `source`
- `title`
- `url`
- `published_at`
- `excerpt`
- `searched_term`
- `matched_term`
- `created_at`

## Regra de duplicidade

O sistema **não remove publicações repetidas ou semelhantes**. Cada resultado corresponde a uma exposição individual em uma fonte, perfil, canal ou URL.

Apenas termos exatamente iguais dentro do mesmo monitoramento são impedidos no banco, para evitar executar a mesma consulta duas vezes.

## Estados de pesquisa

- `pending`
- `running`
- `completed`
- `partial`
- `failed`

`partial` significa que uma ou mais fontes falharam, mas outras retornaram resultados.

## Padrão dos coletores

Todo coletor deverá receber termos e período e devolver uma lista no formato comum de menção. O histórico, a interface e a geração de clipping não devem depender da fonte específica.
