const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type FileItem = {
  id: string;
  title: string;
  original_name: string;
  mime_type: string;
  size: number;
  processing_status: string;
  scan_status: string | null;
  scan_details: string | null;
  metadata_json: Record<string, unknown> | null;
  requires_attention: boolean;
  created_at: string;
  updated_at: string;
};

export type AlertItem = {
  id: number;
  file_id: string;
  level: string;
  message: string;
  created_at: string;
};

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getFiles(): Promise<FileItem[]> {
    return this.request<FileItem[]>("/files", { cache: "no-store" });
  }

  async getAlerts(): Promise<AlertItem[]> {
    return this.request<AlertItem[]>("/alerts", { cache: "no-store" });
  }

  async getFile(fileId: string): Promise<FileItem> {
    return this.request<FileItem>(`/files/${fileId}`);
  }

  async createFile(title: string, file: File): Promise<FileItem> {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/files`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to create file: ${response.statusText}`);
    }

    return response.json();
  }

  async updateFile(fileId: string, title: string): Promise<FileItem> {
    return this.request<FileItem>(`/files/${fileId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.request<void>(`/files/${fileId}`, {
      method: "DELETE",
    });
  }

  getDownloadUrl(fileId: string): string {
    return `${this.baseUrl}/files/${fileId}/download`;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
