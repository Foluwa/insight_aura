import { baseApi } from './baseApi';
import type { SearchParams, SearchResponse, ApiResponse } from '../types/api';

export const searchApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Search endpoint
    searchResults: builder.query<SearchResponse, SearchParams>({
      query: ({ query, page = 1, limit = 10, category, sortBy, sortOrder }) => ({
        url: '/search',
        params: {
          q: query,
          page,
          limit,
          ...(category && { category }),
          ...(sortBy && { sortBy }),
          ...(sortOrder && { sortOrder }),
        },
      }),
      providesTags: (result, error, { query }) => [
        { type: 'Search', id: query },
        'Search',
      ],
      transformResponse: (response: ApiResponse<SearchResponse>) => response.data,
    }),

    // Get search suggestions
    getSearchSuggestions: builder.query<string[], string>({
      query: (query) => ({
        url: '/search/suggestions',
        params: { q: query },
      }),
      transformResponse: (response: ApiResponse<string[]>) => response.data,
    }),

    // Get categories
    getCategories: builder.query<string[], void>({
      query: () => '/search/categories',
      transformResponse: (response: ApiResponse<string[]>) => response.data,
    }),
  }),
});

export const {
  useSearchResultsQuery,
  useLazySearchResultsQuery,
  useGetSearchSuggestionsQuery,
  useGetCategoriesQuery,
} = searchApi;