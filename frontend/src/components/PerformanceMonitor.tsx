import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Activity, HardDrive, Clock, Server, Zap } from 'lucide-react';
import { RecentTasks } from './RecentTasks';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Progress } from '@/components/ui/progress';

interface MemoryStats {
  available: boolean;
  total: number;
  allocated: number;
  free: number;
  utilization: number;
  peak: number;
  system_total: number;
  system_used: number;
  system_free: number;
  system_percent: number;
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

const MetricCard = ({ title, value, icon: Icon, detail, progress }: {
  title: string;
  value: string | number;
  icon: any;
  detail?: string;
  progress?: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <Card className="group relative overflow-hidden rounded-xl border-border/50 bg-gradient-to-br from-black/50 to-black/10 backdrop-blur supports-[backdrop-filter]:bg-background/60 before:pointer-events-none before:absolute before:-inset-px before:rounded-[11px] before:border before:border-white/5 before:bg-[linear-gradient(var(--shine-angle,0deg),transparent_0%,rgba(255,255,255,0.25)_25%,transparent_50%)] before:opacity-0 before:transition-all before:duration-500 hover:before:opacity-100 hover:before:[--shine-angle:170deg] after:absolute after:inset-0 after:rounded-xl after:bg-gradient-to-br after:from-indigo-500/5 after:to-fuchsia-500/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium bg-gradient-to-r from-neutral-200 via-neutral-100/80 to-neutral-300 bg-clip-text text-transparent">{title}</CardTitle>
        <Icon className="h-4 w-4 text-indigo-400/80 animate-pulse" />
      </CardHeader>
      <CardContent>
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 10 }}
          className="text-2xl font-bold bg-gradient-to-r from-neutral-200 via-white to-neutral-300 bg-clip-text text-transparent [text-shadow:_0_1px_5px_rgb(255_255_255_/_10%)]"
        >
          {value}
        </motion.div>
        {detail && (
          <div className="text-xs text-neutral-300/80 mt-1 font-medium">
            {detail}
          </div>
        )}
        {progress !== undefined && (
          <div className="mt-3">
            <Progress 
              value={progress} 
              className="h-2 bg-black/50" 
              indicatorClassName="bg-gradient-to-r from-indigo-500/50 via-fuchsia-500/50 to-indigo-500/50"
            />
            <div className="text-xs text-neutral-300/80 mt-1 font-medium">
              {progress.toFixed(1)}% utilized
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  </motion.div>
);

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

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  const handleUnloadModel = async () => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/unload_model');
      alert(response.data.message);
    } catch (error) {
      alert('Error unloading model: ' + (error as Error).message);
    }
  };

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Zap className="w-8 h-8 text-primary animate-pulse" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ staggerChildren: 0.1 }}
      >
        <MetricCard
          title="GPU Memory"
          value={formatBytes(metrics.memory_stats.allocated)}
          icon={HardDrive}
          detail={`Peak: ${formatBytes(metrics.memory_stats.peak)}`}
          progress={metrics.memory_stats.utilization}
        />

        <MetricCard
          title="Active Tasks"
          value={metrics.active_tasks}
          icon={Activity}
          detail={`Active Agents: ${metrics.active_agents}`}
        />

        <MetricCard
          title="System Status"
          value={metrics.status}
          icon={Server}
          detail={`GPU: ${metrics.memory_stats.available ? 'Available' : 'Not Available'}`}
        />

        <MetricCard
          title="Last Updated"
          value={formatTime(lastUpdated)}
          icon={Clock}
          detail="Auto-refresh every 5s"
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <RecentTasks tasks={metrics.recent_tasks || []} />
      </motion.div>

      <motion.div
        className="flex justify-end"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <button
          onClick={handleUnloadModel}
          className="relative px-4 py-2 rounded-md font-medium text-white bg-gradient-to-r from-red-500/50 to-rose-500/50 hover:from-red-500/60 hover:to-rose-500/60 transition-all duration-200 before:absolute before:inset-0 before:rounded-md before:bg-[linear-gradient(var(--shine-angle,0deg),transparent_0%,rgba(255,255,255,0.25)_25%,transparent_50%)] before:opacity-0 hover:before:opacity-100 hover:before:[--shine-angle:170deg] before:transition-all before:duration-500"
        >
          Unload Model
        </button>
      </motion.div>
    </div>
  );
} 