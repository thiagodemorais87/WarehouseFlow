# 📄 Documentação Oficial — Sprint 01
**Módulo:** Autenticação, Gestão de Usuários e Controle de Acesso (RBAC)  
**Responsável:** Pessoa 2  
**Branch:** `feature/auth-users`  

---

## 🎯 1. Visão Geral
Esta documentação estabelece as diretrizes de **autenticação**, **gestão de usuários** e **controle de acesso baseado em papéis (RBAC - Role-Based Access Control)** para o sistema **WarehouseFlow**.

O objetivo é garantir que apenas usuários autenticados acessem o sistema e que cada perfil possua permissões estritamente limitadas às suas responsabilidades operacionais dentro do galpão.

---

## 👥 2. Mapeamento de Perfis de Usuário

O sistema opera com três níveis de acesso hierárquicos:

              ┌──────────────┐
              │    ADMIN     │ (Acesso Total)
              └──────┬───────┘
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
┌─────────────┐               ┌─────────────┐
│   GESTOR    │               │  OPERADOR   │
└─────────────┘               └─────────────┘
(Gestão e Indicadores)         (Operação de Chão)


### Descrição dos Papéis
* **ADMIN (Administrador):** Possui controle total sobre o sistema. Responsável por cadastrar, editar e remover usuários, além de ter acesso a todos os módulos operacionais e de configuração.
* **GESTOR (Gestor de Estoque/Operações):** Focado em análise, métricas e planejamento. Possui acesso à visualização e edição de estoques, acompanhamento de pedidos, indicadores de desempenho (KPIs) e ao motor de otimização de rotas/armazenamento.
* **OPERADOR (Operador de Galpão):** Focado na execução prática do dia a dia. Acessa a consulta básica de estoque, movimentação direta de itens, atualização do status de pedidos e execução de listas de tarefas.

---

## 🔐 3. Matriz de Permissões e Regras de Acesso

| Módulo / Funcionalidade | Rota / Endpoint | ADMIN | GESTOR | OPERADOR |
| :--- | :--- | :---: | :---: | :---: |
| **Login e Autenticação** | `POST /auth/login` | 🟢 Livre | 🟢 Livre | 🟢 Livre |
| **Gerenciar Usuários** | `POST, GET, PUT, DELETE /users` | 🟢 Total | 🔴 Negado | 🔴 Negado |
| **Visualizar Estoque** | `GET /stock` | 🟢 Total | 🟢 Total | 🟢 Total |
| **Movimentar / Editar Estoque** | `POST, PUT /stock` | 🟢 Total | 🟢 Total | 🟢 Total |
| **Relatórios e Indicadores** | `GET /analytics` | 🟢 Total | 🟢 Total | 🔴 Negado |
| **Motor de Otimização** | `POST /optimization` | 🟢 Total | 🟢 Total | 🔴 Negado |
| **Executar Tarefas de Coleta** | `POST /tasks/{id}/execute` | 🟢 Total | 🟢 Total | 🟢 Execução |

---

## 🛠️ 4. Arquitetura de Segurança (Sprint 02)

### 4.1. Autenticação via JWT (JSON Web Token)
* A autenticação será realizada via token no padrão **OAuth2 com Bearer Token**.
* O token terá tempo de expiração definido (ex: 8 horas) e carregará no *payload* as informações básicas do usuário:
  ```json
  {
    "sub": "user_id_123",
    "email": "operador@warehouseflow.com",
    "role": "OPERADOR",
    "exp": 1700000000

    4.2. Segurança de Senhas
As senhas nunca serão armazenadas em texto plano.

Utilização do algoritmo Bcrypt para criptografia/hashing de senha antes da gravação no banco de dados.

📌 5. Rastreabilidade (GitHub Issues)
Esta especificação atende às seguintes issues do repositório:

#10: Criar autenticação (POST /auth/login)

#11: Criar cadastro de usuários (/users)

#12: Implementar perfis (ADMIN, GESTOR, OPERADOR)

#13: Implementar permissões (Middleware de bloqueio de rotas)