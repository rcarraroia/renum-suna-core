'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

import { useAgents, useUpdateAgent, useDeleteAgent, useOptimisticAgentUpdate, useCreateNewAgent } from '@/hooks/react-query/agents/use-agents';
import { useMarketplaceTemplates, useInstallTemplate, useMyTemplates, useUnpublishTemplate, usePublishTemplate } from '@/hooks/react-query/secure-mcp/use-secure-mcp';
import { useFeatureFlag } from '@/lib/feature-flags';

import { StreamlinedInstallDialog } from '@/components/agents/installation/streamlined-install-dialog';
import type { MarketplaceTemplate } from '@/components/agents/installation/types';

import { getAgentAvatar } from '../../../lib/utils/get-agent-style';
import { AgentsParams } from '@/hooks/react-query/agents/utils';

import { AgentsPageHeader } from '@/components/agents/custom-agents-page/header';
import { TabsNavigation } from '@/components/agents/custom-agents-page/tabs-navigation';
import { MyAgentsTab } from '@/components/agents/custom-agents-page/my-agents-tab';
import { MarketplaceTab } from '@/components/agents/custom-agents-page/marketplace-tab';
import { MyTemplatesTab } from '@/components/agents/custom-agents-page/my-templates-tab';
import { PublishDialog } from '@/components/agents/custom-agents-page/publish-dialog';
import { LoadingSkeleton } from '@/components/agents/custom-agents-page/loading-skeleton';


type ViewMode = 'grid' | 'list';
type AgentSortOption = 'name' | 'created_at' | 'updated_at' | 'tools_count';
type MarketplaceSortOption = 'newest' | 'popular' | 'most_downloaded' | 'name';
type SortOrder = 'asc' | 'desc';

interface FilterOptions {
  hasDefaultAgent: boolean;
  hasMcpTools: boolean;
  hasAgentpressTools: boolean;
  selectedTools: string[];
}

interface PublishDialogData {
  templateId: string;
  templateName: string;
  currentTags: string[];
}

