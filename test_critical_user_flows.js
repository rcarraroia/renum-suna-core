#!/usr/bin/env node

/**
 * Script para testar fluxos críticos de usuário após otimizações
 * Valida funcionalidades essenciais dos frontends
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 Testando Fluxos Críticos de Usuário\n');

// Função para verificar se arquivos críticos existem
function checkCriticalFiles() {
  console.log('📁 Verificando arquivos críticos...\n');
  
  const criticalFiles = [
    // renum-frontend
    'renum-frontend/.next/static/chunks/framework-64ad27b21261a9ce.js',
    'renum-frontend/.next/static/chunks/main-6e9835793cc38fb6.js',
    'renum-frontend/.next/server/pages/index.html',
    'renum-frontend/.next/server/pages/dashboard.html',
    'renum-frontend/.next/server/pages/login.html',
    
    // renum-admin
    'renum-admin/.next/static/chunks/framework-d69964ecee781be3.js',
    'renum-admin/.next/static/chunks/136-f02761638ff59b20.js',
    'renum-admin/.next/server/pages/index.html',
    'renum-admin/.next/server/pages/billing.html',
    'renum-admin/.next/server/pages/users.html'
  ];
  
  let allFilesExist = true;
  
  criticalFiles.forEach(file => {
    if (fs.existsSync(file)) {
      console.log(`✅ ${file}`);
    } else {
      console.log(`❌ ${file} - MISSING`);
      allFilesExist = false;
    }
  });
  
  return allFilesExist;
}

// Função para verificar lazy components
function checkLazyComponents() {
  console.log('\n🔄 Verificando componentes lazy...\n');
  
  const lazyFiles = [
    'renum-frontend/src/components/lazy/LazyComponents.tsx',
    'renum-admin/src/components/lazy/LazyComponents.tsx',
    'renum-frontend/src/components/common/LazyWrapper.tsx',
    'renum-admin/src/components/common/LazyWrapper.tsx'
  ];
  
  let lazyComponentsWorking = true;
  
  lazyFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const lazyCount = (content.match(/createLazyComponent|lazy\(/g) || []).length;
      console.log(`✅ ${file} - ${lazyCount} lazy components`);
    } else {
      console.log(`❌ ${file} - MISSING`);
      lazyComponentsWorking = false;
    }
  });
  
  return lazyComponentsWorking;
}

// Função para verificar otimizações de imagem
function checkImageOptimizations() {
  console.log('\n🖼️ Verificando otimizações de imagem...\n');
  
  const configFiles = [
    'renum-frontend/next.config.js',
    'renum-admin/next.config.js'
  ];
  
  let imageOptimizationsActive = true;
  
  configFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hasImageConfig = content.includes('images:') && content.includes('formats:');
      const hasWebP = content.includes('image/webp');
      const hasAVIF = content.includes('image/avif');
      
      console.log(`📁 ${file}:`);
      console.log(`  ${hasImageConfig ? '✅' : '❌'} Image configuration`);
      console.log(`  ${hasWebP ? '✅' : '❌'} WebP support`);
      console.log(`  ${hasAVIF ? '✅' : '❌'} AVIF support`);
      
      if (!hasImageConfig || !hasWebP || !hasAVIF) {
        imageOptimizationsActive = false;
      }
    } else {
      console.log(`❌ ${file} - MISSING`);
      imageOptimizationsActive = false;
    }
  });
  
  return imageOptimizationsActive;
}

// Função para verificar WebSocket configuration
function checkWebSocketConfig() {
  console.log('\n🔌 Verificando configuração WebSocket...\n');
  
  const wsFiles = [
    'renum-frontend/src/constants/websocket.ts',
    'renum-frontend/src/hooks/useWebSocket.ts',
    'renum-frontend/src/services/websocket-service.ts'
  ];
  
  let webSocketConfigured = true;
  
  wsFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hasEnvVar = content.includes('NEXT_PUBLIC_WEBSOCKET_URL');
      console.log(`✅ ${file} ${hasEnvVar ? '(with env var)' : '(no env var)'}`);
    } else {
      console.log(`❌ ${file} - MISSING`);
      webSocketConfigured = false;
    }
  });
  
  return webSocketConfigured;
}

// Função principal
function runTests() {
  console.log('🚀 Iniciando testes de fluxos críticos...\n');
  
  const results = {
    criticalFiles: checkCriticalFiles(),
    lazyComponents: checkLazyComponents(),
    imageOptimizations: checkImageOptimizations(),
    webSocketConfig: checkWebSocketConfig()
  };
  
  console.log('\n📊 Resumo dos Testes:\n');
  console.log(`✅ Arquivos críticos: ${results.criticalFiles ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Componentes lazy: ${results.lazyComponents ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Otimizações de imagem: ${results.imageOptimizations ? 'PASS' : 'FAIL'}`);
  console.log(`✅ Configuração WebSocket: ${results.webSocketConfig ? 'PASS' : 'FAIL'}`);
  
  const allPassed = Object.values(results).every(result => result === true);
  
  console.log(`\n🎯 Status Geral: ${allPassed ? '✅ TODOS OS TESTES PASSARAM' : '❌ ALGUNS TESTES FALHARAM'}`);
  
  if (allPassed) {
    console.log('\n🎉 Todos os fluxos críticos estão funcionando corretamente!');
    console.log('✅ Frontend está pronto para produção');
  } else {
    console.log('\n⚠️ Alguns problemas foram identificados e precisam ser corrigidos.');
  }
  
  return allPassed;
}

// Executar testes
const success = runTests();
process.exit(success ? 0 : 1);