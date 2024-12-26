import dynamic from 'next/dynamic'

const CoreAgent = dynamic(() => import('../components/CoreAgent'), {
  ssr: false
})

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <CoreAgent />
    </main>
  )
}