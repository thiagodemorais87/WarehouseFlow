# Verificação de secrets — Sprint 11

**Data:** 19/11/2026

## Resultado

Não foram encontrados arquivos `.env`, certificados privados ou padrões de
tokens/chaves privadas versionados nesta revisão.
O `.env` local está protegido pelo `.gitignore` e o repositório acompanha
`.env.example` sem a exposição de uma chave privada.

## Arquivos examinados

- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- arquivos configurados no Git

## Conduta

- Não reproduzir valores reais de `SECRET_KEY`, senhas ou tokens.
- Não publicar o `.env` local.
- Substituir o placeholder do `.env.example` em ambientes reais.
- Alterar senhas padrão em ambientes compartilhados.

## Pendências

- A equipe deve confirmar se existem secrets em variáveis de ambiente fora do
  repositório ou em históricos remotos.
- Valores reais de banco e JWT devem ser gerados por ambiente seguro.
