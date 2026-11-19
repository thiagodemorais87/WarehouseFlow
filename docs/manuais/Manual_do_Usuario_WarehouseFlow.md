# Manual do Usuário — WarehouseFlow

## 1. Apresentação

O WarehouseFlow é um sistema web para gerenciamento de operações de armazém.
Ele auxilia no controle de produtos, estoque, posições físicas, pedidos,
recebimento, expedição, tarefas operacionais e relatórios.

O sistema também utiliza o motor de otimização NN + 2-opt para calcular uma
sequência de visita às posições de picking e apresentar métricas de distância.

**Objetivo:** organizar dados operacionais e apoiar a tomada de decisão com
indicadores e uma rota sugerida para separação.

**Problema tratado:** evitar separações pouco organizadas e deslocamentos
desnecessários entre posições de um armazém.

**Público-alvo:** administradores, gestores e operadores de armazém que
utilizam o sistema no ambiente web.

## 2. Requisitos para utilização

- Navegador moderno compatível com HTML, CSS e JavaScript, como uma versão
  atualizada do Google Chrome, Microsoft Edge ou Firefox.
- Conexão com o endereço do sistema configurado pela equipe.
- Conta ativa com e-mail e senha.
- Ambientes conhecidos:
  - interface/API via Docker: `http://127.0.0.1:8080`;
  - API local diretamente pela FastAPI: `http://127.0.0.1:8000`;
  - Swagger: `http://127.0.0.1:8000/docs`.

Esses endereços são para o ambiente local conhecido. Em uma rede corporativa,
a equipe deverá informar o endereço publicado.

## 3. Acesso ao sistema

### Login

1. Abra `/login` no navegador.
2. Informe o e-mail cadastrado.
3. Informe a senha.
4. Selecione o botão de acesso.

Após credenciais válidas, o sistema cria uma sessão por cookie HttpOnly e
direciona para `/inicio`.

### Encerrar sessão

1. Selecione **Sair** no menu lateral.
2. O sistema removerá o cookie de acesso e abrirá a tela de login.

Após o logout, abrir diretamente uma página protegida deverá redirecionar ao
login.

### Falhas de autenticação

- E-mail ou senha incorretos: revise os dados e tente novamente.
- Usuário inativo: procure o administrador.
- Sessão expirada ou token inválido: realize login novamente.
- Acesso negado: o perfil utilizado não possui a operação solicitada.

## 4. Perfis implementados

| Perfil | Acessos e operações |
|---|---|
| `ADMIN` | Pode consultar e administrar usuários/cargos, gerenciar produtos, estoque, posições, pedidos e tarefas, visualizar relatórios gerenciais e executar operações liberadas pelo backend. |
| `GESTOR` | Pode consultar os módulos e gerenciar produtos, estoque, posições, pedidos e tarefas conforme as regras da API, além de acessar relatórios gerenciais. Não administra usuários. |
| `OPERADOR` | Pode consultar os módulos permitidos, criar/alterar pedidos e tarefas, movimentar estoque, otimizar rotas e consultar o dashboard. Opera sem autorização apenas tarefas atribuídas a si. Não cria/edita produtos, exclui tarefas/pedidos/estoque conforme regras administrativas e não acessa gerenciamento de usuários ou relatórios gerenciais. |

Os links restritos podem ficar ocultos no menu, mas o backend continua
validando o acesso direto pela URL e pelas APIs.

## 5. Funcionalidades

### Dashboard

- **Para que serve:** apresentar indicadores operacionais e resumo da operação.
- **Acesso:** menu **Dashboard**.
- **Como utilizar:** faça login e abra o dashboard.
- **Resultado esperado:** contagens de pedidos, tarefas, estoque e otimizações
  conforme o perfil.

### Produtos

- **Como acessar:** menu **Produtos**.
- **Cadastro:** clique em novo/cadastrar, informe SKU, nome, descrição opcional,
  peso e volume.
- **Campos importantes:** SKU deve ser único; peso e volume não devem ser
  negativos.
- **Atualização:** edite o registro e salve.
- **Exclusão:** o produto só pode ser removido sem vínculos de estoque ou itens
  de pedido. Quando houver dependência, o sistema informa conflito HTTP `409`
  e preserva o registro.
- **Erros comuns:** campos obrigatórios vazios, peso/volume negativo, SKU
  duplicado e tentativa de exclusão de produto vinculado.

### Estoque

- **Como acessar:** menu **Estoque**.
- **Uso:** consultar saldos e realizar entradas/saídas conforme autorização.
- **Campos importantes:** produto, posição, quantidade.
- **Resultado esperado:** saldo atualizado e mensagem de sucesso.
- **Erros comuns:** quantidade negativa ou maior que o saldo disponível,
  produto/posição inexistente e falta de autorização.

### Localizações e posições

- **Como acessar:** menu **Posições**.
- **Uso:** consultar armazéns e posições; criar/editar posições quando permitido.
- **Campos importantes:** código da posição, corredor, estante, nível e armazém.
- **Erros comuns:** código duplicado, armazém inexistente e operação bloqueada
  para `OPERADOR`.

### Pedidos

- **Como acessar:** menu **Pedidos**.
- **Criação:** selecione INBOUND ou OUTBOUND, informe itens e quantidades.
- **Quantidade:** deve ser maior que zero.
- **Status:** `PENDING`, `PROCESSING`, `COMPLETED` ou `CANCELLED`.
- **Recebimento:** pedidos INBOUND representam entrada de mercadorias.
- **Expedição:** pedidos OUTBOUND representam saída e podem alimentar tarefas de
  picking e otimização.
