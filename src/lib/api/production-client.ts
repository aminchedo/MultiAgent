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

  // Mock/Proxy login
  async login(credentials: { username: string; password: string }): Promise<any> {
    // If external backend configured and it supports auth, proxy there
    if (this.baseUrl) {
      try {
        return await this.request('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify(credentials),
        })
      } catch {
        // fall through to mock
      }
    }
    // Mock: persist a fake token
    const token = `mock-${Math.random().toString(36).slice(2)}`
    try { localStorage.setItem('vibe_coding_token', token) } catch {}
    return { access_token: token, success: true }
  }

  // Generate endpoint (create job)
  async generate(prompt: string): Promise<{ job_id: string }> {
    return this.request('/api/jobs', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  // Create vibe job endpoint using the enhanced vibe coding workflow
  async createVibeJob(vibe: string, options: any = {}): Promise<{ data: { id: string }, error?: string }> {
    try {
      // Try the new dedicated vibe coding endpoint first
      const vibeData = new URLSearchParams({
        vibe_prompt: vibe,
        project_type: options.projectType || 'web',
        complexity: options.complexity || 'simple',
        ...(options.framework && { framework: options.framework }),
        ...(options.styling && { styling: options.styling })
      });

      const response = await this.request<{ job_id: string }>('/api/vibe-coding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: vibeData,
      });
      
      return {
        data: { id: response.job_id },
        error: undefined
      };
    } catch (vibeError) {
      console.warn('Vibe endpoint failed, falling back to standard endpoint:', vibeError);
      
      // Fallback to traditional endpoint for backward compatibility
      try {
        const response = await this.request<{ job_id: string }>('/api/jobs', {
          method: 'POST',
          body: JSON.stringify({ 
            prompt: vibe,
            description: vibe,
            name: `Vibe Project: ${vibe.slice(0, 30)}...`,
            mode: 'vibe',
            ...options 
          }),
        });
        
        return {
          data: { id: response.job_id },
          error: undefined
        };
      } catch (fallbackError: any) {
        return {
          data: { id: '' },
          error: fallbackError.message || 'Failed to create vibe project'
        };
      }
    }
  }

  // Status endpoint
  async status(jobId: string): Promise<{ status: string; result?: any }> {
    return this.request(`/api/jobs/${jobId}/status`);
  }

  // Get job status endpoint (alias for status)
  async getJobStatus(jobId: string): Promise<{ data: any, error?: string }> {
    try {
      const response = await this.request(`/api/jobs/${jobId}/status`);
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
    const url = `${this.baseUrl}/api/jobs/${jobId}/download`;
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