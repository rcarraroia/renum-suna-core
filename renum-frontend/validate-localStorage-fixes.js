#!/usr/bin/env node

/**
 * Script de validação para verificar se todos os usos de localStorage
 * foram corrigidos para serem compatíveis com SSR/SSG do Next.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Validando correções de localStorage para compatibilidade SSR/SSG...\n');

// Diretórios a serem verificados
const srcDir = path.join(__dirname, 'src');

// Função para buscar arquivos recursivamente
function findFiles(dir, extension) {
  const files = [];
  
  function searchDir(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        // Pular diretórios de build e node_modules
        if (!item.startsWith('.') && item !== 'node_modules' && item !== '.next') {
          searchDir(fullPath);
        }
      } else if (item.endsWith(extension)) {
        files.push(fullPath);
      }
    }
  }
  
  searchDir(dir);
  return files;
}

// Buscar todos os arquivos TypeScript e JavaScript
const files = [
  ...findFiles(srcDir, '.ts'),
  ...findFiles(srcDir, '.tsx'),
  ...findFiles(srcDir, '.js'),
  ...findFiles(srcDir, '.jsx')
];

console.log(`📁 Verificando ${files.length} arquivos...\n`);

let issuesFound = 0;
const issues = [];

// Padrões problemáticos
const problematicPatterns = [
  {
    pattern: /localStorage\./g,
    description: 'Uso direto de localStorage sem verificação de SSR',
    severity: 'HIGH',
    exclude: [
      // Excluir o arquivo LocalStorageManager que é nossa solução
      'utils/localStorage.ts',
      // Excluir arquivos de build
      '.next/',
      'node_modules/'
    ]
  },
  {
    pattern: /sessionStorage\./g,
    description: 'Uso direto de sessionStorage sem verificação de SSR',
    severity: 'MEDIUM',
    exclude: [
      '.next/',
      'node_modules/'
    ]
  },
  {
    pattern: /window\./g,
    description: 'Uso direto de window sem verificação de SSR',
    severity: 'LOW',
    exclude: [
      '.next/',
      'node_modules/'
    ]
  }
];

// Verificar cada arquivo
for (const filePath of files) {
  const relativePath = path.relative(__dirname, filePath);
  
  // Pular arquivos excluídos
  if (relativePath.includes('.next/') || relativePath.includes('node_modules/')) {
    continue;
  }
  
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    for (const { pattern, description, severity, exclude } of problematicPatterns) {
      // Verificar se o arquivo deve ser excluído para este padrão
      const shouldExclude = exclude.some(excludePath => relativePath.includes(excludePath));
      if (shouldExclude) continue;
      
      const matches = content.match(pattern);
      if (matches) {
        // Para localStorage, verificar se há verificação de window
        if (pattern.source.includes('localStorage')) {
          // Verificar se há verificação de typeof window !== 'undefined'
          const hasWindowCheck = content.includes("typeof window !== 'undefined'") || 
                                content.includes('LocalStorageManager') ||
                                content.includes('if (isBrowser)');
          
          if (!hasWindowCheck) {
            issues.push({
              file: relativePath,
              pattern: pattern.source,
              description,
              severity,
              matches: matches.length,
              lines: getLineNumbers(content, pattern)
            });
            issuesFound++;
          }
        } else {
          // Para outros padrões, reportar sempre
          issues.push({
            file: relativePath,
            pattern: pattern.source,
            description,
            severity,
            matches: matches.length,
            lines: getLineNumbers(content, pattern)
          });
          issuesFound++;
        }
      }
    }
  } catch (error) {
    console.error(`❌ Erro ao ler arquivo ${relativePath}:`, error.message);
  }
}

// Função para obter números de linha das ocorrências
function getLineNumbers(content, pattern) {
  const lines = content.split('\n');
  const lineNumbers = [];
  
  lines.forEach((line, index) => {
    if (pattern.test(line)) {
      lineNumbers.push(index + 1);
    }
  });
  
  return lineNumbers;
}

// Relatório de resultados
console.log('📊 RELATÓRIO DE VALIDAÇÃO\n');
console.log('=' .repeat(50));

if (issuesFound === 0) {
  console.log('✅ SUCESSO: Nenhum problema encontrado!');
  console.log('🎉 Todos os usos de localStorage foram corrigidos para compatibilidade SSR/SSG.');
} else {
  console.log(`❌ PROBLEMAS ENCONTRADOS: ${issuesFound}`);
  console.log('\nDetalhes dos problemas:\n');
  
  // Agrupar por severidade
  const groupedIssues = {
    HIGH: issues.filter(i => i.severity === 'HIGH'),
    MEDIUM: issues.filter(i => i.severity === 'MEDIUM'),
    LOW: issues.filter(i => i.severity === 'LOW')
  };
  
  for (const [severity, severityIssues] of Object.entries(groupedIssues)) {
    if (severityIssues.length === 0) continue;
    
    const icon = severity === 'HIGH' ? '🚨' : severity === 'MEDIUM' ? '⚠️' : 'ℹ️';
    console.log(`${icon} ${severity} PRIORITY (${severityIssues.length} issues):`);
    
    for (const issue of severityIssues) {
      console.log(`  📄 ${issue.file}`);
      console.log(`     ${issue.description}`);
      console.log(`     Padrão: ${issue.pattern}`);
      console.log(`     Ocorrências: ${issue.matches} (linhas: ${issue.lines.join(', ')})`);
      console.log('');
    }
  }
  
  console.log('🔧 RECOMENDAÇÕES:');
  console.log('1. Substitua usos diretos de localStorage por LocalStorageManager');
  console.log('2. Adicione verificações typeof window !== "undefined" onde necessário');
  console.log('3. Use useEffect para operações que dependem do lado do cliente');
  console.log('4. Considere usar bibliotecas como next-themes para temas');
}

console.log('\n' + '='.repeat(50));

// Verificar se o build do Next.js funciona
console.log('\n🏗️  Testando build do Next.js...');

try {
  // Tentar fazer build
  execSync('npm run build', { 
    stdio: 'pipe',
    cwd: __dirname,
    timeout: 120000 // 2 minutos timeout
  });
  console.log('✅ Build do Next.js executado com sucesso!');
} catch (error) {
  console.log('❌ Build do Next.js falhou:');
  console.log(error.stdout?.toString() || '');
  console.log(error.stderr?.toString() || '');
  issuesFound++;
}

// Exit code
process.exit(issuesFound > 0 ? 1 : 0);