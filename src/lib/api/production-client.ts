// Production API client configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export class ProductionClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? API_BASE_URL;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // If expecting blob (download), caller uses fetch directly
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check
  async health(): Promise<{ status: string }> {
    return this.request('/api/health');
  }

  // Login endpoint
  async login(credentials: { username: string; password: string }): Promise<any> {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  // Generate endpoint
  async generate(prompt: string): Promise<{ job_id: string }> {
    return this.request('/api/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  // Create vibe job endpoint
  async createVibeJob(vibe: string, options: any = {}): Promise<{ data: { id: string }, error?: string }> {
    const response = await this.request<{ job_id: string }>('/api/generate', {
      method: 'POST',
      body: JSON.stringify({ 
        prompt: vibe,
        ...options 
      }),
    });
    
    return {
      data: { id: response.job_id },
      error: undefined
    };
  }

  // Status endpoint
  async status(jobId: string): Promise<{ status: string; result?: any }> {
    return this.request(`/api/status/${jobId}`);
  }

  // Get job status endpoint (alias for status)
  async getJobStatus(jobId: string): Promise<{ data: any, error?: string }> {
    try {
      const response = await this.request(`/api/status/${jobId}`);
      return {
        data: response,
        error: undefined
      };
    } catch (error: any) {
      return {
        data: null,
        error: error.message || 'Failed to fetch job status'
      };
    }
  }

  // Download endpoint
  async download(jobId: string): Promise<Blob> {
    const url = `${this.baseUrl}/api/download/${jobId}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.blob();
  }

  // Download job endpoint (alias for download)
  async downloadJob(jobId: string): Promise<{ data: Blob, error?: string }> {
    try {
      const blob = await this.download(jobId);
      return {
        data: blob,
        error: undefined
      };
    } catch (error: any) {
      return {
        data: null as any,
        error: error.message || 'Failed to download project'
      };
    }
  }
}

// Export a default instance
export const productionClient = new ProductionClient();
export const apiClient = productionClient; // Alias for compatibility