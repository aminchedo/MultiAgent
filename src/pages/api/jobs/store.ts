export interface JobRecord {
	id: string
	description: string
	createdAt: number
}

// Global store survives dev hot reloads
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = global as any

if (!g.__mockJobsStore) {
	g.__mockJobsStore = new Map<string, JobRecord>()
}

export const jobsStore: Map<string, JobRecord> = g.__mockJobsStore as Map<string, JobRecord>