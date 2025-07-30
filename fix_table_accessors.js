#!/usr/bin/env node

/**
 * Script para corrigir accessors de string para função nos componentes Table
 */

const fs = require('fs');
const path = require('path');

// Lista de arquivos que precisam ser corrigidos
const filesToFix = [
  'renum-admin/src/pages/users/index.tsx',
  'renum-admin/src/pages/settings/integrations/index.tsx',
  'renum-admin/src/pages/settings/index.tsx',
  'renum-admin/src/pages/homepage/phrases/index.tsx',
  'renum-admin/src/pages/credentials/index.tsx',
  'renum-admin/src/pages/clients/index.tsx',
  'renum-admin/src/pages/billing/limits.tsx',
  'renum-admin/src/pages/billing/invoices/[id].tsx',
  'renum-admin/src/pages/audit/alerts/index.tsx',
  'renum-admin/src/pages/agents/index.tsx',
  'renum-admin/src/components/settings/ChangeLogList.tsx',
  'renum-admin/src/components/billing/InvoicesList.tsx'
];

function fixAccessors(filePath) {
  console.log(`🔧 Corrigindo ${filePath}...`);
  
  if (!fs.existsSync(filePath)) {
    console.log(`❌ Arquivo não encontrado: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  // Padrão para encontrar accessors com strings
  const accessorPattern = /{\s*header:\s*['"`]([^'"`]+)['"`],\s*accessor:\s*['"`]([^'"`]+)['"`]\s*}/g;
  
  content = content.replace(accessorPattern, (match, header, accessor) => {
    console.log(`  ✅ Corrigindo accessor: '${accessor}' -> função`);
    modified = true;
    return `{ header: '${header}', accessor: (row) => row.${accessor} }`;
  });

  if (modified) {
    fs.writeFileSync(filePath, content);
    console.log(`  ✅ ${filePath} corrigido com sucesso!`);
    return true;
  } else {
    console.log(`  ℹ️  Nenhuma correção necessária em ${filePath}`);
    return false;
  }
}

function main() {
  console.log('🔧 Corrigindo Accessors de Tabela');
  console.log('='.repeat(50));

  let totalFixed = 0;

  for (const filePath of filesToFix) {
    if (fixAccessors(filePath)) {
      totalFixed++;
    }
  }

  console.log(`\n📊 Resumo:`);
  console.log(`  • Arquivos processados: ${filesToFix.length}`);
  console.log(`  • Arquivos corrigidos: ${totalFixed}`);
  
  if (totalFixed > 0) {
    console.log(`\n✅ Correções aplicadas com sucesso!`);
    console.log(`   Execute 'npm run build' para verificar se os erros foram resolvidos.`);
  } else {
    console.log(`\n✅ Nenhuma correção necessária.`);
  }
}

if (require.main === module) {
  main();
}