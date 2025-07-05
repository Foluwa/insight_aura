"use client";
import React, { useState, useCallback } from 'react';
import SearchPanel from '../SearchPanel';
import SentimentStats from '../SentimentStats';
import SentimentChart from '../Charts/SentimentChart';
import InsightsPanel from './InsightsPanel';
import RecentReviews from './RecentReviews';
import { StatCardData, SentimentData, InsightData, ReviewData, SearchFormData } from '@/types/sentiment';

const DetailedCharts: React.FC = () => {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<string | null>(null);

  // Sample data
  const [sentimentData] = useState<SentimentData>({
    positive: [65, 67, 70, 68, 72, 69, 68],
    negative: [20, 18, 17, 19, 16, 18, 19],
    neutral: [15, 15, 13, 13, 12, 13, 13]
  });

  const [statsData] = useState<StatCardData[]>([
    {
      value: '68.4%',
      label: 'Positive Sentiment',
      change: '+2.3% from last week',
      changeType: 'positive',
      icon: '😊',
      type: 'positive'
    },
    {
      value: '18.7%',
      label: 'Negative Sentiment',
      change: '-1.2% from last week',
      changeType: 'positive',
      icon: '😞',
      type: 'negative'
    },
    {
      value: '12.9%',
      label: 'Neutral Sentiment',
      change: '+0.4% from last week',
      changeType: 'positive',
      icon: '😐',
      type: 'neutral'
    },
    {
      value: '3,247',
      label: 'Total Reviews',
      change: '+142 this week',
      changeType: 'positive',
      icon: '📊',
      type: 'total'
    }
  ]);

  const [insightsData] = useState<InsightData[]>([
    {
      id: '1',
      type: 'critical',
      title: 'Critical Issue Detected',
      description: 'Users are reporting crashes after the latest update. 23% increase in negative sentiment related to stability issues.',
      icon: '⚠️'
    },
    {
      id: '2',
      type: 'positive',
      title: 'Feature Appreciation',
      description: 'Users love the new dark mode feature. 89% of mentions are positive, especially praising the design aesthetics.',
      icon: '✨'
    },
    {
      id: '3',
      type: 'warning',
      title: 'Improvement Opportunity',
      description: 'Consider adding tutorial videos. 34% of neutral reviews mention confusion about new features.',
      icon: '💡'
    }
  ]);

  const [reviewsData] = useState<ReviewData[]>([
    {
      id: '1',
      user: 'John Smith',
      avatar: 'JS',
      rating: 5,
      text: 'Amazing app! The new dark mode is beautiful and the performance improvements are noticeable. Keep up the great work!',
      sentiment: 'positive',
      date: '2024-01-15'
    },
    {
      id: '2',
      user: 'Maria Johnson',
      avatar: 'MJ',
      rating: 2,
      text: 'App keeps crashing since the latest update. Please fix this issue, it\'s affecting my daily workflow.',
      sentiment: 'negative',
      date: '2024-01-14'
    },
    {
      id: '3',
      user: 'Robert Davis',
      avatar: 'RD',
      rating: 3,
      text: 'Good app overall, but I\'m still figuring out how to use some of the new features. Could use better tutorials.',
      sentiment: 'neutral',
      date: '2024-01-13'
    }
  ]);

  const handleAnalysisComplete = useCallback((data: SearchFormData & { platform: string }) => {
    setCurrentAnalysis(`${data.searchTerm} (${data.platform})`);
    console.log('Analysis completed:', data);
  }, []);

  return (
    <>
      {/* Header Section */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-title-xxl font-bold text-dark dark:text-white">
            Sentiment Analysis Dashboard
          </h2>
          {currentAnalysis && (
            <p className="text-body-sm text-dark dark:text-dark-6">
              Currently analyzing: <span className="font-medium text-dark dark:text-white">{currentAnalysis}</span>
            </p>
          )}
        </div>
        <button
          onClick={() => setIsSearchOpen(true)}
          className="inline-flex items-center justify-center gap-2.5 rounded-[7px] bg-primary px-6 py-4 text-center font-medium text-white hover:bg-opacity-90 lg:px-8 xl:px-10"
        >
          <span className="text-lg">🔍</span>
          New Analysis
        </button>
      </div>

      {/* Stats Cards */}
      <SentimentStats stats={statsData} />

      <div className="mt-4 grid grid-cols-12 gap-4 md:mt-6 md:gap-6 2xl:mt-7.5 2xl:gap-7.5">
        {/* Sentiment Chart */}
        <SentimentChart 
          data={sentimentData}
          title={currentAnalysis ? `Sentiment Trends - ${currentAnalysis}` : 'Sentiment Trends'}
        />

        {/* Rating Distribution Chart Placeholder */}
        <div className="col-span-12 xl:col-span-4">
          <div className="rounded-[10px] bg-white px-7.5 pb-6 pt-7.5 shadow-1 dark:bg-gray-dark dark:shadow-card">
            <div className="mb-3 flex justify-between gap-4 sm:flex">
              <div>
                <h5 className="text-body-2xlg font-bold text-dark dark:text-white">
                  Rating Distribution
                </h5>
              </div>
            </div>
            <div className="mb-2">
              <div className="mx-auto flex h-90 items-center justify-center">
                <div className="text-center text-dark dark:text-dark-6">
                  Rating distribution chart will go here
                  <br />
                  <span className="text-body-sm">You can integrate ChartThree or similar</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Insights and Reviews Section */}
      <div className="mt-4 grid grid-cols-12 gap-4 md:mt-6 md:gap-6 2xl:mt-7.5 2xl:gap-7.5">
        <div className="col-span-12 xl:col-span-6">
          <InsightsPanel insights={insightsData} />
        </div>
        <div className="col-span-12 xl:col-span-6">
          <RecentReviews reviews={reviewsData} />
        </div>
      </div>

      {/* Search Panel Modal */}
      <SearchPanel
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onAnalysisComplete={handleAnalysisComplete}
      />
    </>
  );
};

export default DetailedCharts;