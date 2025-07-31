#!/usr/bin/env node

/**
 * Script para adicionar imports de tipos necessários
 */

const fs = require('fs');
const path = require('path');

// Mapeamento de arquivos para imports necessários
const importMappings = {
  'renum-admin/src/pages/users/index.tsx': "import { User } from '../../types/user';",
  'renum-admin/src/pages/settings/integrations/index.tsx': "import { IntegrationSetting } from '../../types/settings';",
  'renum-admin/src/pages/settings/index.tsx': "import { SystemSetting } from '../../types/settings';",
  'renum-admin/src/pages/homepage/phrases/index.tsx': "import { HomepagePhrase } from '../../types/homepage';",
  'renum-admin/src/pages/credentials/index.tsx': "import { Credential } from '../../types/credential';",
  'renum-admin/src/pages/clients/index.tsx': "import { Client } from '../../types/client';",
  'renum-admin/src/pages/billing/limits.tsx': "import { UsageLimit } from '../../types/billing';",
  'renum-admin/src/pages/billing/invoices/[id].tsx': "import { InvoiceItem } from '../../types/billing';",
  'renum-admin/src/pages/audit/alerts/index.tsx': "import { AuditAlert } from '../../types/audit';",
  'renum-admin/src/components/settings/ChangeLogList.tsx': "import { ChangeLog } from '../../types/settings';"
};

function addImport(filePath, importStatement) {
  console.log(`🔧 Adicionando import em ${filePath}...`);
  
  if (!fs.existsSync(filePath)) {
    console.log(`❌ Arquivo não encontrado: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf8');
  
  // Verificar se o import já existe
  if (content.includes(importStatement)) {
    console.log(`  ℹ️  Import já existe em ${filePath}`);
    return false;
  }

  // Encontrar a posição para inserir o import (após os outros imports)
  const lines = content.split('\n');
  let insertIndex = 0;
  
  // Encontrar a última linha de import
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith('import ')) {
      insertIndex = i + 1;
    } else if (lines[i].trim() === '' && insertIndex > 0) {
      // Linha vazia após imports
      break;
    }
  }

  // Inserir o import
  lines.splice(insertIndex, 0, importStatement);
  
  const newContent = lines.join('\n');
  fs.writeFileSync(filePath, newContent);
  
  console.log(`  ✅ Import adicionado com sucesso!`);
  return true;
}

function main() {
  console.log('🔧 Adicionando Imports Necessários');
  console.log('='.repeat(50));

  let totalFixed = 0;
  const filesToFix = Object.keys(importMappings);

  for (const filePath of filesToFix) {
    const importStatement = importMappings[filePath];
    if (addImport(filePath, importStatement)) {
      totalFixed++;
    }
  }

  console.log(`\n📊 Resumo:`);
  console.log(`  • Arquivos processados: ${filesToFix.length}`);
  console.log(`  • Arquivos corrigidos: ${totalFixed}`);
  
  if (totalFixed > 0) {
    console.log(`\n✅ Imports adicionados com sucesso!`);
    console.log(`   Execute 'npm run build' para verificar se os erros foram resolvidos.`);
  } else {
    console.log(`\n✅ Nenhuma correção necessária.`);
  }
}

if (require.main === module) {
  main();
}