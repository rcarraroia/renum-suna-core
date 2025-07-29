/**
 * Script de validação para verificar se a correção da URL do WebSocket foi aplicada corretamente
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validando correção da URL do WebSocket...\n');

// Arquivos que devem usar a variável de ambiente
const filesToCheck = [
  'src/constants/websocket.ts',
  'src/hooks/useWebSocket.ts'
];

let allValid = true;

filesToCheck.forEach(filePath => {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`❌ Arquivo não encontrado: ${filePath}`);
    allValid = false;
    return;
  }

  const content = fs.readFileSync(fullPath, 'utf8');
  
  // Verifica se usa a variável de ambiente
  const hasEnvVar = content.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL');
  
  // Verifica se ainda tem URL hardcoded sem fallback
  const hasHardcodedUrl = content.includes("'ws://localhost:8000/ws'") && 
                         !content.includes('process.env.NEXT_PUBLIC_WEBSOCKET_URL ||');

  console.log(`📁 ${filePath}:`);
  
  if (hasEnvVar && !hasHardcodedUrl) {
    console.log('  ✅ Usa variável de ambiente NEXT_PUBLIC_WEBSOCKET_URL');
    console.log('  ✅ Tem fallback para desenvolvimento');
  } else if (hasHardcodedUrl) {
    console.log('  ❌ Ainda contém URL hardcoded sem usar variável de ambiente');
    allValid = false;
  } else {
    console.log('  ⚠️  Configuração não encontrada ou formato inesperado');
    allValid = false;
  }
  
  console.log('');
});

// Verifica se a variável de ambiente está documentada
const envExamplePath = path.join(__dirname, '.env.development');
if (fs.existsSync(envExamplePath)) {
  const envContent = fs.readFileSync(envExamplePath, 'utf8');
  if (envContent.includes('NEXT_PUBLIC_WEBSOCKET_URL')) {
    console.log('✅ Variável NEXT_PUBLIC_WEBSOCKET_URL documentada em .env.development');
  } else {
    console.log('⚠️  Variável NEXT_PUBLIC_WEBSOCKET_URL não encontrada em .env.development');
  }
} else {
  console.log('⚠️  Arquivo .env.development não encontrado');
}

console.log('\n' + '='.repeat(50));

if (allValid) {
  console.log('🎉 Correção da URL do WebSocket aplicada com sucesso!');
  console.log('');
  console.log('📋 Resumo da correção:');
  console.log('• URLs hardcoded substituídas por variável de ambiente');
  console.log('• Fallback para localhost mantido para desenvolvimento');
  console.log('• Configuração agora usa NEXT_PUBLIC_WEBSOCKET_URL em produção');
  console.log('');
  console.log('🚀 Próximos passos:');
  console.log('1. Fazer commit das alterações');
  console.log('2. Fazer deploy no Vercel');
  console.log('3. Verificar se a variável NEXT_PUBLIC_WEBSOCKET_URL está configurada no Vercel');
  process.exit(0);
} else {
  console.log('❌ Algumas verificações falharam. Revise os arquivos acima.');
  process.exit(1);
}