import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { SearchParams } from '../types/api';

interface SearchState {
  currentQuery: string;
  searchParams: SearchParams;
  recentSearches: string[];
  filters: {
    category: string;
    sortBy: 'relevance' | 'date' | 'title';
    sortOrder: 'asc' | 'desc';
  };
}

const initialState: SearchState = {
  currentQuery: '',
  searchParams: {
    query: '',
    page: 1,
    limit: 10,
  },
  recentSearches: [],
  filters: {
    category: '',
    sortBy: 'relevance',
    sortOrder: 'desc',
  },
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setQuery: (state, action: PayloadAction<string>) => {
      state.currentQuery = action.payload;
      state.searchParams.query = action.payload;
      state.searchParams.page = 1; // Reset to first page on new search
    },
    
    setPage: (state, action: PayloadAction<number>) => {
      state.searchParams.page = action.payload;
    },
    
    setFilters: (state, action: PayloadAction<Partial<SearchState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.searchParams = {
        ...state.searchParams,
        category: state.filters.category,
        sortBy: state.filters.sortBy,
        sortOrder: state.filters.sortOrder,
        page: 1, // Reset to first page when filters change
      };
    },
    
    addRecentSearch: (state, action: PayloadAction<string>) => {
      const query = action.payload.trim();
      if (query && !state.recentSearches.includes(query)) {
        state.recentSearches.unshift(query);
        if (state.recentSearches.length > 10) {
          state.recentSearches.pop();
        }
      }
    },
    
    clearRecentSearches: (state) => {
      state.recentSearches = [];
    },
    
    resetSearch: (state) => {
      state.currentQuery = '';
      state.searchParams = { ...initialState.searchParams };
      state.filters = { ...initialState.filters };
    },
  },
});

export const {
  setQuery,
  setPage,
  setFilters,
  addRecentSearch,
  clearRecentSearches,
  resetSearch,
} = searchSlice.actions;

export default searchSlice.reducer;