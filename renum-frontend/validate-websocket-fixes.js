#!/usr/bin/env node

/**
 * Script de validação das correções de WebSocket
 * 
 * Este script verifica se as correções implementadas para resolver
 * as falhas de conexão WebSocket estão funcionando corretamente.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validando correções de WebSocket...\n');

// 1. Verificar variáveis de ambiente
console.log('1. ✅ Verificando variáveis de ambiente:');

const envDev = path.join(__dirname, '.env.development');
const envProd = path.join(__dirname, '.env.production');

if (fs.existsSync(envDev)) {
  const devContent = fs.readFileSync(envDev, 'utf8');
  if (devContent.includes('NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws')) {
    console.log('   ✅ .env.development: NEXT_PUBLIC_WEBSOCKET_URL configurada corretamente');
  } else {
    console.log('   ❌ .env.development: NEXT_PUBLIC_WEBSOCKET_URL não encontrada ou incorreta');
  }
} else {
  console.log('   ❌ .env.development não encontrado');
}

if (fs.existsSync(envProd)) {
  const prodContent = fs.readFileSync(envProd, 'utf8');
  if (prodContent.includes('NEXT_PUBLIC_WEBSOCKET_URL=wss://api.renum.com.br/ws')) {
    console.log('   ✅ .env.production: NEXT_PUBLIC_WEBSOCKET_URL configurada corretamente');
  } else {
    console.log('   ❌ .env.production: NEXT_PUBLIC_WEBSOCKET_URL não encontrada ou incorreta');
  }
} else {
  console.log('   ❌ .env.production não encontrado');
}

// 2. Verificar uso consistente da variável
console.log('\n2. ✅ Verificando uso consistente da variável:');

const useWebSocketPath = path.join(__dirname, 'src/hooks/useWebSocket.ts');
if (fs.existsSync(useWebSocketPath)) {
  const useWebSocketContent = fs.readFileSync(useWebSocketPath, 'utf8');
  if (useWebSocketContent.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL')) {
    console.log('   ✅ useWebSocket.ts: Usando NEXT_PUBLIC_WEBSOCKET_URL');
  } else {
    console.log('   ❌ useWebSocket.ts: Não está usando NEXT_PUBLIC_WEBSOCKET_URL');
  }
} else {
  console.log('   ❌ useWebSocket.ts não encontrado');
}

const appPath = path.join(__dirname, 'src/pages/_app.tsx');
if (fs.existsSync(appPath)) {
  const appContent = fs.readFileSync(appPath, 'utf8');
  if (appContent.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL')) {
    console.log('   ✅ _app.tsx: Usando NEXT_PUBLIC_WEBSOCKET_URL');
  } else {
    console.log('   ❌ _app.tsx: Não está usando NEXT_PUBLIC_WEBSOCKET_URL');
  }
} else {
  console.log('   ❌ _app.tsx não encontrado');
}

// 3. Verificar estrutura de arquivos WebSocket
console.log('\n3. ✅ Verificando estrutura de arquivos WebSocket:');

const requiredFiles = [
  'src/contexts/WebSocketContext.tsx',
  'src/hooks/useWebSocket.ts',
  'src/services/websocket-service.ts',
  'src/types/websocket.ts',
  'src/constants/websocket.ts'
];

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`   ✅ ${file}: Encontrado`);
  } else {
    console.log(`   ❌ ${file}: Não encontrado`);
  }
});

// 4. Verificar configurações de build
console.log('\n4. ✅ Verificando configurações de build:');

const nextConfigPath = path.join(__dirname, 'next.config.js');
if (fs.existsSync(nextConfigPath)) {
  console.log('   ✅ next.config.js: Encontrado');
} else {
  console.log('   ❌ next.config.js: Não encontrado');
}

const packageJsonPath = path.join(__dirname, 'package.json');
if (fs.existsSync(packageJsonPath)) {
  const packageContent = fs.readFileSync(packageJsonPath, 'utf8');
  const packageJson = JSON.parse(packageContent);
  
  if (packageJson.scripts && packageJson.scripts.build) {
    console.log('   ✅ package.json: Script de build encontrado');
  } else {
    console.log('   ❌ package.json: Script de build não encontrado');
  }
} else {
  console.log('   ❌ package.json não encontrado');
}

console.log('\n🎯 Resumo das correções implementadas:');
console.log('   1. Adicionada variável NEXT_PUBLIC_WEBSOCKET_URL nos arquivos .env');
console.log('   2. Padronizado uso da variável em useWebSocket.ts e _app.tsx');
console.log('   3. Configurações de ambiente separadas para desenvolvimento e produção');
console.log('   4. URLs WebSocket corretas: ws://localhost:8000/ws (dev) e wss://api.renum.com.br/ws (prod)');

console.log('\n📋 Próximos passos para validação completa:');
console.log('   1. Verificar se o backend está configurado com CORS para domínios do Renum');
console.log('   2. Testar conexão WebSocket em ambiente de desenvolvimento');
console.log('   3. Testar conexão WebSocket em ambiente de produção (Vercel)');
console.log('   4. Validar autenticação via token JWT no WebSocket');

console.log('\n✅ Validação das correções de frontend concluída!');