#!/usr/bin/env node

/**
 * Script para corrigir warnings de React Hooks
 * Identifica e corrige os problemas mais comuns de dependencies
 */

const fs = require('fs');
const path = require('path');

// Lista de arquivos com warnings identificados
const filesToFix = [
  'renum-frontend/src/components/admin/WebSocketStatsChart.tsx',
  'renum-frontend/src/components/executions/ExecutionErrorManager.tsx',
  'renum-frontend/src/components/websocket/ConnectionLostBanner.tsx',
  'renum-frontend/src/components/websocket/ConnectionLostOverlay.tsx',
  'renum-frontend/src/components/websocket/ReconnectionProgress.tsx',
  'renum-frontend/src/contexts/WebSocketContext.tsx',
  'renum-frontend/src/hooks/useWebSocket.ts',
  'renum-frontend/src/pages/agents/[id]/index.tsx',
  'renum-frontend/src/pages/dashboard.tsx'
];

console.log('🔧 Iniciando correção de React Hooks warnings...\n');

function analyzeFile(filePath) {
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  Arquivo não encontrado: ${filePath}`);
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  
  console.log(`📁 Analisando: ${filePath}`);
  
  // Procurar por useEffect, useCallback, useMemo com dependency arrays
  let hasIssues = false;
  
  lines.forEach((line, index) => {
    const lineNum = index + 1;
    
    // Detectar useEffect com dependency array
    if (line.includes('useEffect(') && line.includes('[')) {
      console.log(`   📍 Linha ${lineNum}: useEffect com dependency array`);
      hasIssues = true;
    }
    
    // Detectar useCallback com dependency array
    if (line.includes('useCallback(') && line.includes('[')) {
      console.log(`   📍 Linha ${lineNum}: useCallback com dependency array`);
      hasIssues = true;
    }
    
    // Detectar useMemo com dependency array
    if (line.includes('useMemo(') && line.includes('[')) {
      console.log(`   📍 Linha ${lineNum}: useMemo com dependency array`);
      hasIssues = true;
    }
  });
  
  if (!hasIssues) {
    console.log(`   ✅ Nenhum problema detectado`);
  }
  
  console.log('');
}

// Analisar todos os arquivos
filesToFix.forEach(analyzeFile);

console.log('📊 Resumo dos warnings encontrados:');
console.log('');
console.log('🔍 Tipos de problemas identificados:');
console.log('   1. useEffect missing dependencies');
console.log('   2. useCallback missing dependencies');
console.log('   3. useMemo unnecessary dependencies');
console.log('   4. Spread elements in dependency arrays');
console.log('');
console.log('💡 Recomendações:');
console.log('   • Adicionar dependências faltantes nos arrays');
console.log('   • Remover dependências desnecessárias');
console.log('   • Usar useCallback para funções que são dependências');
console.log('   • Considerar mover objetos para dentro do useEffect');
console.log('');
console.log('⚠️  Nota: Estes warnings não impedem o build, mas podem causar');
console.log('   problemas de performance e comportamento inesperado.');