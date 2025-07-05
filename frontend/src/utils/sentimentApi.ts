export interface AnalysisRequest {
  platform: 'appstore' | 'playstore' | 'youtube';
  searchTerm: string;
  options: {
    includeRecentReviews: boolean;
    enableAiInsights: boolean;
    includeCompetitorComparison: boolean;
  };
}

export interface AnalysisResponse {
  success: boolean;
  data?: {
    sentimentData: any;
    statsData: any;
    insightsData: any;
    reviewsData: any;
  };
  error?: string;
}

export const analyzeApp = async (request: AnalysisRequest): Promise<AnalysisResponse> => {
  try {
    // This would be your actual API call
    const response = await fetch('/api/sentiment/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Analysis failed');
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
};

export const validateInput = (platform: string, searchTerm: string): boolean => {
  if (!searchTerm.trim()) return false;
  
  switch (platform) {
    case 'youtube':
      return searchTerm.includes('youtube.com') || searchTerm.includes('youtu.be');
    case 'playstore':
      return searchTerm.length > 2;
    case 'appstore':
      return searchTerm.length > 2;
    default:
      return false;
  }
};