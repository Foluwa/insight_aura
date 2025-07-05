export interface SentimentData {
  positive: number[];
  negative: number[];
  neutral: number[];
}

export interface StatCardData {
  value: string;
  label: string;
  change: string;
  changeType: 'positive' | 'negative';
  icon: string;
  type: 'positive' | 'negative' | 'neutral' | 'total';
}

export interface ReviewData {
  id: string;
  user: string;
  avatar: string;
  rating: number;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  date: string;
}

export interface InsightData {
  id: string;
  type: 'critical' | 'warning' | 'positive';
  title: string;
  description: string;
  icon: string;
}

export interface Platform {
  id: 'appstore' | 'playstore' | 'youtube';
  name: string;
  icon: string;
  searchPlaceholder: string;
  examples: ExampleData[];
}

export interface ExampleData {
  text: string;
  value: string;
}

export interface SearchFormData {
  searchTerm: string;
  includeRecentReviews: boolean;
  enableAiInsights: boolean;
  includeCompetitorComparison: boolean;
}

export interface AnalysisProgress {
  step: number;
  totalSteps: number;
  currentStep: string;
  completed: string[];
}
