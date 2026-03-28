'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// API Base URL - your EC2 server
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
      
      console.log('Metrics data:', metricsData); // Debug log
      
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
        // No data or wrong format
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
            <div className="text-2xl font-bold text-gray-600">
              {cpuData.length > 0 ? cpuData[cpuData.length - 1].cpu.toFixed(2) : '0.00'}%
            </div>
          </div>
          <div className="border-l-4 border-green-500 pl-4">
            <div className="text-sm text-gray-600">Average CPU (Today)</div>
            <div className="text-2xl font-bold text-gray-600">
              {cpuData.length > 0 
                ? (cpuData.reduce((sum, d) => sum + d.cpu, 0) / cpuData.length).toFixed(2)
                : '0.00'
              }%
            </div>
          </div>
          <div className="border-l-4 border-orange-500 pl-4">
            <div className="text-sm text-gray-600">Peak CPU (Today)</div>
            <div className="text-2xl font-bold text-gray-600">
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
              <div className="text-lg font-bold truncate text-gray-600">
                {s3Data.resource_id}
              </div>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <div className="text-sm text-gray-600">Total Size</div>
              <div className="text-2xl font-bold text-gray-600">
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
              <div className="text-2xl font-bold text-gray-600">
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