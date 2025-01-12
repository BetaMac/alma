import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { History, Cpu } from 'lucide-react';

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

interface RecentTasksProps {
  tasks: Task[];
}

export function RecentTasks({ tasks }: RecentTasksProps) {
  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const formatDuration = (seconds: number) => {
    return `${seconds.toFixed(1)}s`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Recent Tasks List */}
      <Card className="col-span-1">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Recent Tasks</CardTitle>
          <History className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px] pr-4">
            {tasks.map((task) => (
              <div key={task.id} className="mb-4 p-3 bg-muted/50 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium capitalize">{task.type}</div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    task.status === 'completed' ? 'bg-green-100 text-green-800' :
                    task.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {task.status}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground mb-2 line-clamp-2">
                  {task.prompt}
                </div>
                <div className="text-xs text-muted-foreground flex justify-between">
                  <span>{formatTime(task.created_at)}</span>
                  <span>{formatDuration(task.execution_time)}</span>
                </div>
              </div>
            ))}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Token Usage Stats */}
      <Card className="col-span-1">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Token Usage</CardTitle>
          <Cpu className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="p-3 bg-muted/50 rounded-lg">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium">Input</span>
                    <span>{task.input_tokens} tokens</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Output</span>
                    <span>{task.output_tokens} tokens</span>
                  </div>
                  <div className="mt-2 h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500"
                      style={{
                        width: `${(task.input_tokens / (task.input_tokens + task.output_tokens)) * 100}%`
                      }}
                    />
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground text-right">
                    Total: {task.input_tokens + task.output_tokens} tokens
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
} 