#!/usr/bin/env node
/**
 * Script para analisar e comparar dependências entre renum-frontend e renum-admin
 */

const fs = require('fs');
const path = require('path');

function readPackageJson(projectPath) {
    const packagePath = path.join(projectPath, 'package.json');
    if (!fs.existsSync(packagePath)) {
        throw new Error(`package.json not found at ${packagePath}`);
    }
    return JSON.parse(fs.readFileSync(packagePath, 'utf8'));
}

function compareVersions(version1, version2) {
    // Remove ^ and ~ prefixes for comparison
    const clean1 = version1.replace(/^[\^~]/, '');
    const clean2 = version2.replace(/^[\^~]/, '');
    
    if (clean1 === clean2) return 'same';
    
    const parts1 = clean1.split('.').map(Number);
    const parts2 = clean2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const part1 = parts1[i] || 0;
        const part2 = parts2[i] || 0;
        
        if (part1 > part2) return 'newer';
        if (part1 < part2) return 'older';
    }
    
    return 'same';
}

function analyzeDependencies() {
    console.log('🔍 Analisando Dependências dos Projetos Frontend');
    console.log('=' * 60);
    
    try {
        // Ler package.json dos dois projetos
        const frontendPkg = readPackageJson('renum-frontend');
        const adminPkg = readPackageJson('renum-admin');
        
        console.log(`\n📦 Projetos Analisados:`);
        console.log(`  • renum-frontend v${frontendPkg.version}`);
        console.log(`  • renum-admin v${adminPkg.version}`);
        
        // Analisar dependências principais
        console.log(`\n📋 Análise de Dependências Principais:`);
        analyzeDependencySection(frontendPkg.dependencies, adminPkg.dependencies, 'dependencies');
        
        // Analisar devDependencies
        console.log(`\n🛠️  Análise de DevDependencies:`);
        analyzeDependencySection(frontendPkg.devDependencies, adminPkg.devDependencies, 'devDependencies');
        
        // Gerar recomendações
        console.log(`\n💡 Recomendações de Alinhamento:`);
        generateRecommendations(frontendPkg, adminPkg);
        
    } catch (error) {
        console.error(`❌ Erro: ${error.message}`);
        process.exit(1);
    }
}

function analyzeDependencySection(frontendDeps, adminDeps, sectionName) {
    const allPackages = new Set([
        ...Object.keys(frontendDeps || {}),
        ...Object.keys(adminDeps || {})
    ]);
    
    const differences = [];
    const missing = { frontend: [], admin: [] };
    const versionMismatches = [];
    
    allPackages.forEach(pkg => {
        const frontendVersion = frontendDeps?.[pkg];
        const adminVersion = adminDeps?.[pkg];
        
        if (!frontendVersion && adminVersion) {
            missing.frontend.push({ package: pkg, version: adminVersion });
        } else if (frontendVersion && !adminVersion) {
            missing.admin.push({ package: pkg, version: frontendVersion });
        } else if (frontendVersion && adminVersion) {
            const comparison = compareVersions(frontendVersion, adminVersion);
            if (comparison !== 'same') {
                versionMismatches.push({
                    package: pkg,
                    frontend: frontendVersion,
                    admin: adminVersion,
                    comparison
                });
            }
        }
    });
    
    // Mostrar resultados
    if (missing.frontend.length > 0) {
        console.log(`\n  📦 Pacotes ausentes no renum-frontend:`);
        missing.frontend.forEach(item => {
            console.log(`    - ${item.package}: ${item.version}`);
        });
    }
    
    if (missing.admin.length > 0) {
        console.log(`\n  📦 Pacotes ausentes no renum-admin:`);
        missing.admin.forEach(item => {
            console.log(`    - ${item.package}: ${item.version}`);
        });
    }
    
    if (versionMismatches.length > 0) {
        console.log(`\n  ⚠️  Versões diferentes:`);
        versionMismatches.forEach(item => {
            const icon = item.comparison === 'newer' ? '🔼' : '🔽';
            console.log(`    ${icon} ${item.package}:`);
            console.log(`      • frontend: ${item.frontend}`);
            console.log(`      • admin: ${item.admin}`);
        });
    }
    
    if (missing.frontend.length === 0 && missing.admin.length === 0 && versionMismatches.length === 0) {
        console.log(`  ✅ Todas as dependências estão alinhadas!`);
    }
    
    return { missing, versionMismatches };
}

