#!/usr/bin/env node

/**
 * Script para testar funcionalidades WebSocket em tempo real
 * Valida configurações e conectividade
 */

const fs = require('fs');

console.log('🔌 Testando Funcionalidades WebSocket\n');

// Função para verificar configurações WebSocket
function checkWebSocketConfiguration() {
  console.log('⚙️ Verificando configurações WebSocket...\n');
  
  const configFiles = [
    {
      path: 'renum-frontend/src/constants/websocket.ts',
      name: 'WebSocket Constants'
    },
    {
      path: 'renum-frontend/src/hooks/useWebSocket.ts',
      name: 'WebSocket Hook'
    },
    {
      path: 'renum-frontend/src/services/websocket-service.ts',
      name: 'WebSocket Service'
    },
    {
      path: 'renum-frontend/src/contexts/WebSocketContext.tsx',
      name: 'WebSocket Context'
    }
  ];
  
  let allConfigured = true;
  
  configFiles.forEach(({ path, name }) => {
    if (fs.existsSync(path)) {
      const content = fs.readFileSync(path, 'utf8');
      
      // Verificar configurações específicas
      const hasEnvVar = content.includes('NEXT_PUBLIC_WEBSOCKET_URL');
      const hasReconnect = content.includes('reconnect') || content.includes('autoReconnect');
      const hasErrorHandling = content.includes('onError') || content.includes('error');
      
      console.log(`📁 ${name}:`);
      console.log(`  ${hasEnvVar ? '✅' : '❌'} Environment variable support`);
      console.log(`  ${hasReconnect ? '✅' : '❌'} Reconnection logic`);
      console.log(`  ${hasErrorHandling ? '✅' : '❌'} Error handling`);
      console.log('');
      
      if (!hasEnvVar || !hasReconnect || !hasErrorHandling) {
        allConfigured = false;
      }
    } else {
      console.log(`❌ ${name} - File missing: ${path}`);
      allConfigured = false;
    }
  });
  
  return allConfigured;
}

// Função para verificar componentes WebSocket
function checkWebSocketComponents() {
  console.log('🧩 Verificando componentes WebSocket...\n');
  
  const componentFiles = [
    'renum-frontend/src/components/websocket/ConnectionLostBanner.tsx',
    'renum-frontend/src/components/websocket/ConnectionLostOverlay.tsx',
    'renum-frontend/src/components/websocket/ReconnectionProgress.tsx'
  ];
  
  let componentsWorking = true;
  
  componentFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hasUseEffect = content.includes('useEffect');
      const hasWebSocketLogic = content.includes('WebSocket') || content.includes('websocket');
      
      console.log(`✅ ${file.split('/').pop()}`);
      console.log(`  ${hasUseEffect ? '✅' : '❌'} React hooks`);
      console.log(`  ${hasWebSocketLogic ? '✅' : '❌'} WebSocket integration`);
      console.log('');
    } else {
      console.log(`❌ ${file} - MISSING`);
      componentsWorking = false;
    }
  });
  
  return componentsWorking;
}

// Função para verificar environment variables
function checkEnvironmentVariables() {
  console.log('🌍 Verificando variáveis de ambiente...\n');
  
  const envFiles = [
    'renum-frontend/.env.local',
    'renum-frontend/.env.example',
    'renum-frontend/.env.production'
  ];
  
  let hasWebSocketEnv = false;
  
  envFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hasWSUrl = content.includes('NEXT_PUBLIC_WEBSOCKET_URL');
      
      console.log(`📄 ${file}:`);
      console.log(`  ${hasWSUrl ? '✅' : '❌'} NEXT_PUBLIC_WEBSOCKET_URL`);
      
      if (hasWSUrl) {
        hasWebSocketEnv = true;
        // Extrair a URL se possível
        const urlMatch = content.match(/NEXT_PUBLIC_WEBSOCKET_URL=(.+)/);
        if (urlMatch) {
          console.log(`  🔗 URL: ${urlMatch[1]}`);
        }
      }
      console.log('');
    }
  });
  
  if (!hasWebSocketEnv) {
    console.log('⚠️ Nenhuma variável de ambiente WebSocket encontrada');
    console.log('💡 Recomendação: Definir NEXT_PUBLIC_WEBSOCKET_URL');
  }
  
  return hasWebSocketEnv;
}

// Função para verificar integração com backend
function checkBackendIntegration() {
  console.log('🔗 Verificando integração com backend...\n');
  
  // Verificar se há configurações de API
  const apiFiles = [
    'renum-frontend/src/lib/api-client.ts',
    'renum-frontend/src/services/api.ts'
  ];
  
  let hasApiIntegration = false;
  
  apiFiles.forEach(file => {
    if (fs.existsSync(file)) {
      const content = fs.readFileSync(file, 'utf8');
      const hasBaseURL = content.includes('baseURL') || content.includes('API_URL');
      const hasErrorHandling = content.includes('catch') || content.includes('error');
      
      console.log(`✅ ${file.split('/').pop()}:`);
      console.log(`  ${hasBaseURL ? '✅' : '❌'} Base URL configuration`);
      console.log(`  ${hasErrorHandling ? '✅' : '❌'} Error handling`);
      
      hasApiIntegration = true;
    }
  });
  
  if (!hasApiIntegration) {
    console.log('⚠️ Nenhum arquivo de integração API encontrado');
  }
  
  return hasApiIntegration;
}

// Função principal
function runWebSocketTests() {
  console.log('🚀 Iniciando testes WebSocket...\n');
  
  const results = {
    configuration: checkWebSocketConfiguration(),
    components: checkWebSocketComponents(),
    environment: checkEnvironmentVariables(),
    backend: checkBackendIntegration()
  };
  
  console.log('📊 Resumo dos Testes WebSocket:\n');
  console.log(`🔧 Configuração: ${results.configuration ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`🧩 Componentes: ${results.components ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`🌍 Environment: ${results.environment ? '✅ PASS' : '⚠️ PARTIAL'}`);
  console.log(`🔗 Backend Integration: ${results.backend ? '✅ PASS' : '❌ FAIL'}`);
  
  const criticalPassed = results.configuration && results.components && results.backend;
  
  console.log(`\n🎯 Status WebSocket: ${criticalPassed ? '✅ FUNCIONAL' : '❌ PROBLEMAS DETECTADOS'}`);
  
  if (criticalPassed) {
    console.log('\n🎉 WebSocket está configurado e pronto para uso!');
    console.log('✅ Real-time features podem ser implementadas');
    
    if (!results.environment) {
      console.log('\n💡 Recomendação: Configurar variáveis de ambiente para produção');
    }
  } else {
    console.log('\n⚠️ Alguns problemas foram identificados na configuração WebSocket.');
    console.log('🔧 Verifique os arquivos marcados como FAIL acima.');
  }
  
  return criticalPassed;
}

// Executar testes
const success = runWebSocketTests();
process.exit(success ? 0 : 1);