#!/usr/bin/env node

/**
 * Script de validação de build local
 * Simula o processo de build do Vercel para detectar erros antes do deploy
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Iniciando validação de build local...\n');

// Função para executar comandos e capturar output
function runCommand(command, description) {
  console.log(`📋 ${description}...`);
  try {
    const output = execSync(command, { 
      encoding: 'utf8', 
      stdio: 'pipe',
      cwd: process.cwd()
    });
    console.log(`✅ ${description} - Sucesso\n`);
    return { success: true, output };
  } catch (error) {
    console.error(`❌ ${description} - Falhou`);
    console.error(`Erro: ${error.message}`);
    console.error(`Output: ${error.stdout || error.stderr}\n`);
    return { success: false, error: error.message, output: error.stdout || error.stderr };
  }
}

// Função para limpar cache
function cleanCache() {
  console.log('🧹 Limpando cache...');
  
  const pathsToClean = [
    '.next',
    'node_modules/.cache',
    '.eslintcache'
  ];
  
  pathsToClean.forEach(pathToClean => {
    if (fs.existsSync(pathToClean)) {
      try {
        if (process.platform === 'win32') {
          execSync(`rmdir /s /q "${pathToClean}"`, { stdio: 'ignore' });
        } else {
          execSync(`rm -rf "${pathToClean}"`, { stdio: 'ignore' });
        }
        console.log(`  ✅ Removido: ${pathToClean}`);
      } catch (error) {
        console.log(`  ⚠️  Não foi possível remover: ${pathToClean}`);
      }
    }
  });
  
  console.log('✅ Cache limpo\n');
}

// Função principal
async function validateBuild() {
  const startTime = Date.now();
  let hasErrors = false;
  
  try {
    // 1. Limpar cache
    cleanCache();
    
    // 2. Verificar se package.json existe
    if (!fs.existsSync('package.json')) {
      console.error('❌ package.json não encontrado!');
      process.exit(1);
    }
    
    // 3. Instalar dependências
    const installResult = runCommand('npm ci', 'Instalando dependências');
    if (!installResult.success) {
      hasErrors = true;
    }
    
    // 4. Verificar tipos TypeScript
    const typeCheckResult = runCommand('npx tsc --noEmit', 'Verificando tipos TypeScript');
    if (!typeCheckResult.success) {
      hasErrors = true;
    }
    
    // 5. Executar linting
    const lintResult = runCommand('npm run lint', 'Executando ESLint');
    if (!lintResult.success) {
      hasErrors = true;
    }
    
    // 6. Build de produção
    const buildResult = runCommand('npm run build', 'Executando build de produção');
    if (!buildResult.success) {
      hasErrors = true;
    }
    
    // 7. Verificar se os arquivos de build foram criados
    if (fs.existsSync('.next')) {
      console.log('✅ Arquivos de build criados com sucesso');
    } else {
      console.error('❌ Arquivos de build não foram criados');
      hasErrors = true;
    }
    
    // Resumo final
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    console.log('\n' + '='.repeat(50));
    console.log('📊 RESUMO DA VALIDAÇÃO');
    console.log('='.repeat(50));
    console.log(`⏱️  Tempo total: ${duration}s`);
    
    if (hasErrors) {
      console.log('❌ Build falhou - Erros encontrados');
      console.log('\n💡 Dicas:');
      console.log('  • Corrija os erros TypeScript mostrados acima');
      console.log('  • Verifique os avisos do ESLint');
      console.log('  • Execute este script novamente após as correções');
      process.exit(1);
    } else {
      console.log('✅ Build bem-sucedido - Pronto para deploy!');
      console.log('\n🚀 Próximos passos:');
      console.log('  • Faça commit das suas alterações');
      console.log('  • Faça push para o repositório');
      console.log('  • O deploy no Vercel deve funcionar sem problemas');
      process.exit(0);
    }
    
  } catch (error) {
    console.error('\n❌ Erro inesperado durante a validação:');
    console.error(error.message);
    process.exit(1);
  }
}

// Executar validação
validateBuild();