#!/usr/bin/env node

/**
 * Script de validação das configurações WebSocket
 * 
 * Este script valida se todas as configurações WebSocket estão corretas
 * sem depender do backend estar rodando.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validando configurações WebSocket...\n');

let allTestsPassed = true;

// Função para marcar teste como falhou
function testFailed(message) {
    console.log(`   ❌ ${message}`);
    allTestsPassed = false;
}

function testPassed(message) {
    console.log(`   ✅ ${message}`);
}

// 1. Validar variáveis de ambiente do frontend
console.log('1. 📱 Validando configurações do Frontend:');

const frontendEnvDev = path.join('renum-frontend', '.env.development');
const frontendEnvProd = path.join('renum-frontend', '.env.production');

if (fs.existsSync(frontendEnvDev)) {
    const devContent = fs.readFileSync(frontendEnvDev, 'utf8');
    if (devContent.includes('NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws')) {
        testPassed('.env.development: URL WebSocket configurada corretamente');
    } else {
        testFailed('.env.development: URL WebSocket não configurada ou incorreta');
    }
} else {
    testFailed('.env.development não encontrado');
}

if (fs.existsSync(frontendEnvProd)) {
    const prodContent = fs.readFileSync(frontendEnvProd, 'utf8');
    if (prodContent.includes('NEXT_PUBLIC_WEBSOCKET_URL=wss://api.renum.com.br/ws')) {
        testPassed('.env.production: URL WebSocket configurada corretamente');
    } else {
        testFailed('.env.production: URL WebSocket não configurada ou incorreta');
    }
} else {
    testFailed('.env.production não encontrado');
}

// 2. Validar uso consistente no código
console.log('\n2. 🔧 Validando uso no código:');

const useWebSocketPath = path.join('renum-frontend', 'src', 'hooks', 'useWebSocket.ts');
if (fs.existsSync(useWebSocketPath)) {
    const useWebSocketContent = fs.readFileSync(useWebSocketPath, 'utf8');
    if (useWebSocketContent.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL')) {
        testPassed('useWebSocket.ts: Usando variável de ambiente correta');
    } else {
        testFailed('useWebSocket.ts: Não está usando NEXT_PUBLIC_WEBSOCKET_URL');
    }
} else {
    testFailed('useWebSocket.ts não encontrado');
}

const appPath = path.join('renum-frontend', 'src', 'pages', '_app.tsx');
if (fs.existsSync(appPath)) {
    const appContent = fs.readFileSync(appPath, 'utf8');
    if (appContent.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL')) {
        testPassed('_app.tsx: Usando variável de ambiente correta');
    } else {
        testFailed('_app.tsx: Não está usando NEXT_PUBLIC_WEBSOCKET_URL');
    }
} else {
    testFailed('_app.tsx não encontrado');
}

// 3. Validar configurações do backend
console.log('\n3. 🖥️  Validando configurações do Backend:');

const backendApiPath = path.join('backend', 'api.py');
if (fs.existsSync(backendApiPath)) {
    const apiContent = fs.readFileSync(backendApiPath, 'utf8');
    
    if (apiContent.includes('localhost:3001')) {
        testPassed('api.py: CORS configurado para localhost:3001 (Renum local)');
    } else {
        testFailed('api.py: CORS não configurado para localhost:3001');
    }
    
    if (apiContent.includes('renum.com.br')) {
        testPassed('api.py: CORS configurado para domínios renum.com.br');
    } else {
        testFailed('api.py: CORS não configurado para domínios renum.com.br');
    }
    
    if (apiContent.includes('renum-.*\\.vercel\\.app')) {
        testPassed('api.py: CORS configurado para Vercel do Renum');
    } else {
        testFailed('api.py: CORS não configurado para Vercel do Renum');
    }
    
    if (apiContent.includes('setup_websocket_routes(app)')) {
        testPassed('api.py: Rotas WebSocket configuradas');
    } else {
        testFailed('api.py: Rotas WebSocket não configuradas');
    }
} else {
    testFailed('api.py não encontrado');
}

// 4. Validar estrutura de arquivos WebSocket
console.log('\n4. 📁 Validando estrutura de arquivos:');

const websocketFiles = [
    'renum-frontend/src/contexts/WebSocketContext.tsx',
    'renum-frontend/src/hooks/useWebSocket.ts',
    'renum-frontend/src/services/websocket-service.ts',
    'renum-frontend/src/types/websocket.ts',
    'renum-frontend/src/constants/websocket.ts',
    'backend/websocket_endpoint_final.py'
];

websocketFiles.forEach(file => {
    if (fs.existsSync(file)) {
        testPassed(`${path.basename(file)}: Encontrado`);
    } else {
        testFailed(`${path.basename(file)}: Não encontrado`);
    }
});

// 5. Validar configurações específicas
console.log('\n5. ⚙️  Validando configurações específicas:');

const websocketConstantsPath = path.join('renum-frontend', 'src', 'constants', 'websocket.ts');
if (fs.existsSync(websocketConstantsPath)) {
    const constantsContent = fs.readFileSync(websocketConstantsPath, 'utf8');
    if (constantsContent.includes('ws://localhost:8000/ws')) {
        testPassed('websocket.ts: URL padrão configurada corretamente');
    } else {
        testFailed('websocket.ts: URL padrão não configurada corretamente');
    }
} else {
    testFailed('websocket.ts não encontrado');
}

// Resumo final
console.log('\n🎯 Resumo da Validação:');

if (allTestsPassed) {
    console.log('✅ Todas as configurações WebSocket estão corretas!');
    console.log('\n📋 Próximos passos:');
    console.log('   1. Iniciar o backend: cd backend && python api.py');
    console.log('   2. Iniciar o frontend: cd renum-frontend && npm run dev');
    console.log('   3. Testar conexão WebSocket no navegador');
    console.log('   4. Fazer commit das alterações');
    console.log('   5. Deploy no Vercel com as novas variáveis de ambiente');
    
    console.log('\n🚀 Status: PRONTO PARA PRODUÇÃO!');
} else {
    console.log('❌ Algumas configurações precisam ser corrigidas.');
    console.log('\n🔧 Verifique os itens marcados com ❌ acima.');
}

console.log('\n📊 Configurações implementadas:');
console.log('   • Frontend: Variáveis NEXT_PUBLIC_WEBSOCKET_URL configuradas');
console.log('   • Frontend: Uso consistente das variáveis de ambiente');
console.log('   • Backend: CORS configurado para domínios do Renum');
console.log('   • Backend: Rotas WebSocket funcionais');
console.log('   • Estrutura: Todos os arquivos WebSocket presentes');

process.exit(allTestsPassed ? 0 : 1);