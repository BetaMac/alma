import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { motion } from 'framer-motion';
import { Clock, Hash, Zap, Type } from 'lucide-react';

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

const TaskCard = ({ task }: { task: Task }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border border-red-500/20';
      case 'processing':
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
      default:
        return 'bg-gray-500/10 text-gray-400 border border-gray-500/20';
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-4 last:mb-0"
    >
      <Card className="group relative overflow-hidden rounded-xl border-border/50 bg-gradient-to-br from-black/50 to-black/10 backdrop-blur supports-[backdrop-filter]:bg-background/60 before:pointer-events-none before:absolute before:-inset-px before:rounded-[11px] before:border before:border-white/5 before:bg-[linear-gradient(var(--shine-angle,0deg),transparent_0%,rgba(255,255,255,0.25)_25%,transparent_50%)] before:opacity-0 before:transition-all before:duration-500 hover:before:opacity-100 hover:before:[--shine-angle:170deg] after:absolute after:inset-0 after:rounded-xl after:bg-gradient-to-br after:from-indigo-500/5 after:to-fuchsia-500/5">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                  {task.status}
                </div>
                <span className="text-xs text-neutral-300/80 font-medium">
                  <Clock className="inline-block w-3 h-3 mr-1 text-neutral-400/80" />
                  {formatTime(task.created_at)}
                </span>
              </div>
              <p className="text-sm text-neutral-300/90 line-clamp-2 font-medium">{task.prompt}</p>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-indigo-400/80" />
                  <div>
                    <div className="text-xs text-neutral-300/80 font-medium">Tokens</div>
                    <div className="text-sm font-medium bg-gradient-to-r from-neutral-200 via-white to-neutral-300 bg-clip-text text-transparent [text-shadow:_0_1px_5px_rgb(255_255_255_/_10%)]">
                      {task.input_tokens || 0} in / {task.output_tokens || 0} out
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-indigo-400/80 animate-pulse" />
                  <div>
                    <div className="text-xs text-neutral-300/80 font-medium">Time</div>
                    <div className="text-sm font-medium bg-gradient-to-r from-neutral-200 via-white to-neutral-300 bg-clip-text text-transparent [text-shadow:_0_1px_5px_rgb(255_255_255_/_10%)]">
                      {task.execution_time ? `${task.execution_time.toFixed(2)}s` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="ml-4">
              <Type className="w-4 h-4 text-indigo-400/80" />
              <span className="text-xs text-neutral-300/80 ml-1 font-medium">{task.type}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export function RecentTasks({ tasks }: { tasks: Task[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="group relative overflow-hidden rounded-xl border-border/50 bg-gradient-to-br from-black/50 to-black/10 backdrop-blur supports-[backdrop-filter]:bg-background/60 before:pointer-events-none before:absolute before:-inset-px before:rounded-[11px] before:border before:border-white/5 before:bg-[linear-gradient(var(--shine-angle,0deg),transparent_0%,rgba(255,255,255,0.25)_25%,transparent_50%)] before:opacity-0 before:transition-all before:duration-500 hover:before:opacity-100 hover:before:[--shine-angle:170deg] after:absolute after:inset-0 after:rounded-xl after:bg-gradient-to-br after:from-indigo-500/5 after:to-fuchsia-500/5">
        <CardHeader>
          <CardTitle className="text-lg font-semibold bg-gradient-to-r from-neutral-200 via-white to-neutral-300 bg-clip-text text-transparent [text-shadow:_0_1px_5px_rgb(255_255_255_/_10%)]">Recent Tasks</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px] pr-4">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
              />
            ))}
          </ScrollArea>
        </CardContent>
      </Card>
    </motion.div>
  );
} 