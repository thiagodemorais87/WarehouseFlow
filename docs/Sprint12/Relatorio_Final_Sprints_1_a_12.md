# WarehouseFlow - Relatório Final Consolidado das Sprints 1 a 12

## Capa

**Grupo 26 - Turma 8MB**
**Ciência da Computação**
**UNINASSAU - Centro Universitário Maurício de Nassau - Campus Graças**
**Professor: David Wilber Silva Daltro**
**Ano: 2026**

## Equipe

Gabriel George de Araújo Figueiredo — 01605236  
Guilherme Branco Ferrario — 01596391  
João Pedro Silva de Araujo — 01606470  
Sérgio José de Araújo Júnior — 01590694  
Thiago de Morais Gonçalves — 01609695

## Projeto

WarehouseFlow é um sistema acadêmico de gerenciamento de armazém com CRUD de operações, autenticação/RBAC, relatórios e motor de otimização de rotas NN + 2-opt.

## Objetivo

Organizar produtos, estoque, posições, pedidos, tarefas e usuários, reduzindo deslocamentos desnecessários em operações de picking.

## Tecnologias

- Python/FastAPI/Pydantic/SQLAlchemy
- PostgreSQL
- HTML/CSS/JavaScript/Jinja2
- Pytest
- Docker/Docker Compose/Nginx
- Git/GitHub

## Arquitetura

Frontend Jinja/JavaScript → API FastAPI → serviços e provedores SQLAlchemy → PostgreSQL; motor de otimização separado em `backend/optimization`.

## Banco de dados

O projeto fornece `schema.sql`, `seed.sql`, migrations e SQL dedicado ao histórico do motor. O seed demonstra roles, usuários, armazém, posições, produtos, estoque, pedidos, itens, tarefas e execuções de otimização.

## Módulos registrados no código

Autenticação, usuários, produtos, estoque, posições, pedidos, tarefas, relatórios, dashboard e otimização.

## Histórico das Sprints

Os documentos anteriores das Sprints 1 a 11 estão em [`docs/`](../). O índice oficial consolidado é [`indice_documentacao_sprints.md`](../indice_documentacao_sprints.md). Os PDFs acumulados existentes foram encontrados em `docs/`, `docs/entrega-final/` e `docs/sprint-10/`.

Não há atribuição nominal formal de todas as atividades individuais nas fontes antigas. O README também registra essa ausência profissionalmente.

### Sprint 12

Foi realizada a validação final, restauração de um arquivo truncado, correção de consistência do seed e do Compose, execução da suíte e consolidação documental.

## Funcionalidades entregues

CRUD e regras descritas no README e nos módulos da API; JWT/RBAC; dashboard; relatórios CSV; motor NN + 2-opt; persistência de execuções.

## Testes e resultados reais

- Estado inicial: 14 erros de coleta por sintaxe truncada.
- Após restauração: primeira execução finalizou com 236 passed, 66 skipped e 2 falhas de consistência.
- Após correções finais: 239 passed, 66 skipped, 1 warning.
- Smoke do motor: distância 38 → 11; redução 27; percentual 71.05263157894737%.
- Docker Compose real iniciado; PostgreSQL healthy, API e frontend ativos.
- Fluxos principais exercitados sobre a API conectada ao banco Docker; registros temporários de CRUD removidos.
- Ciclo de vida de usuário ADMIN/OPERADOR e três exportações CSV validados na API Docker.
- Capturas reais do navegador incluídas nos anexos da Sprint 12.

## Bugs

Os bugs reais estão registrados em [`Registro_Bugs_Sprint12.md`](Registro_Bugs_Sprint12.md).

## Limitações justificadas

O banco Docker utiliza volume preexistente e não foi zerado. O cenário por pedido validado resultou em distância igual antes/depois; uma heurística não garante melhoria para toda entrada.

## Code Freeze e Release

Não foi declarado Code Freeze. Não houve push, tag final nem Release. A situação está registrada em [`Code_Freeze_Release.md`](Code_Freeze_Release.md).

## Evidências

- [`Checklist_Evidencias.md`](Checklist_Evidencias.md)
- [`evidencias/`](evidencias/)
- Evidências anteriores das Sprints 9, 10 e 11 permanecem nos respectivos diretórios.

## PDF acumulado

- [PDF exclusivo da Sprint 12](Grupo26_WarehouseFlow_Sprint12.pdf)
- [PDF consolidado das Sprints 1 a 12](Relatorio_Final_Sprints_1_a_12.pdf)
- [Cópia para entrega](../entrega-final/Grupo26_WarehouseFlow_Sprints_1_a_12.pdf)

## Vídeo

A gravação está pendente. O roteiro está em [`Roteiro_Video_Demonstracao.md`](Roteiro_Video_Demonstracao.md).

## Link oficial

https://github.com/thiagodemorais87/WarehouseFlow

## Conclusão

O motor, a API e a suíte apresentam uma linha de base funcional após a correção dos problemas encontrados. A entrega final ainda depende da validação Docker/PostgreSQL, do ensaio geral e da criação aprovada de tag/Release.

## Referências

- README do projeto
- Documentação técnica e do usuário
- Contrato da API
- Documentação do motor
- PDFs das Sprints anteriores
