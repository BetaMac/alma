import React from 'react';
import CoreAgent from './components/CoreAgent';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          ALMA - AI Learning Manager Assistant
        </h1>
        <CoreAgent />
      </div>
    </div>
  );
}

export default App;