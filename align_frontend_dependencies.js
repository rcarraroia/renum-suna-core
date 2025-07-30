#!/usr/bin/env node

/**
 * Script para alinhar dependências entre renum-frontend e renum-admin
 */

const fs = require('fs');
const path = require('path');

// Cores para output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function loadPackageJson(projectPath) {
  const packagePath = path.join(projectPath, 'package.json');
  if (!fs.existsSync(packagePath)) {
    throw new Error(`package.json não encontrado em ${projectPath}`);
  }
  return JSON.parse(fs.readFileSync(packagePath, 'utf8'));
}

function savePackageJson(projectPath, packageData) {
  const packagePath = path.join(projectPath, 'package.json');
  fs.writeFileSync(packagePath, JSON.stringify(packageData, null, 2) + '\n');
}

function compareVersions(v1, v2) {
  // Remove prefixos como ^, ~, etc.
  const clean1 = v1.replace(/^[\^~>=<]/, '');
  const clean2 = v2.replace(/^[\^~>=<]/, '');
  
  const parts1 = clean1.split('.').map(Number);
  const parts2 = clean2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;
    
    if (part1 > part2) return 1;
    if (part1 < part2) return -1;
  }
  
  return 0;
}

function getLatestVersion(v1, v2) {
  const comparison = compareVersions(v1, v2);
  return comparison >= 0 ? v1 : v2;
}

function analyzeDependencies() {
  console.log(colorize('🔍 Analisando Dependências dos Projetos Frontend', 'cyan'));
  console.log('='.repeat(60));

  // Carregar package.json dos dois projetos
  const frontendPkg = loadPackageJson('renum-frontend');
  const adminPkg = loadPackageJson('renum-admin');

  console.log(colorize('\n📦 Projetos Analisados:', 'blue'));
  console.log(`  • renum-frontend v${frontendPkg.version}`);
  console.log(`  • renum-admin v${adminPkg.version}`);

  // Analisar dependencies
  const frontendDeps = frontendPkg.dependencies || {};
  const adminDeps = adminPkg.dependencies || {};
  
  // Analisar devDependencies
  const frontendDevDeps = frontendPkg.devDependencies || {};
  const adminDevDeps = adminPkg.devDependencies || {};

  const analysis = {
    dependencies: {
      conflicts: {},
      missingInFrontend: {},
      missingInAdmin: {},
      aligned: {}
    },
    devDependencies: {
      conflicts: {},
      missingInFrontend: {},
      missingInAdmin: {},
      aligned: {}
    }
  };

  // Analisar dependencies principais
  const allDeps = new Set([...Object.keys(frontendDeps), ...Object.keys(adminDeps)]);
  
  for (const dep of allDeps) {
    const frontendVersion = frontendDeps[dep];
    const adminVersion = adminDeps[dep];

    if (frontendVersion && adminVersion) {
      if (frontendVersion !== adminVersion) {
        analysis.dependencies.conflicts[dep] = {
          frontend: frontendVersion,
          admin: adminVersion,
          recommended: getLatestVersion(frontendVersion, adminVersion)
        };
      } else {
        analysis.dependencies.aligned[dep] = frontendVersion;
      }
    } else if (frontendVersion && !adminVersion) {
      analysis.dependencies.missingInAdmin[dep] = frontendVersion;
    } else if (!frontendVersion && adminVersion) {
      analysis.dependencies.missingInFrontend[dep] = adminVersion;
    }
  }

  // Analisar devDependencies
  const allDevDeps = new Set([...Object.keys(frontendDevDeps), ...Object.keys(adminDevDeps)]);
  
  for (const dep of allDevDeps) {
    const frontendVersion = frontendDevDeps[dep];
    const adminVersion = adminDevDeps[dep];

    if (frontendVersion && adminVersion) {
      if (frontendVersion !== adminVersion) {
        analysis.devDependencies.conflicts[dep] = {
          frontend: frontendVersion,
          admin: adminVersion,
          recommended: getLatestVersion(frontendVersion, adminVersion)
        };
      } else {
        analysis.devDependencies.aligned[dep] = frontendVersion;
      }
    } else if (frontendVersion && !adminVersion) {
      analysis.devDependencies.missingInAdmin[dep] = frontendVersion;
    } else if (!frontendVersion && adminVersion) {
      analysis.devDependencies.missingInFrontend[dep] = adminVersion;
    }
  }

  return { analysis, frontendPkg, adminPkg };
}

