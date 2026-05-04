'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Database, HardDrive, TrendingUp, AlertCircle, CheckCircle, DollarSign, Zap } from 'lucide-react';

// API Base URL
const API_URL = 'http://35.85.216.208:8000';

interface MetricsSummary {
  total_metrics: number;
  ec2_metrics_count: number;
  s3_metrics_count: number;
  latest_collection: string;
  status: string;
}

interface CPUData {
  timestamp: string;
  cpu: number;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [cpuData, setCpuData] = useState<CPUData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [s3Data, setS3Data] = useState<any>(null);
  const [costSummary, setCostSummary] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const summaryRes = await fetch(`${API_URL}/api/metrics/summary`);
      if (!summaryRes.ok) throw new Error('Failed to fetch summary');
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      const today = new Date().toISOString().split('T')[0];
      const metricsRes = await fetch(
        `${API_URL}/api/metrics/ec2/i-03fcdfc149b765c98?start_date=${today}&limit=24`
      );
      
      if (!metricsRes.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await metricsRes.json();
      
      if (metricsData.items && Array.isArray(metricsData.items)) {
        const chartData = metricsData.items.map((item: any) => ({
          timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          cpu: parseFloat(item.metrics.CPUUtilization_Average)
        })).reverse();
        setCpuData(chartData);
      } else {
        setCpuData([]);
      }

      const s3Res = await fetch(`${API_URL}/api/metrics/s3?limit=1`);
      if (s3Res.ok) {
        const s3ResData = await s3Res.json();
        if (s3ResData.items && s3ResData.items.length > 0) {
          setS3Data(s3ResData.items[0]);
        }
      }

      const costRes = await fetch(`${API_URL}/api/metrics/costs/summary?days=7`);
      if (costRes.ok) {
        const costData = await costRes.json();
        setCostSummary(costData);
      }

      const recsRes = await fetch(`${API_URL}/api/metrics/recommendations?status=open`);
      if (recsRes.ok) {
        const recsData = await recsRes.json();
        setRecommendations(recsData.recommendations || []);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(`Failed to load data: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-sm font-medium text-gray-700 animate-pulse">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6 max-w-md animate-fadeIn">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <div className="text-sm font-semibold text-red-600">Connection Error</div>
          </div>
          <div className="text-sm text-gray-600">{error}</div>
        </div>
      </div>
    );
  }

  const totalSavings = recommendations.reduce((sum, r) => sum + (r.estimated_savings_monthly || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 animate-slideInLeft">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">
                  Scalar
                </h1>
                <p className="text-sm text-gray-500">
                  AWS Cost Intelligence
                </p>
              </div>
            </div>
            {totalSavings > 0 && (
              <div className="text-right animate-slideInRight">
                <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Potential Savings
                </div>
                <div className="flex items-center justify-end gap-1">
                  <DollarSign className="w-5 h-5 text-emerald-600" />
                  <div className="text-2xl font-semibold text-emerald-600 transition-all duration-500">
                    {totalSavings.toFixed(2)}
                  </div>
                </div>
                <div className="text-xs text-gray-500">per month</div>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { 
              label: 'Total Metrics', 
              value: summary?.total_metrics || 0, 
              delay: '0ms',
              icon: Activity,
              color: 'blue'
            },
            { 
              label: 'EC2 Instances', 
              value: summary?.ec2_metrics_count || 0, 
              delay: '100ms',
              icon: Database,
              color: 'purple'
            },
            { 
              label: 'S3 Buckets', 
              value: summary?.s3_metrics_count || 0, 
              delay: '200ms',
              icon: HardDrive,
              color: 'indigo'
            },
            { 
              label: 'System Status', 
              value: 'Active', 
              delay: '300ms', 
              isStatus: true,
              icon: CheckCircle,
              color: 'emerald'
            }
          ].map((stat, i) => {
            const Icon = stat.icon;
            const colorClasses = {
              blue: 'bg-blue-50 text-blue-600',
              purple: 'bg-purple-50 text-purple-600',
              indigo: 'bg-indigo-50 text-indigo-600',
              emerald: 'bg-emerald-50 text-emerald-600'
            };
            
            return (
              <div 
                key={i}
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all duration-300 animate-fadeInUp"
                style={{ animationDelay: stat.delay }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {stat.label}
                  </div>
                  <div className={`p-2 rounded-lg ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                {stat.isStatus ? (
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full mr-2 animate-pulse"></span>
                    <span className="text-sm font-medium text-gray-900">{stat.value}</span>
                  </div>
                ) : (
                  <div className="text-3xl font-semibold text-gray-900 transition-all duration-500">
                    {stat.value}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* CPU Chart - Spans 2 columns */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow duration-300 animate-fadeInUp" style={{ animationDelay: '400ms' }}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-5 h-5 text-blue-600" />
                  <h2 className="text-lg font-semibold text-gray-900">
                    CPU Utilization
                  </h2>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="font-mono">i-03fcdfc149b765c98</span>
                  <span className="text-gray-300">•</span>
                  <span>t3.micro</span>
                </div>
              </div>
            </div>
          
            {cpuData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={cpuData}>
                    <defs>
                      <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                    <XAxis 
                      dataKey="timestamp" 
                      stroke="#9CA3AF"
                      style={{ fontSize: '11px' }}
                      tickLine={false}
                    />
                    <YAxis 
                      stroke="#9CA3AF"
                      style={{ fontSize: '11px' }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white',
                        border: '1px solid #E5E7EB',
                        borderRadius: '6px',
                        fontSize: '12px'
                      }}
                      animationDuration={200}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="cpu" 
                      stroke="#3B82F6" 
                      strokeWidth={2}
                      dot={false}
                      fill="url(#colorCpu)"
                      name="CPU %"
                      animationDuration={1000}
                      animationEasing="ease-in-out"
                    />
                  </LineChart>
                </ResponsiveContainer>

                <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
                  {[
                    { label: 'Current', value: cpuData[cpuData.length - 1].cpu.toFixed(2), color: 'text-blue-600' },
                    { label: 'Average', value: (cpuData.reduce((sum, d) => sum + d.cpu, 0) / cpuData.length).toFixed(2), color: 'text-purple-600' },
                    { label: 'Peak', value: Math.max(...cpuData.map(d => d.cpu)).toFixed(2), color: 'text-orange-600' }
                  ].map((metric, i) => (
                    <div key={i} className="group">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 group-hover:text-gray-700 transition-colors">
                        {metric.label}
                      </div>
                      <div className={`text-lg font-semibold ${metric.color} transition-colors`}>
                        {metric.value}%
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center text-gray-400 py-16 bg-gray-50 rounded animate-pulse">
                <Activity className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <div className="text-sm">No data available</div>
              </div>
            )}
          </div>

          {/* Side Panel - Storage & Cost */}
          <div className="space-y-6">
            {/* S3 Storage */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all duration-300 animate-fadeInUp" style={{ animationDelay: '500ms' }}>
              <div className="flex items-center gap-2 mb-4">
                <HardDrive className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-semibold text-gray-900">
                  S3 Storage
                </h3>
              </div>
              
              {s3Data ? (
                <div className="space-y-4">
                  <div className="group">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 group-hover:text-gray-700 transition-colors">
                      Bucket
                    </div>
                    <div className="text-sm font-mono text-gray-900 truncate">
                      {s3Data.resource_id}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { 
                        label: 'Size', 
                        value: (s3Data.metrics?.BucketSizeBytes 
                          ? (s3Data.metrics.BucketSizeBytes / 1024).toFixed(2) 
                          : s3Data.BucketSizeBytes 
                          ? (s3Data.BucketSizeBytes / 1024).toFixed(2)
                          : '0.00') + ' KB',
                        color: 'text-indigo-600'
                      },
                      { 
                        label: 'Objects', 
                        value: s3Data.metrics?.NumberOfObjects || s3Data.NumberOfObjects || 0,
                        color: 'text-purple-600'
                      }
                    ].map((metric, i) => (
                      <div key={i} className="group">
                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 group-hover:text-gray-700 transition-colors">
                          {metric.label}
                        </div>
                        <div className={`text-lg font-semibold ${metric.color} transition-colors`}>
                          {metric.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8 text-sm animate-pulse">
                  <HardDrive className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                  <div>No data</div>
                </div>
              )}
            </div>

            {/* Cost Summary */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all duration-300 animate-fadeInUp" style={{ animationDelay: '600ms' }}>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-semibold text-gray-900">
                  7-Day Costs
                </h3>
              </div>
              
              {costSummary ? (
                <div className="space-y-4">
                  <div className="group">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 group-hover:text-gray-700 transition-colors">
                      Total
                    </div>
                    <div className="text-2xl font-semibold text-emerald-600 transition-colors">
                      ${costSummary.total_cost?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      ${costSummary.average_daily_cost?.toFixed(2)}/day avg
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-gray-100 space-y-2">
                    {[
                      { label: 'EC2', value: costSummary.ec2_total?.toFixed(2), color: 'text-blue-600' },
                      { label: 'S3', value: costSummary.s3_total?.toFixed(4), color: 'text-purple-600' }
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between group hover:bg-gray-50 -mx-2 px-2 py-1 rounded transition-colors">
                        <span className="text-xs font-medium text-gray-500 group-hover:text-gray-700 transition-colors">
                          {item.label}
                        </span>
                        <span className={`text-sm font-semibold ${item.color} transition-colors`}>
                          ${item.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8 text-sm animate-pulse">
                  <TrendingUp className="w-10 h-10 mx-auto mb-2 text-gray-300" />
                  <div>Loading...</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-lg border border-gray-200 animate-fadeInUp" style={{ animationDelay: '700ms' }}>
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Cost Optimization Recommendations
              </h2>
            </div>
          </div>
          
          {recommendations.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {/* Summary Banner */}
              <div className="px-6 py-4 bg-emerald-50 hover:bg-emerald-100 transition-colors duration-300">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-emerald-900">
                      {recommendations.length} optimization {recommendations.length === 1 ? 'opportunity' : 'opportunities'} identified
                    </div>
                    <div className="text-xs text-emerald-700 mt-1">
                      ${(totalSavings * 12).toFixed(2)} potential annual savings
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <DollarSign className="w-5 h-5 text-emerald-600" />
                      <div className="text-2xl font-semibold text-emerald-600 transition-all duration-500">
                        {totalSavings.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-xs text-emerald-700">per month</div>
                  </div>
                </div>
              </div>

              {/* Recommendation Items */}
              {recommendations.map((rec, index) => (
                <div 
                  key={rec.recommendation_id || index} 
                  className="px-6 py-5 hover:bg-gray-50 transition-colors duration-200 animate-fadeInUp"
                  style={{ animationDelay: `${800 + index * 100}ms` }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium transition-all duration-200 ${
                          rec.severity === 'high' ? 'bg-red-100 text-red-700 hover:bg-red-200' :
                          rec.severity === 'medium' ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' :
                          'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}>
                          {rec.severity?.toUpperCase()}
                        </span>
                        <span className="text-xs font-medium text-gray-500">
                          {rec.resource_type}
                        </span>
                      </div>
                      
                      <h3 className="text-base font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors">
                        {rec.title}
                      </h3>
                      
                      <p className="text-sm text-gray-600 mb-3">
                        {rec.description}
                      </p>
                      
                      <div className="bg-gray-50 rounded px-3 py-2 mb-3 hover:bg-gray-100 transition-colors">
                        <div className="text-xs font-medium text-gray-500 mb-1">
                          Resource ID
                        </div>
                        <div className="font-mono text-xs text-gray-900">
                          {rec.resource_id}
                        </div>
                      </div>
                      
                      <div className="bg-emerald-50 rounded px-3 py-2 border border-emerald-200 hover:border-emerald-300 hover:bg-emerald-100 transition-all duration-200">
                        <div className="flex items-center gap-1 mb-1">
                          <CheckCircle className="w-3 h-3 text-emerald-600" />
                          <div className="text-xs font-medium text-emerald-900">
                            Recommended Action
                          </div>
                        </div>
                        <div className="text-sm text-gray-900">
                          {rec.recommended_action}
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-6 text-right min-w-[120px]">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                        Savings
                      </div>
                      <div className="flex items-center justify-end gap-1">
                        <DollarSign className="w-5 h-5 text-emerald-600" />
                        <div className="text-2xl font-semibold text-emerald-600 transition-all duration-500 hover:text-emerald-700">
                          {rec.estimated_savings_monthly?.toFixed(2)}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">per month</div>
                      <div className="mt-2 text-sm font-medium text-gray-900">
                        ${rec.estimated_savings_yearly?.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">per year</div>
                    </div>
                  </div>

                  {rec.metrics_summary && Object.keys(rec.metrics_summary).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="text-xs text-gray-500">
                        {Object.entries(rec.metrics_summary as Record<string, any>).map(([key, value], i) => (
                          <span key={i}>
                            {i > 0 && ' • '}
                            {key}: {typeof value === 'number' ? value.toFixed(2) : String(value ?? '')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="px-6 py-12 text-center animate-fadeIn">
              <CheckCircle className="w-16 h-16 mx-auto mb-3 text-emerald-500" />
              <div className="text-sm font-medium text-gray-900 mb-1">
                All resources optimized
              </div>
              <div className="text-sm text-gray-500">
                No cost-saving opportunities identified at this time
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center animate-fadeIn" style={{ animationDelay: '1000ms' }}>
          <div className="inline-block text-xs text-gray-500">
            Last updated: {summary?.latest_collection 
              ? new Date(summary.latest_collection).toLocaleString()
              : 'N/A'
            }
          </div>
        </div>
      </div>

      {/* Global Styles for Animations */}
      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out forwards;
        }

        .animate-fadeInUp {
          animation: fadeInUp 0.6s ease-out forwards;
          opacity: 0;
        }

        .animate-slideInLeft {
          animation: slideInLeft 0.6s ease-out forwards;
        }

        .animate-slideInRight {
          animation: slideInRight 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}