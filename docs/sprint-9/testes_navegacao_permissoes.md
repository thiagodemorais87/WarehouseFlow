# Testes de navegação e permissões — Sprint 9

**Ambiente executado nesta correção:** TestClient/FastAPI com SQLite em memória, perfis `ADMIN`, `GESTOR` e `OPERADOR`.

## Regras implementadas confirmadas no código

- Perfis reais: `ADMIN`, `GESTOR` e `OPERADOR`.
- Páginas comuns são protegidas por cookie JWT; sem sessão, `/inicio` e as páginas HTML redirecionam para `/login`.
- `/usuarios` aceita diretamente somente `ADMIN`.
- `/relatorios/movimentacoes` aceita diretamente `ADMIN` e `GESTOR`.
- Links com `data-roles` são ocultados no menu pelo JavaScript; o backend permanece responsável pela autorização real.
- O logout remove o cookie `access_token` e redireciona para `/login`.
- JWT tem validade configurada de 8 horas.
- Todas as rotas privadas da API exigem token/cookie; perfis sem operação permitida recebem `403`.

## Casos executados

| ID | Perfil | Tela ou endpoint | Procedimento | Resultado esperado | Resultado obtido | Status | Evidência |
|---|---|---|---|---|---|---|---|
| NAV-S9-01 | Sem login | `/inicio` e páginas protegidas | Acessar diretamente `/inicio`, `/dashboard`, `/produtos`, `/estoque`, `/posicoes`, `/pedidos`, `/tarefas`, `/otimizacao`, `/relatorios/picking`, `/usuarios` e `/relatorios/movimentacoes` | Todas retornam redirect `303` para `/login` | Todas as páginas parametrizadas retornaram `303` com `Location: /login` | PASSOU | Teste `test_pagina_html_restrita_sem_login_redireciona`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-02 | ADMIN | `/usuarios` | Fazer login por formulário e acessar diretamente a URL | HTML `200` | `200` | PASSOU | Teste `test_acesso_direto_usuarios_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-03 | GESTOR | `/usuarios` | Fazer login por formulário e acessar diretamente a URL | `403` | `403` | PASSOU | Teste `test_acesso_direto_usuarios_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-04 | OPERADOR | `/usuarios` | Fazer login por formulário e acessar diretamente a URL | `403` | `403` | PASSOU | Teste `test_acesso_direto_usuarios_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-05 | ADMIN | `/relatorios/movimentacoes` | Fazer login e acessar diretamente a URL | HTML `200` | `200` | PASSOU | Teste `test_acesso_direto_movimentacoes_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-06 | GESTOR | `/relatorios/movimentacoes` | Fazer login e acessar diretamente a URL | HTML `200` | `200` | PASSOU | Teste `test_acesso_direto_movimentacoes_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-07 | OPERADOR | `/relatorios/movimentacoes` | Fazer login e acessar diretamente a URL | `403` | `403` | PASSOU | Teste `test_acesso_direto_movimentacoes_por_perfil`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-08 | ADMIN, GESTOR, OPERADOR | `/dashboard` e páginas comuns | Entrar pela tela de login e abrir diretamente cada página comum | Sessão válida permite acessar; não há bloqueio indevido pela tela | O TestClient confirmou as telas protegidas por sessão. S9-T12 registrou navegação no menu original | PASSOU para autenticação; cobertura visual por perfil pendente em navegador | [S9-T12](./evidencias/S9-T12-filtro-pedidos-expedicao.png), [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-09 | ADMIN | `/logout` | Fazer login; enviar `POST /logout`; tentar `/inicio` | Remove cookie e redireciona para `/login`; acesso protegido volta ao login | `303` em logout e `/inicio` após logout | PASSOU | Teste `test_logout_apaga_o_cookie`, [S9-T17](./evidencias/S9-T17-logout-e-redirecionamento.png) |
| NAV-S9-10 | OPERADOR | Menu lateral `/usuarios` | Entrar pelo formulário e abrir `/produtos` | Opção deve ficar com `hidden` e `data-roles=ADMIN` no HTML | Link permaneceu no HTML com `hidden` e `data-roles="ADMIN"`; a UI aplica a regra por JavaScript | PASSOU | Teste corrigido `test_menu_lateral_esconde_usuarios_do_operador`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-11 | ADMIN | Menu lateral `/usuarios` | Entrar pelo formulário e abrir `/produtos` | Opção deve ser exibida após verificação do perfil no frontend | HTML contém o link `href="/usuarios"` e `data-roles="ADMIN"` | PASSOU no DOM renderizado pelo servidor; execução visual dinâmica não capturada nesta correção | Teste `test_menu_lateral_mostra_usuarios_ao_admin`; [pytest](./evidencias/navegacao-permissoes-pytest.txt) |
| NAV-S9-12 | Sem token / token inválido | API privada | Chamar `/auth/me` e rotas privadas sem token e com token falso | Sem token/expirado inválido: `401`; perfil sem permissão: `403` | A matriz existente confirmou `401` sem token e token inválido; `403` nos endpoints restritos | PASSOU | [matriz-permissoes.md](../matriz-permissoes.md), [pytest](./evidencias/navegacao-permissoes-pytest.txt) |

## Restrições por operação verificadas pela matriz automatizada

- Usuários: consulta disponível a perfis autenticados; criação, alteração e exclusão somente `ADMIN`.
- Produtos: criação/alteração/exclusão por `ADMIN` e `GESTOR`; operador bloqueado.
- Pedidos: leitura para todos; criação/alteração permite todos; exclusão somente `ADMIN`/`GESTOR`.
- Tarefas: leitura para todos; escrita para todos; exclusão somente `ADMIN`/`GESTOR`; operador limitado às tarefas atribuídas.
- Estoque: operações permitidas conforme política; exclusão somente `ADMIN`/`GESTOR`.
- Relatórios: dashboard para autenticados; relatórios gerenciais somente `ADMIN`/`GESTOR`.
- Posições: somente `ADMIN`/`GESTOR` alteram.

## Navegação principal já existente

O menu lateral contém Dashboard, Produtos, Estoque, Posições, Pedidos, Tarefas, Otimização, Relatório de Picking e opções condicionais de Movimentações e Usuários. Os links de perfil são complementados por bloqueios no backend.

## Limitações desta execução

- Não foi feita captura visual dinâmica dos três perfis nesta correção.
- Docker/PostgreSQL/Nginx não estavam disponíveis na execução original.
- Persistência ou expiração da sessão foi coberta pelo teste de token expirado; expiração real após 8 horas não foi aguardada.
- A sessão usa cookie HttpOnly e JWT com validade configurada em 480 minutos.
