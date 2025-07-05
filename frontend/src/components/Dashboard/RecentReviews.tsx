"use client";
import React from 'react';
import { ReviewData } from '@/types/sentiment';
interface RecentReviewsProps {
  reviews: ReviewData[];
}

const RecentReviews: React.FC<RecentReviewsProps> = ({ reviews }) => {
  const getSentimentBadge = (sentiment: string) => {
    const badges = {
      positive: "bg-green-light-1 text-white",
      negative: "bg-red-light-1 text-white",
      neutral: "bg-orange-light-1 text-white"
    };
    return badges[sentiment as keyof typeof badges];
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <svg
        key={i}
        className={`fill-current ${i < rating ? 'text-orange-light-1' : 'text-dark dark:text-dark-6'}`}
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M8 0.5L9.7 5.7H15.2L11.1 8.8L12.8 14L8 10.9L3.2 14L4.9 8.8L0.8 5.7H6.3L8 0.5Z"/>
      </svg>
    ));
  };

  return (
    <div className="rounded-[10px] bg-white p-6 shadow-1 dark:bg-gray-dark dark:shadow-card">
      <h4 className="mb-6 text-body-2xlg font-bold text-dark dark:text-white">
        Recent Reviews
      </h4>

      <div className="space-y-4">
        {reviews.map((review) => (
          <div key={review.id} className="flex gap-4 rounded-[7px] bg-gray-2 p-4 dark:bg-dark-2">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary text-body-sm font-bold text-white">
              {review.avatar}
            </div>
            <div className="flex-1">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-bold text-dark dark:text-white">
                  {review.user}
                </span>
                <div className="flex gap-1">
                  {renderStars(review.rating)}
                </div>
              </div>
              <p className="mb-3 text-body-sm leading-relaxed text-dark dark:text-dark-6">
                {review.text}
              </p>
              <span className={`inline-block rounded-full px-3 py-1 text-body-xs font-bold uppercase ${getSentimentBadge(review.sentiment)}`}>
                {review.sentiment}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentReviews;