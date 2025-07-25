import React, { useState, useEffect } from 'react';

interface StatsDataPoint {
  timestamp: string;
  total_connections: number;
  active_connections: number;
  idle_connections: number;
  authenticated_connections: number;
  anonymous_connections: number;
  total_channels: number;
  total_messages_sent: number;
  total_bytes_transferred: number;
}

interface WebSocketStatsChartProps {
  className?: string;
}

export const WebSocketStatsChart: React.FC<WebSocketStatsChartProps> = ({
  className = ''
}) => {
  const [statsHistory, setStatsHistory] = useState<StatsDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<1 | 6 | 24>(6); // horas
  const [selectedMetric, setSelectedMetric] = useState<'connections' | 'messages' | 'bytes'>('connections');

  const loadStatsHistory = async () => {
    try {
      setError(null);
      const response = await fetch(`/api/v1/admin/websocket/stats/history?hours=${timeRange}`);
      
      if (!response.ok) {
        throw new Error('Erro ao carregar histórico');
      }

      const data = await response.json();
      setStatsHistory(data.history || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatsHistory();
    
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(loadStatsHistory, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const getChartData = () => {
    if (!statsHistory.length) return [];

    return statsHistory.map(point => ({
      time: new Date(point.timestamp).toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      timestamp: point.timestamp,
      ...point
    }));
  };

  const getMaxValue = (metric: string) => {
    if (!statsHistory.length) return 100;
    
    const values = statsHistory.map(point => {
      switch (metric) {
        case 'connections':
          return point.total_connections;
        case 'messages':
          return point.total_messages_sent;
        case 'bytes':
          return point.total_bytes_transferred;
        default:
          return 0;
      }
    });
    
    return Math.max(...values, 10);
  };

  const formatValue = (value: number, metric: string) => {
    switch (metric) {
      case 'bytes':
        if (value >= 1024 * 1024 * 1024) {
          return `${(value / (1024 * 1024 * 1024)).toFixed(1)}GB`;
        } else if (value >= 1024 * 1024) {
          return `${(value / (1024 * 1024)).toFixed(1)}MB`;
        } else if (value >= 1024) {
          return `${(value / 1024).toFixed(1)}KB`;
        }
        return `${value}B`;
      case 'messages':
        if (value >= 1000000) {
          return `${(value / 1000000).toFixed(1)}M`;
        } else if (value >= 1000) {
          return `${(value / 1000).toFixed(1)}K`;
        }
        return value.toString();
      default:
        return value.toString();
    }
  };

  const renderChart = () => {
    const chartData = getChartData();
    if (!chartData.length) return null;

    const maxValue = getMaxValue(selectedMetric);
    const chartHeight = 200;
    const chartWidth = 600;
    const padding = 40;

    const getYPosition = (value: number) => {
      return chartHeight - padding - ((value / maxValue) * (chartHeight - 2 * padding));
    };

    const getXPosition = (index: number) => {
      return padding + (index / (chartData.length - 1)) * (chartWidth - 2 * padding);
    };

    // Dados para diferentes métricas
    const getMetricData = () => {
      switch (selectedMetric) {
        case 'connections':
          return [
            {
              name: 'Total',
              data: chartData.map(d => d.total_connections),
              color: '#3B82F6'
            },
            {
              name: 'Ativas',
              data: chartData.map(d => d.active_connections),
              color: '#10B981'
            },
            {
              name: 'Inativas',
              data: chartData.map(d => d.idle_connections),
              color: '#F59E0B'
            }
          ];
        case 'messages':
          return [
            {
              name: 'Mensagens',
              data: chartData.map(d => d.total_messages_sent),
              color: '#8B5CF6'
            }
          ];
        case 'bytes':
          return [
            {
              name: 'Bytes',
              data: chartData.map(d => d.total_bytes_transferred),
              color: '#EF4444'
            }
          ];
        default:
          return [];
      }
    };

    const metricData = getMetricData();

    return (
      <div className="relative">
        <svg width={chartWidth} height={chartHeight} className="border border-gray-200 rounded">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
            <g key={ratio}>
              <line
                x1={padding}
                y1={getYPosition(maxValue * ratio)}
                x2={chartWidth - padding}
                y2={getYPosition(maxValue * ratio)}
                stroke="#E5E7EB"
                strokeWidth="1"
              />
              <text
                x={padding - 5}
                y={getYPosition(maxValue * ratio) + 4}
                textAnchor="end"
                fontSize="12"
                fill="#6B7280"
              >
                {formatValue(maxValue * ratio, selectedMetric)}
              </text>
            </g>
          ))}

          {/* Time labels */}
          {chartData.map((point, index) => {
            if (index % Math.ceil(chartData.length / 6) === 0) {
              return (
                <text
                  key={index}
                  x={getXPosition(index)}
                  y={chartHeight - 10}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#6B7280"
                >
                  {point.time}
                </text>
              );
            }
            return null;
          })}

          {/* Data lines */}
          {metricData.map((series, seriesIndex) => {
            const pathData = series.data.map((value, index) => {
              const x = getXPosition(index);
              const y = getYPosition(value);
              return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
            }).join(' ');

            return (
              <g key={seriesIndex}>
                <path
                  d={pathData}
                  fill="none"
                  stroke={series.color}
                  strokeWidth="2"
                />
                {/* Data points */}
                {series.data.map((value, index) => (
                  <circle
                    key={index}
                    cx={getXPosition(index)}
                    cy={getYPosition(value)}
                    r="3"
                    fill={series.color}
                  />
                ))}
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="flex justify-center mt-4 space-x-6">
          {metricData.map((series, index) => (
            <div key={index} className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: series.color }}
              ></div>
              <span className="text-sm text-gray-600">{series.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando estatísticas...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Estatísticas WebSocket
          </h3>
          
          <div className="flex items-center space-x-4">
            {/* Seletor de métrica */}
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="connections">Conexões</option>
              <option value="messages">Mensagens</option>
              <option value="bytes">Bytes Transferidos</option>
            </select>
            
            {/* Seletor de período */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value) as any)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={1}>Última hora</option>
              <option value={6}>Últimas 6 horas</option>
              <option value={24}>Últimas 24 horas</option>
            </select>
            
            <button
              onClick={loadStatsHistory}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800 font-medium">{error}</span>
            </div>
          </div>
        ) : statsHistory.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Sem dados disponíveis
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Não há dados de estatísticas para o período selecionado.
            </p>
          </div>
        ) : (
          <div className="flex justify-center">
            {renderChart()}
          </div>
        )}
      </div>

      {/* Summary stats */}
      {statsHistory.length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-sm font-medium text-gray-700">Pico de Conexões</div>
              <div className="text-lg font-bold text-blue-600">
                {Math.max(...statsHistory.map(s => s.total_connections))}
              </div>
            </div>
            
            <div>
              <div className="text-sm font-medium text-gray-700">Média de Conexões</div>
              <div className="text-lg font-bold text-green-600">
                {Math.round(statsHistory.reduce((sum, s) => sum + s.total_connections, 0) / statsHistory.length)}
              </div>
            </div>
            
            <div>
              <div className="text-sm font-medium text-gray-700">Total de Mensagens</div>
              <div className="text-lg font-bold text-purple-600">
                {formatValue(Math.max(...statsHistory.map(s => s.total_messages_sent)), 'messages')}
              </div>
            </div>
            
            <div>
              <div className="text-sm font-medium text-gray-700">Dados Transferidos</div>
              <div className="text-lg font-bold text-red-600">
                {formatValue(Math.max(...statsHistory.map(s => s.total_bytes_transferred)), 'bytes')}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};