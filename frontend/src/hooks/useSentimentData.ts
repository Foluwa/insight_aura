"use client";
import { useState, useCallback } from 'react';
import { SentimentData, StatCardData, InsightData, ReviewData } from '@/types/sentiment';

export interface SentimentDashboardData {
  sentimentData: SentimentData;
  statsData: StatCardData[];
  insightsData: InsightData[];
  reviewsData: ReviewData[];
  ratingData: number[];
}

export const useSentimentData = () => {
  const [data, setData] = useState<SentimentDashboardData>({
    sentimentData: {
      positive: [65, 67, 70, 68, 72, 69, 68],
      negative: [20, 18, 17, 19, 16, 18, 19],
      neutral: [15, 15, 13, 13, 12, 13, 13]
    },
    statsData: [
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
    ],
    insightsData: [
      {
        id: '1',
        type: 'critical',
        title: 'Critical Issue Detected',
        description: 'Users are reporting crashes after the latest update.',
        icon: '⚠️'
      }
    ],
    reviewsData: [
      {
        id: '1',
        user: 'John Smith',
        avatar: 'JS',
        rating: 5,
        text: 'Amazing app! The new dark mode is beautiful.',
        sentiment: 'positive',
        date: '2024-01-15'
      }
    ],
    ratingData: [45, 25, 15, 10, 5]
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateData = useCallback(async (platform: string, searchTerm: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate new data based on platform and search term
      const newSentimentData: SentimentData = {
        positive: Array.from({length: 7}, () => Math.floor(Math.random() * 20) + 60),
        negative: Array.from({length: 7}, () => Math.floor(Math.random() * 15) + 10),
        neutral: Array.from({length: 7}, () => Math.floor(Math.random() * 10) + 10)
      };

      setData(prevData => ({
        ...prevData,
        sentimentData: newSentimentData
      }));
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    data,
    loading,
    error,
    updateData
  };
};