function printAnalysis(analysis) {
  console.log(colorize('\n📋 Análise de Dependencies:', 'yellow'));
  
  // Conflitos em dependencies
  if (Object.keys(analysis.dependencies.conflicts).length > 0) {
    console.log(colorize('\n  ⚠️  Conflitos de Versão:', 'red'));
    for (const [dep, versions] of Object.entries(analysis.dependencies.conflicts)) {
      console.log(`    🔼 ${dep}:`);
      console.log(`      • frontend: ${versions.frontend}`);
      console.log(`      • admin: ${versions.admin}`);
      console.log(`      • recomendado: ${colorize(versions.recommended, 'green')}`);
    }
  }

  // Pacotes ausentes
  if (Object.keys(analysis.dependencies.missingInAdmin).length > 0) {
    console.log(colorize('\n  📦 Pacotes ausentes no renum-admin:', 'yellow'));
    for (const [dep, version] of Object.entries(analysis.dependencies.missingInAdmin)) {
      console.log(`    - ${dep}: ${version}`);
    }
  }

  if (Object.keys(analysis.dependencies.missingInFrontend).length > 0) {
    console.log(colorize('\n  📦 Pacotes ausentes no renum-frontend:', 'yellow'));
    for (const [dep, version] of Object.entries(analysis.dependencies.missingInFrontend)) {
      console.log(`    - ${dep}: ${version}`);
    }
  }

  // DevDependencies
  console.log(colorize('\n🛠️  Análise de DevDependencies:', 'yellow'));
  
  if (Object.keys(analysis.devDependencies.conflicts).length > 0) {
    console.log(colorize('\n  ⚠️  Conflitos de Versão:', 'red'));
    for (const [dep, versions] of Object.entries(analysis.devDependencies.conflicts)) {
      console.log(`    🔼 ${dep}:`);
      console.log(`      • frontend: ${versions.frontend}`);
      console.log(`      • admin: ${versions.admin}`);
      console.log(`      • recomendado: ${colorize(versions.recommended, 'green')}`);
    }
  }

  if (Object.keys(analysis.devDependencies.missingInAdmin).length > 0) {
    console.log(colorize('\n  📦 Pacotes ausentes no renum-admin:', 'yellow'));
    for (const [dep, version] of Object.entries(analysis.devDependencies.missingInAdmin)) {
      console.log(`    - ${dep}: ${version}`);
    }
  }

  if (Object.keys(analysis.devDependencies.missingInFrontend).length > 0) {
    console.log(colorize('\n  📦 Pacotes ausentes no renum-frontend:', 'yellow'));
    for (const [dep, version] of Object.entries(analysis.devDependencies.missingInFrontend)) {
      console.log(`    - ${dep}: ${version}`);
    }
  }

  // Estatísticas
  const totalConflicts = Object.keys(analysis.dependencies.conflicts).length + 
                        Object.keys(analysis.devDependencies.conflicts).length;
  const totalMissing = Object.keys(analysis.dependencies.missingInAdmin).length + 
                      Object.keys(analysis.dependencies.missingInFrontend).length +
                      Object.keys(analysis.devDependencies.missingInAdmin).length + 
                      Object.keys(analysis.devDependencies.missingInFrontend).length;

  console.log(colorize('\n📊 Resumo:', 'cyan'));
  console.log(`  • Conflitos de versão: ${colorize(totalConflicts, totalConflicts > 0 ? 'red' : 'green')}`);
  console.log(`  • Pacotes ausentes: ${colorize(totalMissing, totalMissing > 0 ? 'yellow' : 'green')}`);
}

