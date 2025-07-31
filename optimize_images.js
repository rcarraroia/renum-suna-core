#!/usr/bin/env node

/**
 * Script para otimizar imagens nos projetos frontend
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function checkImageOptimizationTools() {
  const tools = [
    { name: 'sharp', package: 'sharp' },
    { name: 'imagemin', package: 'imagemin' },
    { name: 'imagemin-mozjpeg', package: 'imagemin-mozjpeg' },
    { name: 'imagemin-pngquant', package: 'imagemin-pngquant' },
    { name: 'imagemin-svgo', package: 'imagemin-svgo' },
    { name: 'imagemin-webp', package: 'imagemin-webp' },
  ];

  console.log(colorize('🔍 Verificando ferramentas de otimização...', 'cyan'));

  const missingTools = [];
  
  for (const tool of tools) {
    try {
      require.resolve(tool.package);
      console.log(colorize(`✅ ${tool.name} encontrado`, 'green'));
    } catch (error) {
      console.log(colorize(`❌ ${tool.name} não encontrado`, 'red'));
      missingTools.push(tool.package);
    }
  }

  if (missingTools.length > 0) {
    console.log(colorize('\n📦 Instalando ferramentas necessárias...', 'yellow'));
    try {
      execSync(`npm install --save-dev ${missingTools.join(' ')}`, { stdio: 'inherit' });
      console.log(colorize('✅ Ferramentas instaladas com sucesso!', 'green'));
    } catch (error) {
      console.error(colorize('❌ Erro ao instalar ferramentas:', 'red'), error.message);
      return false;
    }
  }

  return true;
}

function findImages(dir, extensions = ['.jpg', '.jpeg', '.png', '.svg', '.webp']) {
  const images = [];

  function walkDir(currentDir) {
    const files = fs.readdirSync(currentDir);

    files.forEach(file => {
      const filePath = path.join(currentDir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
        walkDir(filePath);
      } else if (stat.isFile()) {
        const ext = path.extname(file).toLowerCase();
        if (extensions.includes(ext)) {
          images.push({
            path: filePath,
            name: file,
            size: stat.size,
            extension: ext,
          });
        }
      }
    });
  }

  if (fs.existsSync(dir)) {
    walkDir(dir);
  }

  return images;
}

function analyzeImages(projectPath, projectName) {
  console.log(colorize(`\n🔍 Analisando imagens em ${projectName}...`, 'cyan'));

  const publicDir = path.join(projectPath, 'public');
  const srcDir = path.join(projectPath, 'src');

  const publicImages = findImages(publicDir);
  const srcImages = findImages(srcDir);
  const allImages = [...publicImages, ...srcImages];

  if (allImages.length === 0) {
    console.log(colorize('ℹ️  Nenhuma imagem encontrada', 'yellow'));
    return { images: [], stats: null };
  }

  // Analyze image stats
  const stats = {
    total: allImages.length,
    totalSize: allImages.reduce((sum, img) => sum + img.size, 0),
    byExtension: {},
    largeImages: allImages.filter(img => img.size > 500 * 1024), // > 500KB
    recommendations: [],
  };

  // Group by extension
  allImages.forEach(img => {
    const ext = img.extension;
    if (!stats.byExtension[ext]) {
      stats.byExtension[ext] = { count: 0, size: 0 };
    }
    stats.byExtension[ext].count++;
    stats.byExtension[ext].size += img.size;
  });

  // Generate recommendations
  if (stats.largeImages.length > 0) {
    stats.recommendations.push(`${stats.largeImages.length} imagens > 500KB precisam de otimização`);
  }

  const jpgImages = stats.byExtension['.jpg'] || stats.byExtension['.jpeg'];
  if (jpgImages && jpgImages.count > 0) {
    stats.recommendations.push('Considere converter JPEGs para WebP para melhor compressão');
  }

  const pngImages = stats.byExtension['.png'];
  if (pngImages && pngImages.count > 0) {
    stats.recommendations.push('Otimize PNGs com pngquant para reduzir tamanho');
  }

  // Print analysis
  console.log(colorize(`\n📊 Análise de Imagens - ${projectName}`, 'cyan'));
  console.log('='.repeat(50));
  console.log(`📁 Total de imagens: ${stats.total}`);
  console.log(`📏 Tamanho total: ${formatBytes(stats.totalSize)}`);
  console.log(`⚠️  Imagens grandes (>500KB): ${stats.largeImages.length}`);

  console.log(colorize('\n📈 Por extensão:', 'blue'));
  Object.entries(stats.byExtension).forEach(([ext, data]) => {
    console.log(`  ${ext}: ${data.count} arquivos (${formatBytes(data.size)})`);
  });

  if (stats.largeImages.length > 0) {
    console.log(colorize('\n🔍 Imagens que precisam de otimização:', 'yellow'));
    stats.largeImages.slice(0, 5).forEach(img => {
      console.log(`  • ${img.name} (${formatBytes(img.size)})`);
    });
    if (stats.largeImages.length > 5) {
      console.log(`  ... e mais ${stats.largeImages.length - 5} imagens`);
    }
  }

  if (stats.recommendations.length > 0) {
    console.log(colorize('\n💡 Recomendações:', 'yellow'));
    stats.recommendations.forEach((rec, i) => {
      console.log(`  ${i + 1}. ${rec}`);
    });
  }

  return { images: allImages, stats };
}

function optimizeImages(images, outputDir) {
  if (!checkImageOptimizationTools()) {
    return false;
  }

  console.log(colorize(`\n🔧 Otimizando ${images.length} imagens...`, 'cyan'));

  try {
    const imagemin = require('imagemin');
    const imageminMozjpeg = require('imagemin-mozjpeg');
    const imageminPngquant = require('imagemin-pngquant');
    const imageminSvgo = require('imagemin-svgo');
    const imageminWebp = require('imagemin-webp');

    // Create output directory
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Group images by directory for batch processing
    const imagesByDir = {};
    images.forEach(img => {
      const dir = path.dirname(img.path);
      if (!imagesByDir[dir]) {
        imagesByDir[dir] = [];
      }
      imagesByDir[dir].push(img);
    });

    let totalOriginalSize = 0;
    let totalOptimizedSize = 0;

    // Process each directory
    Object.entries(imagesByDir).forEach(async ([dir, dirImages]) => {
      const inputPattern = path.join(dir, '*.{jpg,jpeg,png,svg}');
      const relativeOutputDir = path.join(outputDir, path.relative(process.cwd(), dir));

      try {
        const files = await imagemin([inputPattern], {
          destination: relativeOutputDir,
          plugins: [
            imageminMozjpeg({ quality: 85 }),
            imageminPngquant({ quality: [0.6, 0.8] }),
            imageminSvgo({
              plugins: [
                { name: 'removeViewBox', active: false },
                { name: 'removeDimensions', active: true },
              ],
            }),
          ],
        });

        // Also create WebP versions
        await imagemin([inputPattern], {
          destination: relativeOutputDir,
          plugins: [
            imageminWebp({ quality: 80 }),
          ],
        });

        // Calculate savings
        files.forEach(file => {
          const originalPath = file.sourcePath;
          const originalSize = fs.statSync(originalPath).size;
          const optimizedSize = file.data.length;

          totalOriginalSize += originalSize;
          totalOptimizedSize += optimizedSize;
        });

      } catch (error) {
        console.error(colorize(`❌ Erro ao otimizar imagens em ${dir}:`, 'red'), error.message);
      }
    });

    const savings = totalOriginalSize - totalOptimizedSize;
    const savingsPercent = ((savings / totalOriginalSize) * 100).toFixed(1);

    console.log(colorize('\n✅ Otimização concluída!', 'green'));
    console.log(`📉 Redução de tamanho: ${formatBytes(savings)} (${savingsPercent}%)`);
    console.log(`📁 Imagens otimizadas salvas em: ${outputDir}`);

    return true;

  } catch (error) {
    console.error(colorize('❌ Erro durante otimização:', 'red'), error.message);
    return false;
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function generateOptimizationGuide() {
  const guide = `
# 🖼️ Guia de Otimização de Imagens

## Formatos Recomendados

### WebP
- **Uso**: Imagens gerais (fotos, ilustrações)
- **Vantagem**: 25-35% menor que JPEG/PNG
- **Suporte**: Todos os navegadores modernos

### AVIF
- **Uso**: Imagens de alta qualidade
- **Vantagem**: 50% menor que JPEG
- **Suporte**: Chrome, Firefox (parcial)

### SVG
- **Uso**: Ícones, logos, ilustrações simples
- **Vantagem**: Escalável, pequeno
- **Otimização**: Use SVGO para remover metadados

## Configuração Next.js

\`\`\`javascript
// next.config.js
module.exports = {
  images: {
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
}
\`\`\`

## Componente Otimizado

\`\`\`tsx
import Image from 'next/image';

<Image
  src="/image.jpg"
  alt="Descrição"
  width={800}
  height={600}
  priority={false} // true apenas para imagens above-the-fold
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
\`\`\`

## Ferramentas de Otimização

1. **Sharp** - Processamento rápido de imagens
2. **Imagemin** - Compressão automática
3. **SVGO** - Otimização de SVGs
4. **WebP Converter** - Conversão para WebP

## Boas Práticas

- Use \`priority={true}\` apenas para imagens above-the-fold
- Implemente lazy loading para imagens fora da viewport
- Forneça dimensões explícitas para evitar layout shift
- Use placeholders blur para melhor UX
- Considere responsive images com \`sizes\`
`;

  fs.writeFileSync('IMAGE_OPTIMIZATION_GUIDE.md', guide);
  console.log(colorize('📖 Guia de otimização salvo em IMAGE_OPTIMIZATION_GUIDE.md', 'cyan'));
}

function main() {
  console.log(colorize('🖼️ Otimização de Imagens - Projetos Frontend', 'cyan'));
  console.log('='.repeat(60));

  const projects = [
    { path: 'renum-frontend', name: 'Renum Frontend' },
    { path: 'renum-admin', name: 'Renum Admin' }
  ];

  const mode = process.argv[2] || 'analyze';
  let allImages = [];

  // Analyze all projects
  for (const project of projects) {
    if (!fs.existsSync(project.path)) {
      console.log(colorize(`⚠️  Projeto ${project.name} não encontrado`, 'yellow'));
      continue;
    }

    const { images } = analyzeImages(project.path, project.name);
    allImages = allImages.concat(images);
  }

  if (mode === 'optimize' && allImages.length > 0) {
    const outputDir = 'optimized-images';
    optimizeImages(allImages, outputDir);
  }

  // Generate optimization guide
  generateOptimizationGuide();

  console.log(colorize('\n✅ Análise de imagens concluída!', 'green'));
  
  if (mode === 'analyze' && allImages.length > 0) {
    console.log(colorize('\n💡 Para otimizar as imagens, execute:', 'cyan'));
    console.log('   node optimize_images.js optimize');
  }
}

if (require.main === module) {
  main();
}