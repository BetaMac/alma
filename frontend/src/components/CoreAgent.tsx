'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';

const CoreAgent = () => {
  const [input, setInput] = useState('');
  const [taskType, setTaskType] = useState('creative');
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [error, setError] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);

  // Initialize WebSocket connection with handlers
  const { isConnected, sendMessage } = useWebSocket('ws://127.0.0.1:8000/ws/default', {
    onOpen: () => {
      console.log('Connected to agent backend');
      setError('');
    },
    onClose: () => {
      setError('Connection to agent lost. Attempting to reconnect...');
    },
    onMessage: (message: WebSocketMessage) => {
      switch (message.status) {
        case 'processing':
          setStatus('loading');
          break;
        case 'chunk':
          setResponse(prev => prev + message.data);
          break;
        case 'complete':
          setResponse(message.data);
          setStatus('success');
          break;
        case 'error':
          setError(message.message || 'An error occurred');
          setStatus('error');
          break;
        case 'finished':
          if (message.elapsedTime) setElapsedTime(message.elapsedTime);
          break;
      }
    },
    onError: () => {
      setError('Connection error occurred');
      setStatus('error');
    }
  });

  const handleSubmit = async () => {
    if (!input.trim() || !isConnected) return;

    setStatus('loading');
    setError('');
    setResponse('');
    setElapsedTime(0);

    try {
      // Send task to backend
      const taskData = {
        input,
        taskType,
        timestamp: new Date().toISOString()
      };

      // First, initiate the task via REST API
      const response = await fetch('http://127.0.0.1:8000/api/agent/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        throw new Error('Failed to initiate task');
      }

      // Then notify WebSocket about the task
      sendMessage(taskData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStatus('error');
    }
  };

  const getStatusDisplay = () => {
    if (!isConnected && status !== 'success') {
      return (
        <Alert className="mt-4 bg-yellow-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Connecting to agent...</AlertDescription>
        </Alert>
      );
    }

    const statusConfig = {
      loading: {
        icon: <Clock className="h-4 w-4 animate-spin" />,
        message: `Processing... (${elapsedTime}s)`,
        color: 'bg-blue-50'
      },
      error: {
        icon: <AlertCircle className="h-4 w-4" />,
        message: error,
        color: 'bg-red-50'
      },
      success: {
        icon: <CheckCircle className="h-4 w-4" />,
        message: `Completed in ${elapsedTime} seconds`,
        color: 'bg-green-50'
      }
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    if (!config) return null;

    return (
      <Alert className={`mt-4 ${config.color}`}>
        <div className="flex items-center gap-2">
          {config.icon}
          <AlertDescription>{config.message}</AlertDescription>
        </div>
      </Alert>
    );
  };

  const expectedDuration = taskType === 'creative' ? '~30 seconds' : '~10 minutes';

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>AI Learning Agent Interface</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4 items-start">
          <div className="flex-1">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your task or query..."
              className="min-h-32"
            />
          </div>
          <div className="w-48">
            <Select value={taskType} onValueChange={setTaskType}>
              <SelectTrigger>
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="creative">Creative Task ({expectedDuration})</SelectItem>
                <SelectItem value="analytical">Analytical Task ({expectedDuration})</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              onClick={handleSubmit}
              disabled={status === 'loading' || !input.trim() || !isConnected}
              className="w-full mt-2"
            >
              Process Task
            </Button>
          </div>
        </div>

        {getStatusDisplay()}

        {response && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <pre className="whitespace-pre-wrap">{response}</pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CoreAgent;