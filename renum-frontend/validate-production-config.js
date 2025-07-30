/**
 * Script para validar configuração de produção
 */

// Simular ambiente de produção
process.env.NODE_ENV = 'production';

console.log('🔍 Validação de Configuração de Produção');
console.log('=========================================');

// Verificar variáveis de ambiente
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws';

console.log('\n📋 Configuração Atual:');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('NEXT_PUBLIC_API_URL:', API_URL);
console.log('NEXT_PUBLIC_WEBSOCKET_URL:', WS_URL);

// Análise das URLs
console.log('\n🔍 Análise das URLs:');

// Verificar API URL
const isApiLocalhost = API_URL.includes('localhost') || API_URL.includes('127.0.0.1');
const isApiSecure = API_URL.startsWith('https://');
const hasCorrectApiDomain = API_URL.includes('api.renum.com.br') || API_URL.includes('157.180.39.41');

console.log('API URL Analysis:');
console.log('  - Is Localhost:', isApiLocalhost);
console.log('  - Is Secure (HTTPS):', isApiSecure);
console.log('  - Has Correct Domain:', hasCorrectApiDomain);

// Verificar WebSocket URL
const isWsLocalhost = WS_URL.includes('localhost') || WS_URL.includes('127.0.0.1');
const isWsSecure = WS_URL.startsWith('wss://');
const hasCorrectWsDomain = WS_URL.includes('api.renum.com.br') || WS_URL.includes('157.180.39.41');

console.log('WebSocket URL Analysis:');
console.log('  - Is Localhost:', isWsLocalhost);
console.log('  - Is Secure (WSS):', isWsSecure);
console.log('  - Has Correct Domain:', hasCorrectWsDomain);

// Identificar problemas
console.log('\n⚠️  Problemas Identificados:');

let hasProblems = false;

if (isApiLocalhost) {
  console.log('❌ API URL ainda aponta para localhost em produção');
  console.log('   Atual:', API_URL);
  console.log('   Esperado: https://api.renum.com.br ou https://157.180.39.41:porta');
  hasProblems = true;
}

if (!isApiSecure && !isApiLocalhost) {
  console.log('❌ API URL não está usando HTTPS');
  console.log('   Atual:', API_URL);
  console.log('   Esperado: https://...');
  hasProblems = true;
}

if (isWsLocalhost) {
  console.log('❌ WebSocket URL ainda aponta para localhost em produção');
  console.log('   Atual:', WS_URL);
  console.log('   Esperado: wss://api.renum.com.br/ws ou wss://157.180.39.41:porta/ws');
  hasProblems = true;
}

if (!isWsSecure && !isWsLocalhost) {
  console.log('❌ WebSocket URL não está usando WSS (WebSocket Secure)');
  console.log('   Atual:', WS_URL);
  console.log('   Esperado: wss://...');
  console.log('   CRÍTICO: Navegadores bloqueiam WS em páginas HTTPS (Mixed Content)');
  hasProblems = true;
}

// Sugestões de correção
if (hasProblems) {
  console.log('\n🔧 Sugestões de Correção:');
  
  if (isApiLocalhost || isWsLocalhost) {
    console.log('\n1. Verificar Variáveis de Ambiente no Vercel:');
    console.log('   - Acessar dashboard do Vercel');
    console.log('   - Ir em Settings > Environment Variables');
    console.log('   - Verificar se as variáveis estão definidas para Production');
    console.log('   - Fazer redeploy após alterar variáveis');
  }
  
  if (!isWsSecure && !isWsLocalhost) {
    console.log('\n2. Configurar SSL no Backend:');
    console.log('   - Backend precisa suportar WSS na porta especificada');
    console.log('   - Ou usar proxy reverso com SSL (nginx, cloudflare, etc.)');
    console.log('   - Ou configurar certificado SSL no servidor');
  }
  
  console.log('\n3. Configuração Recomendada para Produção:');
  console.log('   NEXT_PUBLIC_API_URL=https://api.renum.com.br');
  console.log('   NEXT_PUBLIC_WEBSOCKET_URL=wss://api.renum.com.br/ws');
  console.log('   OU');
  console.log('   NEXT_PUBLIC_API_URL=https://157.180.39.41:porta');
  console.log('   NEXT_PUBLIC_WEBSOCKET_URL=wss://157.180.39.41:porta/ws');
  
} else {
  console.log('\n✅ Configuração parece estar correta para produção!');
}

// Teste de conectividade (simulado)
console.log('\n🧪 Testes Recomendados:');
console.log('1. Testar API:', `curl -I ${API_URL}/api/health`);
console.log('2. Testar SSL WebSocket:', `openssl s_client -connect ${WS_URL.replace('wss://', '').replace('/ws', '')}`);
console.log('3. Verificar no navegador: Console > Network tab');

console.log('\n📊 Resumo:');
console.log('Status:', hasProblems ? '❌ PROBLEMAS ENCONTRADOS' : '✅ CONFIGURAÇÃO OK');
console.log('Próximo passo:', hasProblems ? 'Corrigir problemas identificados' : 'Testar em produção');