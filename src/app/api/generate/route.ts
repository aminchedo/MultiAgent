import { NextRequest, NextResponse } from 'next/server'

// Simple in-memory job store using a global to persist across route calls during dev
interface JobRecord {
  id: string
  description: string
  createdAt: number
}

declare global {
  // eslint-disable-next-line no-var
  var __jobsStore: Map<string, JobRecord> | undefined
}

function getJobsStore(): Map<string, JobRecord> {
  if (!globalThis.__jobsStore) {
    globalThis.__jobsStore = new Map<string, JobRecord>()
  }
  return globalThis.__jobsStore
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}))
    const description: string = body?.prompt || body?.description || 'AI generated project'

    const id = `job_${Math.random().toString(36).slice(2, 10)}`
    const createdAt = Date.now()

    const job: JobRecord = { id, description, createdAt }
    getJobsStore().set(id, job)

    return NextResponse.json({ job_id: id })
  } catch (error: any) {
    return NextResponse.json({ error: error?.message || 'Failed to create job' }, { status: 500 })
  }
}