export default function AgentsPage() {
  const { enabled: customAgentsEnabled, loading: agentsFlagLoading } = useFeatureFlag("custom_agents");
  const { enabled: agentMarketplaceEnabled, loading: marketplaceFlagLoading } = useFeatureFlag("agent_marketplace");
  const router = useRouter();
  const flagLoading = agentsFlagLoading || marketplaceFlagLoading;

  useEffect(() => {
    if (!flagLoading && !customAgentsEnabled) {
      router.replace("/dashboard");
    }
  }, [flagLoading, customAgentsEnabled, router]);

  const [activeTab, setActiveTab] = useState("my-agents");
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingAgentId, setEditingAgentId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  
  const [agentsPage, setAgentsPage] = useState(1);
  const [agentsSearchQuery, setAgentsSearchQuery] = useState('');
  const [agentsSortBy, setAgentsSortBy] = useState<AgentSortOption>('created_at');
  const [agentsSortOrder, setAgentsSortOrder] = useState<SortOrder>('desc');
  const [agentsFilters, setAgentsFilters] = useState<FilterOptions>({
    hasDefaultAgent: false,
    hasMcpTools: false,
    hasAgentpressTools: false,
    selectedTools: []
  });

  const [marketplacePage, setMarketplacePage] = useState(1);
  const [marketplaceSearchQuery, setMarketplaceSearchQuery] = useState('');
  const [marketplaceSelectedTags, setMarketplaceSelectedTags] = useState<string[]>([]);
  const [marketplaceSortBy, setMarketplaceSortBy] = useState<MarketplaceSortOption>('newest');
  const [installingItemId, setInstallingItemId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<MarketplaceTemplate | null>(null);
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [marketplaceFilter, setMarketplaceFilter] = useState<'all' | 'kortix' | 'community'>('all');

  const [templatesActioningId, setTemplatesActioningId] = useState<string | null>(null);
  const [publishDialog, setPublishDialog] = useState<PublishDialogData | null>(null);
  const [publishTags, setPublishTags] = useState('');

  const agentsQueryParams: AgentsParams = useMemo(() => {
    const params: AgentsParams = {
      page: agentsPage,
      limit: 20,
      search: agentsSearchQuery || undefined,
      sort_by: agentsSortBy,
      sort_order: agentsSortOrder,
    };

    if (agentsFilters.hasDefaultAgent) {
      params.has_default = true;
    }
    if (agentsFilters.hasMcpTools) {
      params.has_mcp_tools = true;
    }
    if (agentsFilters.hasAgentpressTools) {
      params.has_agentpress_tools = true;
    }
    if (agentsFilters.selectedTools.length > 0) {
      params.tools = agentsFilters.selectedTools.join(',');
    }

    return params;
  }, [agentsPage, agentsSearchQuery, agentsSortBy, agentsSortOrder, agentsFilters]);

  const marketplaceQueryParams = useMemo(() => ({
    limit: 20,
    offset: (marketplacePage - 1) * 20,
    search: marketplaceSearchQuery || undefined,
    tags: marketplaceSelectedTags.length > 0 ? marketplaceSelectedTags.join(',') : undefined,
  }), [marketplacePage, marketplaceSearchQuery, marketplaceSelectedTags]);

  const { data: agentsResponse, isLoading: agentsLoading, error: agentsError, refetch: loadAgents } = useAgents(agentsQueryParams);
  const { data: marketplaceTemplates, isLoading: marketplaceLoading } = useMarketplaceTemplates(marketplaceQueryParams);
  const { data: myTemplates, isLoading: templatesLoading, error: templatesError } = useMyTemplates();
  
  const updateAgentMutation = useUpdateAgent();
  const deleteAgentMutation = useDeleteAgent();
  const createNewAgentMutation = useCreateNewAgent();
  const { optimisticallyUpdateAgent, revertOptimisticUpdate } = useOptimisticAgentUpdate();
  const installTemplateMutation = useInstallTemplate();
  const unpublishMutation = useUnpublishTemplate();
  const publishMutation = usePublishTemplate();

  const agents = agentsResponse?.agents || [];
  const agentsPagination = agentsResponse?.pagination;

  const { kortixTeamItems, communityItems } = useMemo(() => {
    const kortixItems: MarketplaceTemplate[] = [];
    const communityItems: MarketplaceTemplate[] = [];

    if (marketplaceTemplates) {
      marketplaceTemplates.forEach(template => {
        const item: MarketplaceTemplate = {
          id: template.template_id,
          name: template.name,
          description: template.description,
          tags: template.tags || [],
          download_count: template.download_count || 0,
          creator_name: template.creator_name || 'Anonymous',
          created_at: template.created_at,
          marketplace_published_at: template.marketplace_published_at,
          avatar: template.avatar,
          avatar_color: template.avatar_color,
          template_id: template.template_id,
          is_kortix_team: template.is_kortix_team,
          mcp_requirements: template.mcp_requirements,
          metadata: template.metadata,
        };

        if (template.is_kortix_team) {
          kortixItems.push(item);
        } else {
          communityItems.push(item);
        }
      });
    }

    const sortItems = (items: MarketplaceTemplate[]) => {
      return items.sort((a, b) => {
        switch (marketplaceSortBy) {
          case 'newest':
            return new Date(b.marketplace_published_at || b.created_at).getTime() - 
                   new Date(a.marketplace_published_at || a.created_at).getTime();
          case 'popular':
          case 'most_downloaded':
            return b.download_count - a.download_count;
          case 'name':
            return a.name.localeCompare(b.name);
          default:
            return 0;
        }
      });
    };

    return {
      kortixTeamItems: sortItems(kortixItems),
      communityItems: sortItems(communityItems)
    };
  }, [marketplaceTemplates, marketplaceSortBy]);

  const allMarketplaceItems = useMemo(() => {
    if (marketplaceFilter === 'kortix') {
      return kortixTeamItems;
    } else if (marketplaceFilter === 'community') {
      return communityItems;
    }
    return [...kortixTeamItems, ...communityItems];
  }, [kortixTeamItems, communityItems, marketplaceFilter]);

  const handleTabChange = (newTab: string) => {
    setActiveTab(newTab);
  };

  const clearAgentsFilters = () => {
    setAgentsSearchQuery('');
    setAgentsFilters({
      hasDefaultAgent: false,
      hasMcpTools: false,
      hasAgentpressTools: false,
      selectedTools: []
    });
    setAgentsPage(1);
  };

  useEffect(() => {
    setAgentsPage(1);
  }, [agentsSearchQuery, agentsSortBy, agentsSortOrder, agentsFilters]);

  useEffect(() => {
    setMarketplacePage(1);
  }, [marketplaceSearchQuery, marketplaceSelectedTags, marketplaceSortBy]);

  const handleDeleteAgent = async (agentId: string) => {
    try {
      await deleteAgentMutation.mutateAsync(agentId);
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  const handleToggleDefault = async (agentId: string, currentDefault: boolean) => {
    optimisticallyUpdateAgent(agentId, { is_default: !currentDefault });
    try {
      await updateAgentMutation.mutateAsync({
        agentId,
        is_default: !currentDefault
      });
    } catch (error) {
      revertOptimisticUpdate(agentId);
      console.error('Error updating agent:', error);
    }
  };

  const handleEditAgent = (agentId: string) => {
    setEditingAgentId(agentId);
    setEditDialogOpen(true);
  };

  const handleCreateNewAgent = () => {
    createNewAgentMutation.mutate();
  };

  const handleInstallClick = (item: MarketplaceTemplate, e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
    }
    setSelectedItem(item);
    setShowInstallDialog(true);
  };

  const handleInstall = async (
    item: MarketplaceTemplate, 
    instanceName?: string, 
    profileMappings?: Record<string, string>, 
    customMcpConfigs?: Record<string, Record<string, any>>
  ) => {
    setInstallingItemId(item.id);
    
    try {
      if (!instanceName || instanceName.trim() === '') {
        toast.error('Please provide a name for the agent');
        return;
      }

      const regularRequirements = item.mcp_requirements?.filter(req => 
        !req.custom_type
      ) || [];
      const missingProfiles = regularRequirements.filter(req => 
        !profileMappings || !profileMappings[req.qualified_name] || profileMappings[req.qualified_name].trim() === ''
      );
      
      if (missingProfiles.length > 0) {
        const missingNames = missingProfiles.map(req => req.display_name).join(', ');
        toast.error(`Please select credential profiles for: ${missingNames}`);
        return;
      }

      const customRequirements = item.mcp_requirements?.filter(req => 
        req.custom_type && req.custom_type !== 'pipedream'
      ) || [];
      const missingCustomConfigs = customRequirements.filter(req => 
        !customMcpConfigs || !customMcpConfigs[req.qualified_name] || 
        req.required_config.some(field => !customMcpConfigs[req.qualified_name][field]?.trim())
      );
      
      if (missingCustomConfigs.length > 0) {
        const missingNames = missingCustomConfigs.map(req => req.display_name).join(', ');
        toast.error(`Please provide all required configuration for: ${missingNames}`);
        return;
      }

      const pipedreamRequirements = item.mcp_requirements?.filter(req => 
        req.custom_type === 'pipedream'
      ) || [];
      const missingPipedreamConfigs = pipedreamRequirements.filter(req => 
        !customMcpConfigs || !customMcpConfigs[req.qualified_name] || 
        !customMcpConfigs[req.qualified_name].profile_id
      );
      
      if (missingPipedreamConfigs.length > 0) {
        const missingNames = missingPipedreamConfigs.map(req => req.display_name).join(', ');
        toast.error(`Please select Pipedream profiles for: ${missingNames}`);
        return;
      }

      const result = await installTemplateMutation.mutateAsync({
        template_id: item.template_id,
        instance_name: instanceName,
        profile_mappings: profileMappings,
        custom_mcp_configs: customMcpConfigs
      });

      if (result.status === 'installed') {
        toast.success(`Agent "${instanceName}" installed successfully!`);
        setShowInstallDialog(false);
        handleTabChange('my-agents');
      } else if (result.status === 'configs_required') {
        toast.error('Please provide all required configurations');
        return;
      } else {
        toast.error('Unexpected response from server. Please try again.');
        return;
      }
    } catch (error: any) {
      console.error('Installation error:', error);

      if (error.message?.includes('already in your library')) {
        toast.error('This agent is already in your library');
      } else if (error.message?.includes('Credential profile not found')) {
        toast.error('One or more selected credential profiles could not be found. Please refresh and try again.');
      } else if (error.message?.includes('Missing credential profile')) {
        toast.error('Please select credential profiles for all required services');
      } else if (error.message?.includes('Invalid credential profile')) {
        toast.error('One or more selected credential profiles are invalid. Please select valid profiles.');
      } else if (error.message?.includes('inactive')) {
        toast.error('One or more selected credential profiles are inactive. Please select active profiles.');
      } else if (error.message?.includes('Template not found')) {
        toast.error('This agent template is no longer available');
      } else if (error.message?.includes('Access denied')) {
        toast.error('You do not have permission to install this agent');
      } else {
        toast.error(error.message || 'Failed to install agent. Please try again.');
      }
    } finally {
      setInstallingItemId(null);
    }
  };

  const getItemStyling = (item: MarketplaceTemplate) => {
    if (item.avatar && item.avatar_color) {
      return {
        avatar: item.avatar,
        color: item.avatar_color,
      };
    }
    return getAgentAvatar(item.id);
  };

  const handleUnpublish = async (templateId: string, templateName: string) => {
    try {
      setTemplatesActioningId(templateId);
      await unpublishMutation.mutateAsync(templateId);
      toast.success(`${templateName} has been unpublished from the marketplace`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to unpublish template');
    } finally {
      setTemplatesActioningId(null);
    }
  };

  const openPublishDialog = (template: any) => {
    setPublishDialog({
      templateId: template.template_id,
      templateName: template.name,
      currentTags: template.tags || []
    });
    setPublishTags((template.tags || []).join(', '));
  };

  const handlePublish = async () => {
    if (!publishDialog) return;

    try {
      setTemplatesActioningId(publishDialog.templateId);
      
      const tags = publishTags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      await publishMutation.mutateAsync({
        template_id: publishDialog.templateId,
        tags: tags.length > 0 ? tags : undefined
      });
      
      toast.success(`${publishDialog.templateName} has been published to the marketplace`);
      setPublishDialog(null);
      setPublishTags('');
    } catch (error: any) {
      toast.error(error.message || 'Failed to publish template');
    } finally {
      setTemplatesActioningId(null);
    }
  };

  const getTemplateStyling = (template: any) => {
    if (template.avatar && template.avatar_color) {
      return {
        avatar: template.avatar,
        color: template.avatar_color,
      };
    }
    return getAgentAvatar(template.template_id);
  };

  if (flagLoading) {
    return (
      <div className="min-h-screen">
        <div className="container max-w-7xl mx-auto px-4 py-8">
          <AgentsPageHeader />
        </div>
        
        <div className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/40 shadow-sm">
          <div className="container max-w-7xl mx-auto px-4 py-4">
            <TabsNavigation activeTab={activeTab} onTabChange={handleTabChange} />
          </div>
        </div>

        <div className="container max-w-7xl mx-auto px-4 py-8">
          <LoadingSkeleton />
        </div>
      </div>
    );
  }

  if (!customAgentsEnabled) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <AgentsPageHeader />
      </div>
      <div className="sticky top-0 z-50 relative">
        <div className="absolute inset-0 backdrop-blur-md" style={{
          maskImage: 'linear-gradient(to bottom, black 0%, black 60%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(to bottom, black 0%, black 60%, transparent 100%)'
        }}></div>
        <div className="relative bg-gradient-to-b from-background/95 via-background/70 to-transparent">
          <div className="container mx-auto max-w-7xl px-4 py-4">
            <TabsNavigation activeTab={activeTab} onTabChange={handleTabChange} />
          </div>
        </div>
      </div>
      <div className="container mx-auto max-w-7xl px-4 py-2">
        <div className="w-full">
          {activeTab === "my-agents" && (
            <MyAgentsTab
              agentsSearchQuery={agentsSearchQuery}
              setAgentsSearchQuery={setAgentsSearchQuery}
              agentsLoading={agentsLoading}
              agents={agents}
              agentsPagination={agentsPagination}
              viewMode={viewMode}
              onCreateAgent={handleCreateNewAgent}
              onEditAgent={handleEditAgent}
              onDeleteAgent={handleDeleteAgent}
              onToggleDefault={handleToggleDefault}
              onClearFilters={clearAgentsFilters}
              deleteAgentMutation={deleteAgentMutation}
              setAgentsPage={setAgentsPage}
            />
          )}

          {activeTab === "marketplace" && (
            <MarketplaceTab
              marketplaceSearchQuery={marketplaceSearchQuery}
              setMarketplaceSearchQuery={setMarketplaceSearchQuery}
              marketplaceFilter={marketplaceFilter}
              setMarketplaceFilter={setMarketplaceFilter}
              marketplaceLoading={marketplaceLoading}
              allMarketplaceItems={allMarketplaceItems}
              kortixTeamItems={kortixTeamItems}
              communityItems={communityItems}
              installingItemId={installingItemId}
              onInstallClick={handleInstallClick}
              getItemStyling={getItemStyling}
            />
          )}

          {activeTab === "my-templates" && (
            <MyTemplatesTab
              templatesError={templatesError}
              templatesLoading={templatesLoading}
              myTemplates={myTemplates}
              templatesActioningId={templatesActioningId}
              onPublish={openPublishDialog}
              onUnpublish={handleUnpublish}
              onViewInMarketplace={() => handleTabChange('marketplace')}
              onSwitchToMyAgents={() => handleTabChange('my-agents')}
              getTemplateStyling={getTemplateStyling}
            />
          )}
        </div>

        <PublishDialog
          publishDialog={publishDialog}
          publishTags={publishTags}
          templatesActioningId={templatesActioningId}
          onClose={() => setPublishDialog(null)}
          onPublishTagsChange={setPublishTags}
          onPublish={handlePublish}
        />

        <StreamlinedInstallDialog
          item={selectedItem}
          open={showInstallDialog}
          onOpenChange={setShowInstallDialog}
          onInstall={handleInstall}
          isInstalling={installingItemId === selectedItem?.id}
        />
      </div>
    </div>
  );
}