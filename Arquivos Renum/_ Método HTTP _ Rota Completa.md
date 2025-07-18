| Método HTTP | Rota Completa | Parâmetros/Corpo da Requisição | Formato da Resposta Esperado | Observações |
|-------------|---------------|--------------------------------|------------------------------|-------------|
| POST | https://api.orshot.com/v1/studio/render | N/A | JSON | Encontrado em renum-suna-core/frontend/src/app/api/share-page/og-image/route.tsx | Rota para serviço externo. Verificar se é proxy ou chamada direta. |
| GET | /api/${backendUrl}/api/webhooks/test/${workflowId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/app/api/webhooks/trigger/[workflowId]/route.ts | Rota com variável de backend. Verificar se é proxy ou chamada direta. |
| POST | /api/${backendUrl}/api/send-welcome-email | N/A | JSON | Encontrado em renum-suna-core/frontend/src/app/auth/actions.ts | Rota com variável de backend. Verificar se é proxy ou chamada direta. |
| POST | /api/mcp/discover-custom-tools | N/A | JSON | Encontrado em renum-suna-core/frontend/src/components/agents/mcp/custom-mcp-dialog.tsx |
| GET | /api/knowledge-base/${entryId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/knowledge-base/use-knowledge-base-queries.ts |
| PUT | /api/knowledge-base/${entryId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/knowledge-base/use-knowledge-base-queries.ts |
| DELETE | /api/knowledge-base/${entryId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/knowledge-base/use-knowledge-base-queries.ts |
| GET | /api/credential-profiles | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| GET | /api/credential-profiles/${encodedName} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| GET | /api/credential-profiles/profile/${profileId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| POST | /api/credential-profiles | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| PUT | /api/credential-profiles/${profileId}/set-default | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| DELETE | /api/credential-profiles/${profileId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-credential-profiles.ts | Rota com variável API_BASE. Verificar se é proxy ou chamada direta. |
| GET | /api/mcp/servers | ${params} | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-mcp-servers.ts |
| GET | /api/mcp/servers/${qualifiedName} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-mcp-servers.ts |
| GET | /api/mcp/popular-servers | ${params} | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/mcp/use-mcp-servers.ts |
| GET | /api/secure-mcp/credentials | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| POST | /api/secure-mcp/credentials | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| DELETE | /api/secure-mcp/credentials/${encodeURIComponent(mcp_qualified_name)} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| GET | /api/templates/marketplace | ${searchParams} | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| GET | /api/templates/${template_id} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| POST | /api/templates | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| GET | /api/templates/my | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| POST | /api/templates/${template_id}/publish | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| POST | /api/templates/${template_id}/unpublish | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| POST | /api/templates/install | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/secure-mcp/use-secure-mcp.ts |
| PUT | /api/triggers/${data.triggerId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/triggers/use-agent-triggers.ts |
| DELETE | /api/triggers/${triggerId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/triggers/use-agent-triggers.ts |
| POST | /api/integrations/install | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/triggers/use-oauth-integrations.ts |
| DELETE | /api/integrations/uninstall/${triggerId} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/triggers/use-oauth-integrations.ts |
| GET | /api/triggers/providers | N/A | JSON | Encontrado em renum-suna-core/frontend/src/hooks/react-query/triggers/use-trigger-providers.ts |
| GET | /api/feature-flags/${flagName} | N/A | JSON | Encontrado em renum-suna-core/frontend/src/lib/feature-flags.ts |
| GET | /api/feature-flags | N/A | JSON | Encontrado em renum-suna-core/frontend/src/lib/feature-flags.ts |
