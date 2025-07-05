// Base API response structure
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Search related types
export interface SearchResult {
  id: string;
  title: string;
  description: string;
  url?: string;
  imageUrl?: string;
  createdAt: string;
  category: string;
  tags: string[];
}

export interface SearchParams {
  query: string;
  page?: number;
  limit?: number;
  category?: string;
  sortBy?: 'relevance' | 'date' | 'title';
  sortOrder?: 'asc' | 'desc';
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  suggestions?: string[];
}

// Error response
export interface ApiError {
  status: number;
  message: string;
  errors?: Record<string, string[]>;
}