'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Fetch summary
      const summaryRes = await fetch(`${API_URL}/api/metrics/summary`);
      if (!summaryRes.ok) {
        throw new Error('Failed to fetch summary');
      }
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Fetch EC2 metrics (last 24 hours)
      const today = new Date().toISOString().split('T')[0];
      const metricsRes = await fetch(
        `${API_URL}/api/metrics/ec2/i-03fcdfc149b765c98?start_date=${today}&limit=24`
      );
      
      if (!metricsRes.ok) {
        throw new Error('Failed to fetch metrics');
      }
      
      const metricsData = await metricsRes.json();
      
      console.log('Metrics data:', metricsData);
      
      // Check if items exists and is an array
      if (metricsData.items && Array.isArray(metricsData.items)) {
        // Transform data for chart
        const chartData = metricsData.items.map((item: any) => ({
          timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          cpu: parseFloat(item.metrics.CPUUtilization_Average)
        })).reverse();

        setCpuData(chartData);
      } else {
        console.warn('No items in response or wrong format:', metricsData);
        setCpuData([]);
      }

      // Fetch S3 metrics
      const s3Res = await fetch(`${API_URL}/api/metrics/s3?limit=1`);
      if (s3Res.ok) {
        const s3ResData = await s3Res.json();
        if (s3ResData.items && s3ResData.items.length > 0) {
          setS3Data(s3ResData.items[0]);
        }
      }

      // Fetch cost summary
      const costRes = await fetch(`${API_URL}/api/metrics/costs/summary?days=7`);
      if (costRes.ok) {
        const costData = await costRes.json();
        setCostSummary(costData);
      }

      // Fetch recommendations
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
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">
          AWS Cost Optimizer Dashboard
        </h1>
        <p className="text-gray-600 mt-2">
          Real-time monitoring and cost optimization
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Total Metrics</div>
          <div className="text-3xl font-bold text-blue-600">
            {summary?.total_metrics || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">EC2 Metrics</div>
          <div className="text-3xl font-bold text-green-600">
            {summary?.ec2_metrics_count || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">S3 Metrics</div>
          <div className="text-3xl font-bold text-purple-600">
            {summary?.s3_metrics_count || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Status</div>
          <div className="text-xl font-bold text-green-500 flex items-center">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            {summary?.status || 'Active'}
          </div>
        </div>
      </div>

      {/* CPU Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          EC2 CPU Usage - Today
        </h2>
        <div className="text-sm text-gray-600 mb-4">
          Instance: i-03fcdfc149b765c98 (t3.micro)
        </div>
        
        {cpuData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis 
                label={{ value: 'CPU %', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="cpu" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="CPU Usage (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center text-gray-500 py-12">
            No data available for today
          </div>
        )}
      </div>

      {/* Current Stats */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Current Performance
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border-l-4 border-blue-500 pl-4">
            <div className="text-sm text-gray-600">Current CPU</div>
            <div className="text-2xl font-bold">
              {cpuData.length > 0 ? cpuData[cpuData.length - 1].cpu.toFixed(2) : '0.00'}%
            </div>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <div className="text-sm text-gray-600">Average CPU (Today)</div>
            <div className="text-2xl font-bold">
              {cpuData.length > 0 
                ? (cpuData.reduce((sum, d) => sum + d.cpu, 0) / cpuData.length).toFixed(2)
                : '0.00'
              }%
            </div>
          </div>
          <div className="border-l-4 border-orange-500 pl-4">
            <div className="text-sm text-gray-600">Peak CPU (Today)</div>
            <div className="text-2xl font-bold">
              {cpuData.length > 0 
                ? Math.max(...cpuData.map(d => d.cpu)).toFixed(2)
                : '0.00'
              }%
            </div>
          </div>
        </div>
      </div>

      {/* S3 Storage Metrics */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          S3 Storage Metrics
        </h2>
        
        {s3Data ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-l-4 border-purple-500 pl-4">
              <div className="text-sm text-gray-600">Bucket Name</div>
              <div className="text-lg font-bold truncate">
                {s3Data.resource_id}
              </div>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <div className="text-sm text-gray-600">Total Size</div>
              <div className="text-2xl font-bold">
                {s3Data.metrics?.BucketSizeBytes 
                  ? (s3Data.metrics.BucketSizeBytes / 1024).toFixed(2) 
                  : s3Data.BucketSizeBytes 
                  ? (s3Data.BucketSizeBytes / 1024).toFixed(2)
                  : '0.00'
                } KB
              </div>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <div className="text-sm text-gray-600">Total Objects</div>
              <div className="text-2xl font-bold">
                {s3Data.metrics?.NumberOfObjects || s3Data.NumberOfObjects || 0}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No S3 metrics available yet
          </div>
        )}
      </div>

      {/* Cost Summary */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          💰 Cost Analysis (Last 7 Days)
        </h2>
        
        {costSummary ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="border-l-4 border-green-500 pl-4">
              <div className="text-sm text-gray-600">Total Cost</div>
              <div className="text-3xl font-bold text-gray-900">
                ${costSummary.total_cost?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {costSummary.days_analyzed} days
              </div>
            </div>
            
            <div className="border-l-4 border-blue-500 pl-4">
              <div className="text-sm text-gray-600">Daily Average</div>
              <div className="text-2xl font-bold text-gray-900">
                ${costSummary.average_daily_cost?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                per day
              </div>
            </div>
            
            <div className="border-l-4 border-orange-500 pl-4">
              <div className="text-sm text-gray-600">EC2 Costs</div>
              <div className="text-2xl font-bold text-gray-900">
                ${costSummary.ec2_total?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {costSummary.total_cost > 0 ? ((costSummary.ec2_total / costSummary.total_cost) * 100).toFixed(0) : '0'}% of total
              </div>
            </div>
            
            <div className="border-l-4 border-purple-500 pl-4">
              <div className="text-sm text-gray-600">S3 Costs</div>
              <div className="text-2xl font-bold text-gray-900">
                ${costSummary.s3_total?.toFixed(4) || '0.0000'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {costSummary.total_cost > 0 && costSummary.s3_total > 0 ? ((costSummary.s3_total / costSummary.total_cost) * 100).toFixed(1) : '0'}% of total
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            Loading cost data...
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          💡 Cost Optimization Recommendations
        </h2>
        
        {recommendations.length > 0 ? (
          <div className="space-y-4">
            {/* Total Savings Card */}
            <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-green-900">
                    Potential Savings Available
                  </h3>
                  <p className="text-sm text-green-700">
                    {recommendations.length} optimization {recommendations.length === 1 ? 'opportunity' : 'opportunities'} found
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-green-600">
                    ${recommendations.reduce((sum, r) => sum + (r.estimated_savings_monthly || 0), 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-green-700">per month</div>
                  <div className="text-xs text-green-600">
                    ${(recommendations.reduce((sum, r) => sum + (r.estimated_savings_monthly || 0), 0) * 12).toFixed(2)}/year
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation Cards */}
            {recommendations.map((rec, index) => (
              <div 
                key={rec.recommendation_id || index}
                className={`border-l-4 p-4 rounded-r-lg ${
                  rec.severity === 'high' ? 'border-red-500 bg-red-50' :
                  rec.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                  'border-blue-500 bg-blue-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        rec.severity === 'high' ? 'bg-red-200 text-red-800' :
                        rec.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {rec.severity?.toUpperCase()}
                      </span>
                      <span className="px-2 py-1 rounded text-xs font-semibold bg-gray-200 text-gray-700">
                        {rec.resource_type}
                      </span>
                    </div>
                    
                    <h3 className="font-bold text-lg text-gray-900 mb-1">
                      {rec.title}
                    </h3>
                    
                    <p className="text-sm text-gray-700 mb-2">
                      {rec.description}
                    </p>
                    
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Resource:</span>
                        <span className="font-mono text-gray-900 ml-1">
                          {rec.resource_id?.substring(0, 20)}...
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                      <div className="text-sm font-semibold text-gray-700 mb-1">
                        ✅ Recommended Action:
                      </div>
                      <div className="text-sm text-gray-900">
                        {rec.recommended_action}
                      </div>
                    </div>
                  </div>
                  
                  <div className="ml-6 text-right">
                    <div className="text-2xl font-bold text-green-600">
                      ${rec.estimated_savings_monthly?.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-600">per month</div>
                    <div className="text-sm font-semibold text-green-700 mt-1">
                      ${rec.estimated_savings_yearly?.toFixed(2)}/year
                    </div>
                  </div>
                </div>

                {rec.metrics_summary && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-xs text-gray-600">
                      Metrics: {Object.entries(rec.metrics_summary).map(([key, value]) => 
                        `${key}: ${typeof value === 'number' ? value.toFixed(2) : value}`
                      ).join(' | ')}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✅</div>
            <div className="text-xl font-semibold text-gray-700 mb-2">
              All Resources Optimized!
            </div>
            <div className="text-gray-500">
              No cost-saving recommendations at this time
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        Last updated: {summary?.latest_collection 
          ? new Date(summary.latest_collection).toLocaleString()
          : 'N/A'
        }
      </div>
    </div>
  );
}