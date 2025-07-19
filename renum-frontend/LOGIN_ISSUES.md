# Solução de Problemas de Login

Este documento contém informações para resolver problemas comuns de login na aplicação Renum Frontend.

## Problemas Comuns

### 1. Erro de Autenticação no Vercel

Se você estiver enfrentando problemas de login no ambiente de produção do Vercel, verifique os seguintes pontos:

#### Configuração de Ambiente

Certifique-se de que a variável de ambiente `NEXT_PUBLIC_API_URL` está configurada corretamente no painel do Vercel:

1. Acesse o painel do projeto no Vercel
2. Vá para "Settings" > "Environment Variables"
3. Verifique se `NEXT_PUBLIC_API_URL` está configurada com a URL correta da API (ex: `https://api.renum.com.br`)

#### CORS (Cross-Origin Resource Sharing)

Se o backend estiver rejeitando as requisições, verifique se o CORS está configurado corretamente:

1. No backend, certifique-se de que o domínio do frontend (ex: `renum-frontend.vercel.app`) está na lista de origens permitidas
2. Verifique se o backend está enviando os headers CORS corretos:
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Methods`
   - `Access-Control-Allow-Headers`

#### Cookies e LocalStorage

Se o login falhar devido a problemas com cookies ou localStorage:

1. Verifique se o navegador não está bloqueando cookies ou localStorage
2. Tente usar o modo de navegação normal (não incógnito)
3. Limpe o cache e cookies do navegador

### 2. Credenciais de Demonstração

Para testar o login sem precisar de uma conta real, use as credenciais de demonstração:

- Email: `demo@renum.com`
- Senha: `password`

### 3. Problemas com LocalStorage

Se o localStorage não estiver funcionando corretamente:

1. Verifique se o navegador tem suporte a localStorage
2. Verifique se o localStorage não está cheio
3. Verifique se o navegador não está no modo privado/incógnito

## Depuração

Para ajudar na depuração de problemas de login:

1. Abra o console do navegador (F12 ou Ctrl+Shift+I)
2. Verifique se há erros relacionados a CORS, localStorage ou fetch
3. Verifique a aba "Network" para ver as requisições HTTP e suas respostas
4. Use o botão "Conta de demonstração" para testar o login sem precisar digitar credenciais

## Contato

Se os problemas persistirem, entre em contato com a equipe de suporte:

- Email: suporte@renum.com.br
- Discord: [Link para o servidor Discord]