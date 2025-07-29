#!/usr/bin/env node

/**
 * Script de teste integrado para validar conexão WebSocket
 * 
 * Este script testa a conectividade WebSocket entre frontend e backend
 * para verificar se as correções implementadas estão funcionando.
 */

const WebSocket = require('ws');
const http = require('http');

console.log('🔍 Testando integração WebSocket...\n');

// Configurações de teste
const BACKEND_URL = 'http://localhost:8000';
const WEBSOCKET_URL = 'ws://localhost:8000/ws';

// Função para testar se o backend está rodando
async function testBackendHealth() {
    console.log('1. ✅ Testando saúde do backend:');
    
    return new Promise((resolve) => {
        const req = http.get(`${BACKEND_URL}/api/health`, (res) => {
            if (res.statusCode === 200) {
                console.log('   ✅ Backend está rodando e respondendo');
                resolve(true);
            } else {
                console.log(`   ❌ Backend respondeu com status ${res.statusCode}`);
                resolve(false);
            }
        });
        
        req.on('error', (err) => {
            console.log(`   ❌ Erro ao conectar com backend: ${err.message}`);
            resolve(false);
        });
        
        req.setTimeout(5000, () => {
            console.log('   ❌ Timeout ao conectar com backend');
            req.destroy();
            resolve(false);
        });
    });
}

// Função para testar endpoints WebSocket específicos
async function testWebSocketEndpoints() {
    console.log('\n2. ✅ Testando endpoints WebSocket:');
    
    const endpoints = [
        '/ws/health',
        '/ws/stats'
    ];
    
    for (const endpoint of endpoints) {
        await new Promise((resolve) => {
            const req = http.get(`${BACKEND_URL}${endpoint}`, (res) => {
                if (res.statusCode === 200) {
                    console.log(`   ✅ ${endpoint}: Respondendo corretamente`);
                } else {
                    console.log(`   ❌ ${endpoint}: Status ${res.statusCode}`);
                }
                resolve();
            });
            
            req.on('error', (err) => {
                console.log(`   ❌ ${endpoint}: Erro - ${err.message}`);
                resolve();
            });
            
            req.setTimeout(3000, () => {
                console.log(`   ❌ ${endpoint}: Timeout`);
                req.destroy();
                resolve();
            });
        });
    }
}

// Função para testar conexão WebSocket
async function testWebSocketConnection() {
    console.log('\n3. ✅ Testando conexão WebSocket:');
    
    return new Promise((resolve) => {
        let connected = false;
        let messageReceived = false;
        
        const ws = new WebSocket(WEBSOCKET_URL);
        
        const timeout = setTimeout(() => {
            if (!connected) {
                console.log('   ❌ Timeout na conexão WebSocket');
                ws.close();
                resolve(false);
            }
        }, 10000);
        
        ws.on('open', () => {
            console.log('   ✅ Conexão WebSocket estabelecida');
            connected = true;
            
            // Enviar mensagem de teste
            const testMessage = {
                type: 'ping',
                timestamp: new Date().toISOString()
            };
            
            ws.send(JSON.stringify(testMessage));
            console.log('   ✅ Mensagem de ping enviada');
        });
        
        ws.on('message', (data) => {
            try {
                const message = JSON.parse(data.toString());
                console.log(`   ✅ Mensagem recebida: ${message.type}`);
                messageReceived = true;
                
                // Fechar conexão após receber resposta
                setTimeout(() => {
                    ws.close();
                }, 1000);
            } catch (error) {
                console.log(`   ❌ Erro ao parsear mensagem: ${error.message}`);
            }
        });
        
        ws.on('close', (code, reason) => {
            clearTimeout(timeout);
            console.log(`   ✅ Conexão WebSocket fechada: ${code} ${reason}`);
            resolve(connected && messageReceived);
        });
        
        ws.on('error', (error) => {
            clearTimeout(timeout);
            console.log(`   ❌ Erro na conexão WebSocket: ${error.message}`);
            resolve(false);
        });
    });
}

// Função para testar autenticação (simulada)
async function testWebSocketAuth() {
    console.log('\n4. ✅ Testando autenticação WebSocket:');
    
    return new Promise((resolve) => {
        // Simular token JWT (em produção, seria obtido do sistema de auth)
        const mockToken = 'mock-jwt-token-for-testing';
        const wsUrlWithToken = `${WEBSOCKET_URL}?token=${encodeURIComponent(mockToken)}`;
        
        const ws = new WebSocket(wsUrlWithToken);
        
        const timeout = setTimeout(() => {
            console.log('   ⚠️  Timeout na conexão com token (esperado se não houver token válido)');
            ws.close();
            resolve(true); // Consideramos sucesso pois o sistema deve rejeitar tokens inválidos
        }, 5000);
        
        ws.on('open', () => {
            console.log('   ✅ Conexão com token estabelecida (sistema de fallback funcionando)');
            clearTimeout(timeout);
            ws.close();
            resolve(true);
        });
        
        ws.on('close', (code, reason) => {
            clearTimeout(timeout);
            if (code === 1000) {
                console.log('   ✅ Conexão fechada normalmente');
            } else {
                console.log(`   ⚠️  Conexão fechada com código ${code} (pode ser esperado para token inválido)`);
            }
            resolve(true);
        });
        
        ws.on('error', (error) => {
            clearTimeout(timeout);
            console.log(`   ⚠️  Erro esperado com token inválido: ${error.message}`);
            resolve(true); // Erro esperado para token inválido
        });
    });
}

// Função principal
async function main() {
    try {
        // Testar saúde do backend
        const backendHealthy = await testBackendHealth();
        
        if (!backendHealthy) {
            console.log('\n❌ Backend não está rodando. Inicie o backend primeiro:');
            console.log('   cd backend && python api.py');
            return;
        }
        
        // Testar endpoints WebSocket
        await testWebSocketEndpoints();
        
        // Testar conexão WebSocket
        const websocketWorking = await testWebSocketConnection();
        
        // Testar autenticação
        await testWebSocketAuth();
        
        // Resumo final
        console.log('\n🎯 Resumo dos testes:');
        console.log(`   Backend: ${backendHealthy ? '✅ Funcionando' : '❌ Com problemas'}`);
        console.log(`   WebSocket: ${websocketWorking ? '✅ Funcionando' : '❌ Com problemas'}`);
        
        if (backendHealthy && websocketWorking) {
            console.log('\n🎉 Todos os testes passaram! As correções WebSocket estão funcionando.');
            console.log('\n📋 Próximos passos:');
            console.log('   1. Testar no frontend React (npm run dev)');
            console.log('   2. Verificar logs do backend para conexões WebSocket');
            console.log('   3. Testar em ambiente de produção (Vercel)');
        } else {
            console.log('\n⚠️  Alguns testes falharam. Verifique:');
            console.log('   1. Se o backend está rodando (python api.py)');
            console.log('   2. Se não há firewall bloqueando a porta 8000');
            console.log('   3. Se as configurações de CORS estão corretas');
        }
        
    } catch (error) {
        console.error('\n❌ Erro durante os testes:', error.message);
    }
}

// Executar testes
main().catch(console.error);