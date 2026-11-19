# Relatório de correção da avaliação — Sprint 9

## Correções realizadas

| Apontamento do professor | Correção realizada | Arquivo/evidência |
|---|---|---|
| Falta de registro formal dos 20 cenários | Mantidos exatamente S9-T01 a S9-T20; cada cenário agora possui nome, funcionalidade, objetivo, pré-condições, procedimento, resultado esperado, resultado obtido, status, evidência e observações | [matriz_testes_sprint9.md](./matriz_testes_sprint9.md) |
| Navegação insuficiente | Criados cenários formais para login/logout, páginas comuns, URLs diretas e navegação principal | [testes_navegacao_permissoes.md](./testes_navegacao_permissoes.md) |
| Falta de testes relacionados às permissões | Testes diretos para ADMIN, GESTOR e OPERADOR, incluindo `/usuarios` e `/relatorios/movimentacoes`, além da matriz existente da API | [testes_navegacao_permissoes.md](./testes_navegacao_permissoes.md), [matriz-permissoes.md](../matriz-permissoes.md), [navegacao-permissoes-pytest.txt](./evidencias/navegacao-permissoes-pytest.txt) |
| Atualização técnica ausente | README e referência da API foram atualizados; banco recebeu regra de exclusão segura; links da Sprint 9 foram publicados | [README.md](../../README.md), [Api-doc.md](../Api-doc.md), [backend/database/README.md](../../backend/database/README.md) |
| Dificuldades ausentes | Registradas somente dificuldades comprovadas e itens que precisam ser confirmados pela equipe | [dificuldades_e_proximos_passos.md](./dificuldades_e_proximos_passos.md) |
| Próximos passos ausentes | Separados em pendências técnicas, testes, documentação e melhorias futuras | [dificuldades_e_proximos_passos.md](./dificuldades_e_proximos_passos.md) |
| Evidência do GitHub ausente | Registrado histórico, estado local, sincronização e pendência de autorização de commit/push | [evidencia_github.md](./evidencia_github.md) |

## Registro técnico complementar

- `tests/test_auth.py` recebeu testes diretos de redirecionamento sem sessão, acesso por perfil a `/usuarios` e `/relatorios/movimentacoes`, além de logout.
- Uma asserção incorreta do menu lateral foi corrigida para validar `hidden` e `data-roles`, em vez de procurar/remover texto no HTML.
- A saída dos testes foi preservada em `docs/sprint-9/evidencias/navegacao-permissoes-pytest.txt`.

## Limitações não transformadas em aprovações

- Docker/PostgreSQL/Nginx continuam bloqueados.
- Capturas visuais dos três perfis em navegador real não substituem os resultados existentes.
- Expiração real após 8 horas não foi aguardada.
