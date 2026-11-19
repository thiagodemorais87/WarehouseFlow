# Dificuldades e próximos passos — Sprint 9

## Dificuldades encontradas

### Comprovadas

1. **Exclusão com dependências (`BUG-S9-01`)**
   - Problema: o `DELETE /products/{product_id}` retornava `500` ao encontrar referências em estoque/pedidos.
   - Impacto: erro interno e mensagem genérica na UI.
   - Diagnóstico: a API não verificava `stock` e `order_items` antes da exclusão.
   - Resolução: verificações antes do DELETE e resposta `409` com detalhe das dependências.
   - Evidência: `evidencias/S9-T18-*` e `bugs_sprint9.md`.

2. **Docker/PostgreSQL/Nginx indisponíveis**
   - Docker CLI estava instalado, mas o daemon Linux do Docker não estava disponível.
   - Não havia PostgreSQL local respondendo em `localhost:5433`.
   - Impacto: execução real via Compose não foi possível; os testes funcionais usaram SQLite descartável.

3. **Geração opt-in da matriz de permissões**
   - O teste `test_gerar_arquivo_da_matriz` só gera `docs/matriz-permissoes.md` com `GERAR_MATRIZ=1`.
   - O arquivo existente não foi sobrescrito na execução original para preservar documentação do repositório.

4. **Cobertura visual de navegação por perfil**
   - Os testes existentes cobriam RBAC da API e parte da interface.
   - O menu HTML contém opções com `hidden`/`data-roles`; uma asserção anterior verificava apenas texto no HTML e não a restrição real.
   - Resolução desta correção: teste corrigido para validar `hidden`/`data-roles`, além de testes diretos das URLs HTML.

5. **Ferramentas instaladas nesta correção**
   - O Python atual não tinha pytest instalado no início da correção.
   - Resolução: dependências de `requirements.txt` foram instaladas no ambiente local.

### A confirmar pela equipe

- Não foi encontrado registro formal de credenciais reais ou perfis adicionais além de `ADMIN`, `GESTOR` e `OPERADOR`.
- Não foi possível confirmar visualmente, nesta correção, a troca dinâmica dos links do menu em navegador real para os três perfis.
- Não foi possível confirmar a execução real com PostgreSQL/Compose nem o proxy em `8080`.
- Não há evidência registrada de espera até a expiração real da sessão de 8 horas.

## Próximos passos

### Pendências técnicas

- Executar `docker compose up --build` com Docker Desktop/daemon ativo.
- Validar PostgreSQL, migrações/seed e persistência em `localhost:5433`.
- Validar a interface pelo proxy em `localhost:8080`.
- Confirmar visualmente o menu por perfil em navegador real.
- Confirmar expiração real do cookie/JWT após os 480 minutos configurados.
- Investigar o aviso de depreciação do Starlette ao usar `httpx` no TestClient.

### Pendências de testes

- Capturar screenshots reais das URLs `/usuarios` e `/relatorios/movimentacoes` para cada perfil.
- Testar navegação entre todas as telas principais com cada perfil.
- Testar logout em navegador e confirmar remoção persistente da sessão.
- Reexecutar os 20 cenários em PostgreSQL, não apenas em SQLite.
- Executar novamente a regressão S9-T18 com dependências reais em banco PostgreSQL.
- Reexecutar a geração opt-in da matriz de permissões em momento controlado e revisar o diff gerado.

### Pendências de documentação

- Atualizar PDF acumulado da Sprint 09 após publicação da matriz corrigida.
- Manter a matriz de permissões sincronizada caso novas rotas ou perfis sejam adicionados.
- Registrar a versão/data da próxima execução com PostgreSQL.

### Melhorias futuras

- Centralizar regras de ocultação do menu e autorização em uma configuração única por perfil.
- Cobrir testes frontend com navegador automatizado (Playwright/Selenium).
- Adicionar evidências automáticas de status HTTP e redirecionamento para cada tela.
- Criar política formal de retenção/limpeza das evidências de testes.
