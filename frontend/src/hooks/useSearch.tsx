import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/types/store';
import { 
  setQuery, 
  setPage, 
  setFilters, 
  addRecentSearch,
  resetSearch 
} from '@/store/slices/searchSlice';
import { 
  useSearchResultsQuery, 
  useLazySearchResultsQuery 
} from '@/store/api/searchApi';

export const useSearch = () => {
  const dispatch = useAppDispatch();
  const { searchParams, recentSearches, filters } = useAppSelector(state => state.search);
  
  // Auto-trigger search when searchParams change
  const { data, error, isLoading, isFetching } = useSearchResultsQuery(
    searchParams,
    { skip: !searchParams.query }
  );
  
  // Manual search trigger
  const [triggerSearch] = useLazySearchResultsQuery();
  
  const search = useCallback((query: string) => {
    if (query.trim()) {
      dispatch(setQuery(query));
      dispatch(addRecentSearch(query));
    }
  }, [dispatch]);
  
  const changePage = useCallback((page: number) => {
    dispatch(setPage(page));
  }, [dispatch]);
  
  const updateFilters = useCallback((newFilters: Partial<typeof filters>) => {
    dispatch(setFilters(newFilters));
  }, [dispatch]);
  
  const reset = useCallback(() => {
    dispatch(resetSearch());
  }, [dispatch]);
  
  return {
    // Data
    results: data?.results || [],
    total: data?.total || 0,
    pagination: {
      page: data?.page || 1,
      limit: data?.limit || 10,
      totalPages: data?.totalPages || 0,
    },
    suggestions: data?.suggestions || [],
    recentSearches,
    filters,
    
    // States
    isLoading,
    isFetching,
    error,
    
    // Actions
    search,
    changePage,
    updateFilters,
    reset,
    triggerSearch,
  };
};