- **Erros comuns:** quantidade zero ou negativa, produto inexistente, item vazio
  e exclusão sem autorização.

### Tarefas

- **Como acessar:** menu **Tarefas**.
- **Tipos:** `PICKING`, `PUTAWAY` e `REPLENISHMENT`.
- **Uso:** vincular a um pedido, atribuir responsável e alterar status.
- **Restrições:** `OPERADOR` não pode reatribuir tarefas nem alterar tarefas de
  outros usuários; exclusão é limitada a `ADMIN` e `GESTOR`.

### Otimização de rotas

- **Como acessar:** menu **Otimização**.
- **Opções:** informar posições manualmente ou selecionar um pedido OUTBOUND.
- **Resultado:** rota Nearest Neighbor, melhoria 2-opt, distância antes/depois,
  redução percentual e tempo de execução.
- **Erros comuns:** IDs duplicados, pedido sem posições encontradas, coordenadas
  inválidas e falta de autenticação.

### Relatórios

- **Dashboard:** disponível a usuários autenticados.
- **Relatório de Picking:** mostra histórico das execuções e pode estar disponível
  conforme a tela implementada.
- **Relatório de Pedidos:** limitado a `ADMIN` e `GESTOR`.
- **Movimentações de estoque:** limitado a `ADMIN` e `GESTOR`.
- **Exportação CSV:** disponível nos relatórios gerenciais implementados pela API.

### Usuários

- **Como acessar:** somente pelo ambiente autenticado como `ADMIN`, na opção
  **Usuários**.
- **Uso:** consultar, criar, editar, ativar/desativar ou excluir usuários/cargos
  conforme autorização.
- Senhas são armazenadas como hash e não são devolvidas pela API.
- **Erros comuns:** e-mail inválido ou duplicado, senha curta, cargo inexistente
  ou acesso feito por outro perfil.

## 6. Solução de problemas

| Situação | Orientação |
|---|---|
| Página retorna ao login | Faça login novamente; a sessão pode ter expirado ou o cookie pode ter sido removido. |
| “E-mail ou senha incorretos” | Confira capitalização, espaços e cadastro da conta. |
| “Acesso negado” | O perfil atual não tem permissão. Solicite acesso ao administrador. |
| Tela não aparece no menu | A opção pode estar condicionada ao perfil; não tente usar a URL sem autorização. |
| SKU duplicado | Use um código exclusivo ou edite o produto existente. |
| Quantidade inválida | Informe quantidade inteira maior que zero. |
| Produto não pode ser excluído | Remova ou desvincule primeiro estoque e itens de pedidos associados. |
| Página não carrega | Atualize a página e confirme se API e frontend estão ativos. |
| Resposta 401 | Faça login novamente. |
| Resposta 403 | Solicite ao administrador as permissões necessárias. |
| Resposta 409 | O registro possui conflito ou dependência; revise vínculos e duplicidades. |

## 7. Perguntas frequentes

**Posso usar o sistema sem login?** Não. Todas as páginas operacionais exigem
autenticação.

**O operador pode administrar usuários?** Não. Essa operação exige `ADMIN`.

**O operador pode excluir uma tarefa?** Não. Exclusão de tarefa exige
`ADMIN` ou `GESTOR`.

**Posso excluir um produto usado em pedidos ou estoque?** Não. O sistema
bloqueia a exclusão e informa o conflito.

**Como recebo mercadorias?** Use pedidos INBOUND e controle o estoque pelas
operações do módulo correspondente.

**Como otimizar uma expedição?** Selecione um pedido OUTBOUND na tela de
Otimização e execute o cálculo.

**A otimização garante a menor rota possível?** O motor usa heurísticas
Nearest Neighbor e 2-opt. A redução é informada pelas métricas; não é
representada como solução exata global.

## 8. Glossário

- **ADMIN:** perfil com maior nível administrativo.
- **GESTOR:** perfil gerencial com acesso a relatórios e operações de gestão.
- **OPERADOR:** perfil operacional com restrições administrativas.
- **JWT:** token usado para autenticar chamadas da API.
- **SKU:** código único de identificação do produto.
- **INBOUND:** pedido de entrada/recebimento.
- **OUTBOUND:** pedido de saída/expedição.
- **PICKING:** separação de itens de pedido.
- **PUTAWAY:** armazenamento de mercadoria em posição.
- **REPLENISHMENT:** reposição de estoque.
- **2-opt:** melhoria local usada para reduzir a rota sugerida.
- **Nearest Neighbor:** heurística que escolhe sequencialmente posições próximas.
- **HTTP 401:** ausência ou invalidação da autenticação.
- **HTTP 403:** usuário autenticado sem permissão.
- **HTTP 409:** conflito de negócio ou dependência.

## 9. Considerações finais

### Evidências visuais disponíveis

- Login, dashboard, filtros, pedidos, tarefas, relatórios e correção de
  exclusão: [docs/sprint-9/evidencias](../sprint-9/evidencias).
- Sprint 10: [docs/sprint-10/evidencias](../sprint-10/evidencias).
- Evidências do motor: [docs/sprint-11/evidencias](../sprint-11/evidencias).

### Capturas ainda pendentes

Capturas visuais reais ainda precisam ser registradas para os fluxos por
perfil em navegador real, incluindo `/usuarios` e
`/relatorios/movimentacoes`, além da execução completa em Docker/PostgreSQL.
Essas lacunas devem ser preenchidas pela equipe antes do encerramento do
ensaio final, sem substituir screenshots existentes.
