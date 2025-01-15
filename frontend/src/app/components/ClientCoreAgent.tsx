'use client'

import dynamic from 'next/dynamic'

const CoreAgent = dynamic(() => import('../../components/CoreAgent'), {
  ssr: false
})

export default function ClientCoreAgent() {
  return <CoreAgent />
} 