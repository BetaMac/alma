import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Activity, HardDrive, Clock, Server } from 'lucide-react';
import { RecentTasks } from './RecentTasks';

interface MemoryStats {
  available: boolean;
  total: number;
  reserved: number;
  allocated: number;
  free: number;
  utilization: number;
}

interface Task {
  id: string;
  type: string;
  status: string;
  input_tokens: number;
  output_tokens: number;
  execution_time: number;
  created_at: number;
  prompt: string;
}

interface SystemMetrics {
  memory_stats: MemoryStats;
  active_tasks: number;
  active_agents: number;
  task_statistics: Record<string, number>;
  status: string;
  recent_tasks: Task[];
}

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/metrics');
        const data = await response.json();
        setMetrics(data);
        setLastUpdated(new Date());
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    // Initial fetch
    fetchMetrics();

    // Set up polling every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatBytes = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  if (!metrics) {
    return <div>Loading metrics...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Memory Usage Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.memory_stats.utilization.toFixed(1)}%</div>
            <div className="text-xs text-muted-foreground">
              Free: {formatBytes(metrics.memory_stats.free)}
            </div>
            <div className="mt-4 h-2 w-full bg-secondary rounded-full">
              <div
                className="h-2 bg-primary rounded-full transition-all duration-500"
                style={{ width: `${metrics.memory_stats.utilization}%` }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Active Tasks Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.active_tasks}</div>
            <div className="text-xs text-muted-foreground">
              Agents: {metrics.active_agents}
            </div>
            <div className="mt-4 space-y-2">
              {Object.entries(metrics.task_statistics).map(([status, count]) => (
                <div key={status} className="text-xs flex justify-between">
                  <span className="capitalize">{status}</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Status Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{metrics.status}</div>
            <div className="text-xs text-muted-foreground">
              GPU: {metrics.memory_stats.available ? 'Available' : 'Not Available'}
            </div>
          </CardContent>
        </Card>

        {/* Last Updated Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatTime(lastUpdated)}</div>
            <div className="text-xs text-muted-foreground">
              Auto-refresh every 5s
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tasks and Token Usage */}
      <RecentTasks tasks={metrics.recent_tasks || []} />
    </div>
  );
} 