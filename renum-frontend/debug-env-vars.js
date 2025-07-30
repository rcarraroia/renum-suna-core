/**
 * Script de diagnóstico para verificar variáveis de ambiente
 */

console.log('🔍 Diagnóstico de Variáveis de Ambiente');
console.log('=====================================');

// Verificar variáveis de ambiente
console.log('\n📋 Variáveis de Ambiente:');
console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
console.log('NEXT_PUBLIC_WEBSOCKET_URL:', process.env.NEXT_PUBLIC_WEBSOCKET_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);

// Verificar se estamos no browser
const isBrowser = typeof window !== 'undefined';
console.log('\n🌐 Ambiente:');
console.log('Is Browser:', isBrowser);
console.log('Is Server:', !isBrowser);

if (isBrowser) {
  console.log('Window location:', window.location.href);
  console.log('User Agent:', navigator.userAgent);
}

// Verificar URLs que serão usadas
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws';

console.log('\n🔗 URLs Configuradas:');
console.log('API Base URL:', API_BASE_URL);
console.log('WebSocket URL:', WEBSOCKET_URL);

// Verificar se as URLs estão corretas para produção
const isProduction = process.env.NODE_ENV === 'production';
const hasCorrectApiUrl = API_BASE_URL.includes('api.renum.com.br') || API_BASE_URL.includes('157.180.39.41');
const hasCorrectWsUrl = WEBSOCKET_URL.includes('wss://') && (WEBSOCKET_URL.includes('api.renum.com.br') || WEBSOCKET_URL.includes('157.180.39.41'));

console.log('\n✅ Verificações:');
console.log('Is Production:', isProduction);
console.log('Has Correct API URL:', hasCorrectApiUrl);
console.log('Has Correct WebSocket URL:', hasCorrectWsUrl);

if (isProduction) {
  console.log('\n⚠️  Problemas Identificados:');
  
  if (!hasCorrectApiUrl) {
    console.log('❌ API URL ainda aponta para localhost em produção');
    console.log('   Esperado: https://api.renum.com.br ou https://157.180.39.41:porta');
    console.log('   Atual:', API_BASE_URL);
  }
  
  if (!hasCorrectWsUrl) {
    console.log('❌ WebSocket URL não está usando WSS ou aponta para localhost');
    console.log('   Esperado: wss://api.renum.com.br/ws ou wss://157.180.39.41:porta/ws');
    console.log('   Atual:', WEBSOCKET_URL);
  }
  
  if (hasCorrectApiUrl && hasCorrectWsUrl) {
    console.log('✅ Todas as URLs estão configuradas corretamente para produção');
  }
} else {
  console.log('\n🏠 Ambiente de desenvolvimento - URLs localhost são esperadas');
}

// Testar conectividade (apenas no browser)
if (isBrowser) {
  console.log('\n🧪 Testando Conectividade...');
  
  // Testar API
  fetch(`${API_BASE_URL}/api/health`)
    .then(response => {
      console.log('✅ API Health Check:', response.status, response.statusText);
    })
    .catch(error => {
      console.log('❌ API Health Check Failed:', error.message);
    });
  
  // Testar WebSocket (apenas log, não conectar de verdade)
  console.log('🔌 WebSocket URL que será usada:', WEBSOCKET_URL);
  
  if (WEBSOCKET_URL.startsWith('ws://') && window.location.protocol === 'https:') {
    console.log('⚠️  MIXED CONTENT WARNING: Tentando usar WebSocket inseguro (ws://) em página HTTPS');
    console.log('   Isso será bloqueado pelo navegador por segurança');
  }
}

export default function DebugEnvVars() {
  return null; // Este é apenas um script de diagnóstico
}