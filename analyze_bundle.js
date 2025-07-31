#!/usr/bin/env node

/**
 * Script para analisar bundles dos projetos frontend
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function checkProjectExists(projectPath) {
  return fs.existsSync(path.join(projectPath, 'package.json'));
}

function installBundleAnalyzer(projectPath) {
  console.log(`📦 Instalando @next/bundle-analyzer em ${projectPath}...`);
  
  try {
    execSync('npm install --save-dev @next/bundle-analyzer', {
      cwd: projectPath,
      stdio: 'inherit'
    });
    console.log(colorize('✅ Bundle analyzer instalado com sucesso!', 'green'));
  } catch (error) {
    console.error(colorize('❌ Erro ao instalar bundle analyzer:', 'red'), error.message);
    return false;
  }
  
  return true;
}

function updateNextConfig(projectPath) {
  const configPath = path.join(projectPath, 'next.config.js');
  
  if (!fs.existsSync(configPath)) {
    console.error(colorize(`❌ next.config.js não encontrado em ${projectPath}`, 'red'));
    return false;
  }

  let config = fs.readFileSync(configPath, 'utf8');
  
  // Check if bundle analyzer is already configured
  if (config.includes('bundleAnalyzer')) {
    console.log(colorize('ℹ️  Bundle analyzer já configurado', 'yellow'));
    return true;
  }

  // Add bundle analyzer import
  if (!config.includes('@next/bundle-analyzer')) {
    config = `const withBundleAnalyzer = require('@next/bundle-analyzer')({\n  enabled: process.env.ANALYZE === 'true',\n});\n\n${config}`;
  }

  // Wrap the config export
  config = config.replace(
    'module.exports = nextConfig;',
    'module.exports = withBundleAnalyzer(nextConfig);'
  );

  fs.writeFileSync(configPath, config);
  console.log(colorize('✅ next.config.js atualizado com bundle analyzer', 'green'));
  
  return true;
}

function analyzeBundles(projectPath, projectName) {
  console.log(`\n🔍 Analisando bundles do ${projectName}...`);
  
  try {
    // Build with analysis
    execSync('ANALYZE=true npm run build', {
      cwd: projectPath,
      stdio: 'inherit',
      env: { ...process.env, ANALYZE: 'true' }
    });
    
    console.log(colorize(`✅ Análise do ${projectName} concluída!`, 'green'));
    console.log(colorize('📊 O relatório foi aberto no seu navegador', 'cyan'));
    
  } catch (error) {
    console.error(colorize(`❌ Erro na análise do ${projectName}:`, 'red'), error.message);
    return false;
  }
  
  return true;
}

function generateBuildReport(projectPath, projectName) {
  console.log(`\n📊 Gerando relatório de build para ${projectName}...`);
  
  try {
    // Regular build to get stats
    execSync('npm run build', {
      cwd: projectPath,
      stdio: 'pipe'
    });

    const buildDir = path.join(projectPath, '.next');
    const staticDir = path.join(buildDir, 'static');
    
    if (!fs.existsSync(staticDir)) {
      console.log(colorize('⚠️  Diretório de build não encontrado', 'yellow'));
      return;
    }

    // Analyze build output
    const stats = analyzeBuildOutput(staticDir);
    
    console.log(colorize(`\n📈 Relatório de Build - ${projectName}`, 'cyan'));
    console.log('='.repeat(50));
    console.log(`📦 Total de chunks: ${stats.totalChunks}`);
    console.log(`📏 Tamanho total: ${formatBytes(stats.totalSize)}`);
    console.log(`🎯 Maior chunk: ${stats.largestChunk.name} (${formatBytes(stats.largestChunk.size)})`);
    console.log(`📊 Chunks > 1MB: ${stats.largeChunks}`);
    
    if (stats.recommendations.length > 0) {
      console.log(colorize('\n💡 Recomendações:', 'yellow'));
      stats.recommendations.forEach((rec, i) => {
        console.log(`  ${i + 1}. ${rec}`);
      });
    }
    
  } catch (error) {
    console.error(colorize(`❌ Erro ao gerar relatório do ${projectName}:`, 'red'), error.message);
  }
}

function analyzeBuildOutput(staticDir) {
  const stats = {
    totalChunks: 0,
    totalSize: 0,
    largestChunk: { name: '', size: 0 },
    largeChunks: 0,
    recommendations: []
  };

  function walkDir(dir) {
    const files = fs.readdirSync(dir);
    
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        walkDir(filePath);
      } else if (file.endsWith('.js')) {
        stats.totalChunks++;
        stats.totalSize += stat.size;
        
        if (stat.size > stats.largestChunk.size) {
          stats.largestChunk = { name: file, size: stat.size };
        }
        
        if (stat.size > 1024 * 1024) { // > 1MB
          stats.largeChunks++;
        }
      }
    });
  }

  walkDir(staticDir);

  // Generate recommendations
  if (stats.largestChunk.size > 2 * 1024 * 1024) { // > 2MB
    stats.recommendations.push('Considere dividir o chunk maior usando code splitting');
  }
  
  if (stats.largeChunks > 3) {
    stats.recommendations.push('Muitos chunks grandes - implemente lazy loading');
  }
  
  if (stats.totalSize > 10 * 1024 * 1024) { // > 10MB
    stats.recommendations.push('Bundle total muito grande - otimize dependências');
  }

  return stats;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function main() {
  console.log(colorize('🔍 Análise de Bundle - Projetos Frontend', 'cyan'));
  console.log('='.repeat(60));

  const projects = [
    { path: 'renum-frontend', name: 'Renum Frontend' },
    { path: 'renum-admin', name: 'Renum Admin' }
  ];

  const mode = process.argv[2] || 'report';

  for (const project of projects) {
    if (!checkProjectExists(project.path)) {
      console.log(colorize(`⚠️  Projeto ${project.name} não encontrado`, 'yellow'));
      continue;
    }

    if (mode === 'analyze') {
      // Full analysis with bundle analyzer
      if (installBundleAnalyzer(project.path) && updateNextConfig(project.path)) {
        analyzeBundles(project.path, project.name);
      }
    } else {
      // Quick report
      generateBuildReport(project.path, project.name);
    }
  }

  console.log(colorize('\n✅ Análise concluída!', 'green'));
  
  if (mode === 'report') {
    console.log(colorize('\n💡 Para análise detalhada, execute:', 'cyan'));
    console.log('   node analyze_bundle.js analyze');
  }
}

if (require.main === module) {
  main();
}