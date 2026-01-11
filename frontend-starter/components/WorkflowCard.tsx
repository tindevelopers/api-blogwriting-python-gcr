import React from 'react';

interface WorkflowCardProps {
  title: string;
  subtitle?: string;
  status: 'done' | 'in_progress' | 'not_started';
  details?: string;
  updatedAt?: string;
  isActive?: boolean;
}

export function WorkflowCard({
  title,
  subtitle,
  status,
  details,
  updatedAt,
  isActive = false,
}: WorkflowCardProps) {
  const getStatusBadge = () => {
    switch (status) {
      case 'done':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            done
          </span>
        );
      case 'in_progress':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            in progress
          </span>
        );
      case 'not_started':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            not started
          </span>
        );
    }
  };

  // Split title if it contains "and" to handle "Polish and Human in the Loop"
  const titleParts = title.includes(' and ') ? title.split(' and ') : [title];
  const mainTitle = titleParts[0];
  const secondaryTitle = titleParts.length > 1 ? titleParts[1] : null;

  return (
    <div
      className={`
        relative p-4 rounded-lg border transition-all
        ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}
        hover:shadow-md
        flex-shrink-0
        w-full sm:w-auto
        min-w-[140px] max-w-[200px]
      `}
    >
      <div className="flex flex-col h-full">
        <div className="mb-2">
          {getStatusBadge()}
        </div>
        
        <div className="flex flex-col min-w-0">
          <h3 className="font-semibold text-sm text-gray-900 break-words leading-tight">
            {mainTitle}
          </h3>
          {secondaryTitle && (
            <div className="mt-1 leading-tight">
              <div className="text-xs text-gray-600 break-words">
                ({secondaryTitle})
              </div>
            </div>
          )}
        </div>

        {details && (
          <p className="text-xs text-gray-600 mt-2 break-words">
            {details}
          </p>
        )}

        {updatedAt && (
          <p className="text-xs text-gray-500 mt-2">
            Updated {updatedAt}
          </p>
        )}
      </div>
    </div>
  );
}

interface WorkflowCardsProps {
  cards: WorkflowCardProps[];
}

export function WorkflowCards({ cards }: WorkflowCardsProps) {
  return (
    <div className="w-full overflow-x-auto">
      <div className="flex gap-3 sm:gap-4 pb-4">
        {cards.map((card, index) => (
          <WorkflowCard key={index} {...card} />
        ))}
      </div>
    </div>
  );
}

