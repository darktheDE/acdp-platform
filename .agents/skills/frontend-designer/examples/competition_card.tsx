'use client';

import React from 'react';
import { Calendar, Trophy, Users, ExternalLink, ShieldCheck } from 'lucide-react';

export interface CompetitionCardProps {
  id: string;
  name: string;
  organizer: string;
  category: string;
  registrationDeadline: string;
  tier: 'School' | 'City' | 'National' | 'International';
  teamSize: string;
  prizePoolVnd: number;
  tags: string[];
  isVerified: boolean;
  onExploreRules?: (id: string) => void;
}

export const CompetitionCard: React.FC<CompetitionCardProps> = ({
  id,
  name,
  organizer,
  category,
  registrationDeadline,
  tier,
  teamSize,
  prizePoolVnd,
  tags,
  isVerified,
  onExploreRules,
}) => {
  const formattedPrize = new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(prizePoolVnd);

  const formattedDeadline = new Date(registrationDeadline).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <article
      className="group relative flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all duration-200 hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
      aria-labelledby={`comp-title-${id}`}
    >
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 pb-3">
          <span className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
            {tier}
          </span>
          {isVerified && (
            <span
              className="inline-flex items-center gap-1 text-xs font-medium text-green-700 dark:text-green-400"
              title="Thông tin đã được kiểm chứng từ BTC chính thức"
            >
              <ShieldCheck className="h-4 w-4" />
              Đã xác thực
            </span>
          )}
        </div>

        {/* Title & Organizer */}
        <h3
          id={`comp-title-${id}`}
          className="text-lg font-semibold text-slate-900 line-clamp-2 group-hover:text-blue-900 dark:text-slate-100 dark:group-hover:text-blue-400"
        >
          {name}
        </h3>
        <p className="mt-1 text-xs text-slate-500 line-clamp-1 dark:text-slate-400">{organizer}</p>

        {/* Key Metrics Grid */}
        <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-xs text-slate-600 dark:border-slate-800 dark:text-slate-300">
          <div className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4 text-orange-600 dark:text-orange-400" />
            <span className="font-mono">{formattedDeadline}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="h-4 w-4 text-slate-400" />
            <span>{teamSize}</span>
          </div>
          <div className="col-span-2 flex items-center gap-1.5 font-medium text-slate-900 dark:text-slate-100">
            <Trophy className="h-4 w-4 text-amber-500" />
            <span className="font-mono">{formattedPrize}</span>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="rounded-sm bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300"
            >
              #{tag}
            </span>
          ))}
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800">
        <button
          type="button"
          onClick={() => onExploreRules?.(id)}
          className="text-xs font-semibold text-blue-800 hover:underline dark:text-blue-400"
          aria-label={`Hỏi AI thể lệ cuộc thi ${name}`}
        >
          Tra cứu thể lệ (RAG) &rarr;
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          aria-label={`Xem chi tiết cuộc thi ${name}`}
        >
          <span>Chi tiết</span>
          <ExternalLink className="h-3 w-3" />
        </button>
      </div>
    </article>
  );
};
