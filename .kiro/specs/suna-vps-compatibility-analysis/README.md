# Análise de Compatibilidade Suna VPS

Este diretório contém scripts e ferramentas para analisar a compatibilidade entre o ambiente Suna na VPS e o backend Renum.

## Estrutura de Diretórios

```
suna-vps-compatibility-analysis/
├── reports/              # Relatórios gerados pelos scripts
├── scripts/              # Scripts de análise
│   ├── analyze_environment_variables.py    # Análise básica de variáveis de ambiente
│   ├── validate_env_variables.py           # Validação detalhada de variáveis
│   ├── compare_env_files.py                # Comparação entre .env e contêineres
│   └── run_env_analysis.py                 # Script principal para executar todas as análises
├── design.md             # Documento de design da análise
├── requirements.md       # Requisitos da análise
├── tasks.md              # Tarefas de implementação
└── README.md             # Este arquivo
```

## Scripts de Análise de Variáveis de Ambiente

### 1. Análise Básica de Variáveis de Ambiente

Este script extrai as variáveis de ambiente dos contêineres Renum e Suna e verifica a presença das variáveis necessárias.

```bash
python scripts/analyze_environment_variables.py
```

### 2. Validação Detalhada de Variáveis

Este script realiza uma validação mais detalhada das variáveis de ambiente, verificando formatos e valores.

```bash
python scripts/validate_env_variables.py
```

### 3. Comparação entre Arquivos .env e Contêineres

Este script compara as variáveis definidas nos arquivos .env com as presentes nos contêineres em execução.

```bash
python scripts/compare_env_files.py
```

### 4. Execução Completa da Análise

Este script executa todos os scripts de análise e gera um relatório consolidado.

```bash
python scripts/run_env_analysis.py
```

## Relatórios

Os relatórios gerados pelos scripts são salvos no diretório `reports/`. O relatório consolidado contém um resumo de todas as análises realizadas.

## Requisitos

- Python 3.6+
- Acesso SSH à VPS
- Permissões para executar comandos Docker na VPS

## Como Usar

1. Conecte-se à VPS via SSH
2. Clone este repositório ou copie os scripts para a VPS
3. Execute o script principal:

```bash
python scripts/run_env_analysis.py
```

4. Verifique os relatórios gerados no diretório `reports/`

## Problemas Comuns

- **Erro de permissão**: Certifique-se de ter permissões para executar comandos Docker
- **Contêineres não encontrados**: Verifique se os contêineres estão em execução com `docker ps`
- **Arquivos .env não encontrados**: Verifique os caminhos dos arquivos .env nos scripts