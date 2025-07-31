#!/usr/bin/env node

/**
 * Script para adicionar tipos aos accessors das tabelas
 */

const fs = require('fs');
const path = require('path');

// Mapeamento de arquivos para seus tipos principais
const fileTypeMapping = {
  'renum-admin/src/pages/users/index.tsx': 'User',
  'renum-admin/src/pages/settings/integrations/index.tsx': 'IntegrationSetting',
  'renum-admin/src/pages/settings/index.tsx': 'SystemSetting',
  'renum-admin/src/pages/homepage/phrases/index.tsx': 'HomepagePhrase',
  'renum-admin/src/pages/credentials/index.tsx': 'Credential',
  'renum-admin/src/pages/clients/index.tsx': 'Client',
  'renum-admin/src/pages/billing/limits.tsx': 'UsageLimit',
  'renum-admin/src/pages/billing/invoices/[id].tsx': 'InvoiceItem',
  'renum-admin/src/pages/audit/alerts/index.tsx': 'AuditAlert',
  'renum-admin/src/pages/agents/index.tsx': 'Agent',
  'renum-admin/src/components/settings/ChangeLogList.tsx': 'ChangeLog',
  'renum-admin/src/components/billing/InvoicesList.tsx': 'Invoice'
};

function fixTypes(filePath) {
  console.log(`🔧 Corrigindo tipos em ${filePath}...`);
  
  if (!fs.existsSync(filePath)) {
    console.log(`❌ Arquivo não encontrado: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  const expectedType = fileTypeMapping[filePath];
  if (!expectedType) {
    console.log(`  ⚠️  Tipo não mapeado para ${filePath}`);
    return false;
  }

  // Padrão para encontrar accessors sem tipo
  const accessorPattern = /accessor:\s*\(row\)\s*=>/g;
  
  content = content.replace(accessorPattern, (match) => {
    console.log(`  ✅ Adicionando tipo ${expectedType} ao accessor`);
    modified = true;
    return `accessor: (row: ${expectedType}) =>`;
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
  console.log('🔧 Corrigindo Tipos de Accessors');
  console.log('='.repeat(50));

  let totalFixed = 0;
  const filesToFix = Object.keys(fileTypeMapping);

  for (const filePath of filesToFix) {
    if (fixTypes(filePath)) {
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