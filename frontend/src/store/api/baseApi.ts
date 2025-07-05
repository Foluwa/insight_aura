import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { ApiError } from '../types/api';

// Define your API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.insightaura.duckdns.org/';

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      headers.set('Content-Type', 'application/json');
      // Add any default headers here
      return headers;
    },
  }),
  tagTypes: ['Search', 'Results'],
  endpoints: () => ({}),
});

// Error handling utility
export const isApiError = (error: any): error is { data: ApiError } => {
  return error?.data && typeof error.data.message === 'string';
};