import { API_URL } from '@/lib/constants';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_URL;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  }

  async uploadFile(endpoint: string, file: File): Promise<{ document_id: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error(`Upload Error: ${response.statusText}`);
    return response.json();
  }

  async getAccents(): Promise<{ accents: Array<{ code: string; name: string; region: string }> }> {
    return this.get('/api/accents');
  }

  async updateSession(sessionId: string, data: { accent?: string; gender?: string }): Promise<void> {
    return this.post(`/api/sessions/${sessionId}/update`, data);
  }

  async getConversationHistory(sessionId: string): Promise<{ messages: Array<{ role: string; content: string }> }> {
    return this.get(`/api/conversations/${sessionId}`);
  }
}

export const apiService = new ApiService();