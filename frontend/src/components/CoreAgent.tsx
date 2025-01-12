"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Clock, CheckCircle, RefreshCcw, Terminal } from 'lucide-react';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';
import { wsManager } from '@/lib/websocketManager';
import { PerformanceMonitor } from './PerformanceMonitor';
// Removed the import for Progress due to the error

const CoreAgent = () => {
  const [input, setInput] = useState('');
  const [taskType, setTaskType] = useState('creative');
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [progress, setProgress] = useState(0);

  // Timer for elapsed time
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (status === 'loading') {
      timer = setInterval(() => {
        setElapsedTime(prev => {
          const newElapsedTime = prev + 1;
          const expectedDuration = taskType === 'creative' ? 30 : 60;
          setProgress(Math.min((newElapsedTime / expectedDuration) * 100, 99));
          return newElapsedTime;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [status, taskType]);
  // Initialize WebSocket connection with enhanced handlers
  const { isConnected, sendMessage } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/', {
    onOpen: () => {
      console.log('Connected to agent backend');
      setError('');
      setIsReconnecting(false);
      setReconnectAttempts(0);
    },
    onClose: () => {
      console.log('WebSocket connection closed');
      if (!isReconnecting) {
        setIsReconnecting(true);
        setReconnectAttempts(prev => prev + 1);
        if (reconnectAttempts < 3) {
          handleReconnect();
        } else {
          setError('Connection lost after multiple attempts. Please refresh the page.');
        }
      }
    },
    onMessage: (message: WebSocketMessage) => {
      try {
        switch (message.status) {
          case 'processing':
            setStatus('loading');
            break;
          case 'chunk':
            setResponse(prev => prev + (message.data || ''));
            break;
          case 'complete':
            setResponse(prev => prev + (message.data || ''));
            setStatus('success');
            setProgress(100);
            break;
          case 'error':
            setError(message.message || 'An error occurred');
            setStatus('error');
            break;
          case 'finished':
            if (message.elapsedTime) setElapsedTime(message.elapsedTime);
            break;
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
        setError('Error processing response');
        setStatus('error');
      }
    },
    onError: (event: Event) => {
      console.error('WebSocket error:', event);
      setError('Connection error occurred. Check if the backend server is running.');
      setStatus('error');
      handleReconnect();
    }
  });

  const handleReconnect = useCallback(() => {
    setIsReconnecting(true);
    setReconnectAttempts(0);
    setError('');
    // Use the WebSocket manager's reconnect method
    wsManager.reconnect();
  }, []);

  const handleSubmit = async () => {
    if (!input.trim() || !isConnected) return;

    setStatus('loading');
    setError('');
    setResponse('');
    setElapsedTime(0);
    setProgress(0);

    try {
      const taskData = {
        input,
        taskType,
        timestamp: new Date().toISOString()
      };

      const response = await fetch('http://127.0.0.1:8000/api/agent/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to initiate task');
      }

      sendMessage(taskData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStatus('error');
    }
  };

  const expectedDuration = taskType === 'creative' ? '~30 seconds' : '~60 seconds';

  const renderStatus = () => {
    if (!isConnected && status !== 'success') {
      return (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <div className="text-lg font-semibold">Connection Error</div>
          <div className="flex items-center gap-2">
            {error || 'Unable to connect to agent backend'}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleReconnect}
              disabled={isReconnecting}
              className="ml-2"
            >
              <RefreshCcw className={`h-4 w-4 mr-2 ${isReconnecting ? 'animate-spin' : ''}`} />
              Reconnect
            </Button>
          </div>
        </Alert>
      );
    }

    if (status === 'loading') {
      return (
        <div className="mt-4 space-y-2">
          <Alert className="bg-blue-50">
            <Clock className="h-4 w-4 animate-spin" />
            <AlertDescription>
              Processing... ({elapsedTime}s elapsed)
              <div className="text-xs text-gray-500">
                Expected duration: {taskType === 'creative' ? '~30 seconds' : '~60 seconds'}
              </div>
            </AlertDescription>
          </Alert>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      );
    }

    if (status === 'error') {
      return (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      );
    }

    if (status === 'success') {
      return (
        <Alert className="mt-4 bg-green-50">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>Completed in {elapsedTime} seconds</AlertDescription>
        </Alert>
      );
    }

    return null;
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Terminal className="h-6 w-6" />
          AI Learning Agent Interface
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4 items-start">
          <div className="flex-1">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your task or query..."
              className="min-h-32 font-mono"
              disabled={status === 'loading'}
            />
          </div>
          <div className="w-48">
            <Select value={taskType} onValueChange={setTaskType}>
              <SelectTrigger>
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="creative">Creative (~30s)</SelectItem>
                <SelectItem value="analytical">Analytical (~60s)</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              onClick={handleSubmit}
              disabled={status === 'loading' || !input.trim() || !isConnected}
              className="w-full mt-2"
            >
              {status === 'loading' ? 'Processing...' : 'Process Task'}
            </Button>
          </div>
        </div>

        {renderStatus()}

        {response && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <pre className="whitespace-pre-wrap font-mono text-sm">{response}</pre>
          </div>
        )}

        <div className="mt-8">
          <PerformanceMonitor />
        </div>
      </CardContent>
    </Card>
  );
};

export default CoreAgent;