function generateAlignmentPlan(analysis) {
  const plan = {
    frontend: {
      dependencies: {},
      devDependencies: {}
    },
    admin: {
      dependencies: {},
      devDependencies: {}
    }
  };

  // Resolver conflitos em dependencies
  for (const [dep, versions] of Object.entries(analysis.dependencies.conflicts)) {
    plan.frontend.dependencies[dep] = versions.recommended;
    plan.admin.dependencies[dep] = versions.recommended;
  }

  // Adicionar pacotes ausentes em dependencies
  for (const [dep, version] of Object.entries(analysis.dependencies.missingInAdmin)) {
    // Apenas adicionar pacotes essenciais ao admin
    const essentialPackages = [
      '@radix-ui/react-label',
      '@radix-ui/react-select', 
      '@radix-ui/react-slot',
      '@radix-ui/react-toast',
      'uuid'
    ];
    
    if (essentialPackages.includes(dep)) {
      plan.admin.dependencies[dep] = version;
    }
  }

  for (const [dep, version] of Object.entries(analysis.dependencies.missingInFrontend)) {
    // Adicionar recharts ao frontend se necessário
    if (dep === 'recharts') {
      plan.frontend.dependencies[dep] = version;
    }
  }

  // Resolver conflitos em devDependencies
  for (const [dep, versions] of Object.entries(analysis.devDependencies.conflicts)) {
    plan.frontend.devDependencies[dep] = versions.recommended;
    plan.admin.devDependencies[dep] = versions.recommended;
  }

  // Adicionar devDependencies essenciais ausentes
  const essentialDevDeps = [
    '@testing-library/jest-dom',
    '@testing-library/react',
    '@testing-library/user-event',
    '@types/jest',
    '@types/uuid',
    'jest',
    'jest-environment-jsdom'
  ];

  for (const [dep, version] of Object.entries(analysis.devDependencies.missingInAdmin)) {
    if (essentialDevDeps.includes(dep)) {
      plan.admin.devDependencies[dep] = version;
    }
  }

  return plan;
}

function applyAlignmentPlan(plan, frontendPkg, adminPkg) {
  console.log(colorize('\n🔧 Aplicando Plano de Alinhamento:', 'green'));

  let changes = false;

  // Aplicar mudanças no frontend
  if (Object.keys(plan.frontend.dependencies).length > 0 || 
      Object.keys(plan.frontend.devDependencies).length > 0) {
    
    console.log(colorize('\n  📦 Atualizando renum-frontend:', 'blue'));
    
    for (const [dep, version] of Object.entries(plan.frontend.dependencies)) {
      frontendPkg.dependencies[dep] = version;
      console.log(`    ✅ ${dep}: ${version}`);
      changes = true;
    }
    
    for (const [dep, version] of Object.entries(plan.frontend.devDependencies)) {
      frontendPkg.devDependencies[dep] = version;
      console.log(`    🛠️  ${dep}: ${version}`);
      changes = true;
    }
  }

  // Aplicar mudanças no admin
  if (Object.keys(plan.admin.dependencies).length > 0 || 
      Object.keys(plan.admin.devDependencies).length > 0) {
    
    console.log(colorize('\n  📦 Atualizando renum-admin:', 'blue'));
    
    for (const [dep, version] of Object.entries(plan.admin.dependencies)) {
      adminPkg.dependencies[dep] = version;
      console.log(`    ✅ ${dep}: ${version}`);
      changes = true;
    }
    
    for (const [dep, version] of Object.entries(plan.admin.devDependencies)) {
      if (!adminPkg.devDependencies) {
        adminPkg.devDependencies = {};
      }
      adminPkg.devDependencies[dep] = version;
      console.log(`    🛠️  ${dep}: ${version}`);
      changes = true;
    }
  }

  if (changes) {
    // Salvar arquivos atualizados
    savePackageJson('renum-frontend', frontendPkg);
    savePackageJson('renum-admin', adminPkg);
    
    console.log(colorize('\n✅ Arquivos package.json atualizados com sucesso!', 'green'));
    
    console.log(colorize('\n📋 Próximos passos:', 'cyan'));
    console.log('  1. Execute npm install em ambos os projetos:');
    console.log('     cd renum-frontend && npm install');
    console.log('     cd renum-admin && npm install');
    console.log('  2. Teste os builds:');
    console.log('     npm run build');
    console.log('  3. Execute os testes se disponíveis:');
    console.log('     npm test');
  } else {
    console.log(colorize('\n✅ Nenhuma mudança necessária - dependências já alinhadas!', 'green'));
  }

  return changes;
}

function main() {
  try {
    const { analysis, frontendPkg, adminPkg } = analyzeDependencies();
    printAnalysis(analysis);
    
    const plan = generateAlignmentPlan(analysis);
    const hasChanges = applyAlignmentPlan(plan, frontendPkg, adminPkg);
    
    if (hasChanges) {
      console.log(colorize('\n🎉 Alinhamento de dependências concluído!', 'green'));
    }
    
  } catch (error) {
    console.error(colorize(`❌ Erro: ${error.message}`, 'red'));
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { analyzeDependencies, generateAlignmentPlan, applyAlignmentPlan };