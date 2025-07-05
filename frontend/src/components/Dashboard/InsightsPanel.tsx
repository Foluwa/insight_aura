"use client";
import React from 'react';
import { InsightData } from '@/types/sentiment';

interface InsightsPanelProps {
  insights: InsightData[];
}

const InsightsPanel: React.FC<InsightsPanelProps> = ({ insights }) => {
  const getInsightStyles = (type: string) => {
    const styles = {
      critical: {
        border: "border-l-red-light-1",
        bg: "bg-red-light-5 dark:bg-red-light-1/10",
        iconBg: "bg-red-light-1/20 dark:bg-red-light-1/20",
        iconColor: "text-red-light-1"
      },
      warning: {
        border: "border-l-orange-light-1",
        bg: "bg-orange-light-5 dark:bg-orange-light-1/10", 
        iconBg: "bg-orange-light-1/20 dark:bg-orange-light-1/20",
        iconColor: "text-orange-light-1"
      },
      positive: {
        border: "border-l-green-light-1",
        bg: "bg-green-light-5 dark:bg-green-light-1/10",
        iconBg: "bg-green-light-1/20 dark:bg-green-light-1/20", 
        iconColor: "text-green-light-1"
      }
    };
    return styles[type as keyof typeof styles];
  };

  return (
    <div className="rounded-[10px] bg-white p-6 shadow-1 dark:bg-gray-dark dark:shadow-card">
      <div className="mb-6 flex items-center gap-3">
        <h4 className="text-body-2xlg font-bold text-dark dark:text-white">
          AI Insights
        </h4>
        <div className="rounded-full bg-primary px-3 py-1">
          <span className="text-body-xs font-bold text-white">AI POWERED</span>
        </div>
      </div>

      <div className="space-y-4">
        {insights.map((insight) => {
          const styles = getInsightStyles(insight.type);
          return (
            <div
              key={insight.id}
              className={`flex items-start gap-4 rounded-[7px] border-l-4 p-4 ${styles.border} ${styles.bg}`}
            >
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${styles.iconBg}`}>
                <span className={`text-body-sm ${styles.iconColor}`}>{insight.icon}</span>
              </div>
              <div className="flex-1">
                <h5 className="mb-2 font-bold text-dark dark:text-white">
                  {insight.title}
                </h5>
                <p className="text-body-sm leading-relaxed text-dark dark:text-dark-6">
                  {insight.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default InsightsPanel;