function generateRecommendations(frontendPkg, adminPkg) {
    const recommendations = [];
    
    // Verificar Next.js
    const frontendNext = frontendPkg.dependencies?.next;
    const adminNext = adminPkg.dependencies?.next;
    
    if (frontendNext && adminNext && frontendNext !== adminNext) {
        recommendations.push({
            priority: 'HIGH',
            category: 'Framework',
            issue: `Next.js versions differ (frontend: ${frontendNext}, admin: ${adminNext})`,
            solution: 'Align both projects to use the same Next.js version'
        });
    }
    
    // Verificar React
    const frontendReact = frontendPkg.dependencies?.react;
    const adminReact = adminPkg.dependencies?.react;
    
    if (frontendReact && adminReact && frontendReact !== adminReact) {
        recommendations.push({
            priority: 'HIGH',
            category: 'Framework',
            issue: `React versions differ (frontend: ${frontendReact}, admin: ${adminReact})`,
            solution: 'Align both projects to use the same React version'
        });
    }
    
    // Verificar TypeScript
    const frontendTS = frontendPkg.devDependencies?.typescript;
    const adminTS = adminPkg.devDependencies?.typescript;
    
    if (frontendTS && adminTS && frontendTS !== adminTS) {
        recommendations.push({
            priority: 'MEDIUM',
            category: 'Development',
            issue: `TypeScript versions differ (frontend: ${frontendTS}, admin: ${adminTS})`,
            solution: 'Align TypeScript versions for consistent development experience'
        });
    }
    
    // Verificar TailwindCSS
    const frontendTailwind = frontendPkg.devDependencies?.tailwindcss;
    const adminTailwind = adminPkg.devDependencies?.tailwindcss;
    
    if (frontendTailwind && adminTailwind && frontendTailwind !== adminTailwind) {
        recommendations.push({
            priority: 'MEDIUM',
            category: 'Styling',
            issue: `TailwindCSS versions differ (frontend: ${frontendTailwind}, admin: ${adminTailwind})`,
            solution: 'Align TailwindCSS versions for consistent styling'
        });
    }
    
    // Verificar pacotes ausentes importantes
    const importantPackages = [
        '@tanstack/react-query',
        'zustand',
        'zod',
        'react-hook-form'
    ];
    
    importantPackages.forEach(pkg => {
        const inFrontend = frontendPkg.dependencies?.[pkg];
        const inAdmin = adminPkg.dependencies?.[pkg];
        
        if (inFrontend && !inAdmin) {
            recommendations.push({
                priority: 'MEDIUM',
                category: 'Missing Package',
                issue: `${pkg} is missing in renum-admin`,
                solution: `Add ${pkg}@${inFrontend} to renum-admin`
            });
        } else if (!inFrontend && inAdmin) {
            recommendations.push({
                priority: 'MEDIUM',
                category: 'Missing Package',
                issue: `${pkg} is missing in renum-frontend`,
                solution: `Add ${pkg}@${inAdmin} to renum-frontend`
            });
        }
    });
    
    // Mostrar recomendações
    if (recommendations.length === 0) {
        console.log('  ✅ Não há recomendações - dependências estão bem alinhadas!');
        return;
    }
    
    recommendations.forEach((rec, index) => {
        const priorityIcon = rec.priority === 'HIGH' ? '🔴' : rec.priority === 'MEDIUM' ? '🟡' : '🟢';
        console.log(`\n  ${index + 1}. ${priorityIcon} [${rec.priority}] ${rec.category}`);
        console.log(`     Problema: ${rec.issue}`);
        console.log(`     Solução: ${rec.solution}`);
    });
    
    // Gerar comandos de alinhamento
    console.log(`\n🔧 Comandos Sugeridos para Alinhamento:`);
    console.log(`\n  Para renum-frontend:`);
    console.log(`  cd renum-frontend`);
    
    // Sugerir atualizações baseadas nas recomendações
    const frontendUpdates = recommendations
        .filter(r => r.solution.includes('renum-frontend') || r.priority === 'HIGH')
        .map(r => r.solution)
        .slice(0, 3);
    
    if (frontendUpdates.length > 0) {
        console.log(`  npm update`);
    }
    
    console.log(`\n  Para renum-admin:`);
    console.log(`  cd renum-admin`);
    
    const adminUpdates = recommendations
        .filter(r => r.solution.includes('renum-admin') || r.priority === 'HIGH')
        .map(r => r.solution)
        .slice(0, 3);
    
    if (adminUpdates.length > 0) {
        console.log(`  npm update`);
    }
}

// Executar análise
if (require.main === module) {
    analyzeDependencies();
}

module.exports = { analyzeDependencies, compareVersions };