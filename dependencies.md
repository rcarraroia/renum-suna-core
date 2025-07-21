# Documentação de Dependências do Projeto

Este documento lista todas as dependências necessárias para o ambiente Python 3.11.9 do projeto Suna/Renum. As dependências estão organizadas por categorias para facilitar a compreensão e manutenção.

## Dependências Essenciais

Estas são as dependências fundamentais para o funcionamento básico do sistema:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| python-dotenv | 1.0.1 | Carrega variáveis de ambiente de arquivos .env |
| fastapi | 0.115.12 | Framework web para construção de APIs |
| uvicorn | 0.27.1 | Servidor ASGI para FastAPI |
| pydantic | 1.10.8 | Validação de dados e configurações |
| httpx | 0.28.0 | Cliente HTTP para Python |
| python-multipart | 0.0.20 | Suporte para upload de arquivos multipart |

## Dependências de Banco de Dados e Cache

Dependências relacionadas ao armazenamento e cache de dados:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| supabase | 2.17.0 | Cliente Python para Supabase |
| redis | 5.2.1 | Cliente Python para Redis |
| upstash-redis | 1.3.0 | Cliente para Upstash Redis |
| prisma | 0.15.0 | ORM para Python |
| pyjwt | 2.10.1 | Implementação de JSON Web Tokens |

## Dependências de Processamento em Background

Dependências para processamento assíncrono e em segundo plano:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| dramatiq | 1.18.0 | Sistema de processamento de tarefas em background |
| pika | 1.3.2 | Cliente Python para RabbitMQ |
| apscheduler | >= 3.10.0 | Agendador de tarefas avançado |
| croniter | >= 1.4.0 | Iterador para expressões cron |
| qstash | >= 2.0.0 | Serviço de mensagens e agendamento |
| asyncio | 3.4.3 | Biblioteca para programação assíncrona |
| nest-asyncio | 1.6.0 | Permite aninhar loops de eventos asyncio |

## Dependências de IA e LLM

Dependências relacionadas a modelos de linguagem e IA:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| mcp | 1.9.4 | Model Context Protocol |
| litellm | 1.72.2 | Biblioteca para interação com LLMs |
| openai | 1.90.0 | Cliente oficial da OpenAI |
| exa-py | 1.9.1 | Biblioteca para busca semântica |
| langfuse | 2.60.5 | Plataforma de observabilidade para LLMs |

## Dependências de Agente e Automação

Dependências para funcionalidades de agente e automação:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| daytona-sdk | 0.21.0 | SDK para Daytona |
| daytona-api-client | 0.21.0 | Cliente API para Daytona |
| daytona-api-client-async | 0.21.0 | Cliente API assíncrono para Daytona |
| e2b-code-interpreter | 1.2.0 | Interpretador de código para agentes |
| tavily-python | 0.5.4 | Cliente Python para API Tavily |
| vncdotool | 1.2.0 | Ferramenta para automação de VNC |
| pytesseract | 0.3.13 | Wrapper para Tesseract OCR |

## Dependências de Rede e Comunicação

Dependências para comunicação em rede:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| aiohttp | 3.12.0 | Cliente/servidor HTTP assíncrono |
| websockets | 11.0.3 | Implementação de WebSockets para Python |
| requests | 2.32.3 | Biblioteca HTTP para Python |
| email-validator | 2.0.0 | Validador de endereços de email |
| mailtrap | 2.0.1 | Cliente para serviço Mailtrap |

## Dependências de Processamento de Dados

Dependências para processamento e manipulação de dados:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| PyPDF2 | 3.0.1 | Manipulação de arquivos PDF |
| python-docx | 1.1.0 | Criação e edição de documentos Word |
| openpyxl | 3.1.2 | Manipulação de planilhas Excel |
| chardet | 5.2.0 | Detecção automática de codificação de caracteres |
| PyYAML | 6.0.1 | Parser e emissor de YAML |
| Pillow | >= 10.4.0 | Processamento de imagens |
| altair | 4.2.2 | Biblioteca de visualização de dados |

## Dependências de Segurança

Dependências relacionadas à segurança:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| cryptography | >= 41.0.0 | Primitivas criptográficas |
| certifi | 2024.2.2 | Certificados CA confiáveis |

## Dependências de Monitoramento e Logging

Dependências para monitoramento e logging:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| sentry-sdk | 2.29.1 | Integração com Sentry para monitoramento de erros |
| prometheus-client | 0.21.1 | Cliente Python para Prometheus |
| structlog | 25.4.0 | Logging estruturado para Python |

## Dependências de Integração

Dependências para integração com serviços externos:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| boto3 | 1.37.3 | SDK da AWS para Python |
| stripe | 12.0.1 | Cliente Python para API Stripe |

## Dependências de Desenvolvimento e Testes

Dependências utilizadas para desenvolvimento e testes:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| pytest | 8.3.3 | Framework de testes para Python |
| pytest-asyncio | 0.24.0 | Suporte a testes assíncronos |
| click | 8.1.7 | Criação de interfaces de linha de comando |
| questionary | 2.0.1 | Criação de prompts interativos |
| packaging | 24.1 | Utilitários para trabalhar com pacotes Python |
| setuptools | 75.3.0 | Ferramentas para empacotamento Python |
| python-ripgrep | 0.0.6 | Wrapper Python para ripgrep |

## Dependências Específicas do MCP

Dependências específicas para o funcionamento do MCP:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| pydantic-core | 2.10.1 | Núcleo de validação do Pydantic |
| typing-extensions | 4.7.1 | Extensões para o módulo typing |

## Dependências de Implantação

Dependências utilizadas para implantação em produção:

| Dependência | Versão | Descrição |
|-------------|--------|-----------|
| gunicorn | >= 23.0.0 | Servidor WSGI para produção |

## Notas Importantes

1. As versões específicas são importantes para garantir compatibilidade entre os componentes.
2. Algumas dependências têm requisitos de versão mínima (indicadas com >=) e podem ser atualizadas conforme necessário.
3. O ambiente Python 3.11.9 é recomendado para garantir compatibilidade com todas as dependências.
4. A instalação deve ser feita preferencialmente em um ambiente virtual para evitar conflitos.

## Instalação

Para instalar todas as dependências de uma vez, utilize o comando:

```bash
pip install -e .
```

Ou para instalar grupos específicos de dependências, utilize os scripts batch fornecidos:

- `install_mcp_deps.bat` - Instala o MCP e dependências básicas
- `install_mcp_related_deps.bat` - Instala dependências relacionadas ao MCP
- `install_final_deps.bat` e `install_final_deps2.bat` - Instala dependências adicionais
- `install_more_deps.bat` - Instala dependências comuns