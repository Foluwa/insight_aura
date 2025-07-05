"use client";
import React from 'react';
import { StatCardData } from '@/types/sentiment';

interface SentimentStatsProps {
  stats: StatCardData[];
}

const SentimentStats: React.FC<SentimentStatsProps> = ({ stats }) => {
  const getIconBg = (type: string) => {
    const iconBgs = {
      positive: "bg-green-light-1",
      negative: "bg-red-light-1", 
      neutral: "bg-orange-light-1",
      total: "bg-blue-light-1"
    };
    return iconBgs[type as keyof typeof iconBgs] || "bg-blue-light-1";
  };

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
      {stats.map((stat, index) => (
        <div key={index} className="rounded-[10px] bg-white px-7.5 py-6 shadow-1 dark:bg-gray-dark dark:shadow-card">
          <div className={`flex h-11.5 w-11.5 items-center justify-center rounded-full ${getIconBg(stat.type)}`}>
            <span className="text-xl text-white">{stat.icon}</span>
          </div>

          <div className="mt-4 flex items-end justify-between">
            <div>
              <h4 className="text-title-md font-bold text-dark dark:text-white">
                {stat.value}
              </h4>
              <span className="text-body-sm font-medium text-dark dark:text-dark-6">{stat.label}</span>
            </div>

            <span className={`flex items-center gap-1 text-body-sm font-medium ${
              stat.changeType === 'positive' ? 'text-green-light-1' : 'text-red-light-1'
            }`}>
              {stat.change}
              <svg
                className={`fill-current ${stat.changeType === 'positive' ? '' : 'rotate-180'}`}
                width="10"
                height="11"
                viewBox="0 0 10 11"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4.35716 2.47737L0.908974 5.82987L5.0443e-07 4.94612L5 0.0848689L10 4.94612L9.09103 5.82987L5.64284 2.47737L5.64284 10.0849L4.35716 10.0849L4.35716 2.47737Z"
                  fill=""
                />
              </svg>
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SentimentStats;