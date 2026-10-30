import React from 'react';
import { ChevronRight } from 'lucide-react';

export default function FolderCard({
  tabLabel,
  tabColor = 'bg-gray-300',
  icon: Icon,
  iconBg = 'bg-gray-200',
  iconColor = 'text-black',
  badgeText,
  badgeBg = 'bg-gray-100',
  badgeColor = 'text-black',
  title,
  description,
  onClick
}) {
  return (
    <div 
      role="button"
      tabIndex={0}
      aria-label={`Buka editor ${title}`}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      className="relative pt-4 group cursor-pointer focus:outline-none focus-visible:ring-3 focus-visible:ring-black rounded-2xl"
    >
      {/* Folder Tab */}
      <div className={`absolute top-0 left-4 ${tabColor} border-t-3 border-x-3 border-black px-4 py-1 rounded-t-xl text-xs font-black shadow-neo-sm select-none z-10`}>
        {tabLabel}
      </div>

      {/* Main Folder Body */}
      <div className="bg-white border-3 border-black rounded-2xl rounded-tl-none p-5 shadow-neo group-hover:translate-x-0.5 group-hover:translate-y-0.5 transition-all flex flex-col justify-between h-48">
        <div>
          <div className="flex items-start justify-between">
            <div className={`w-12 h-12 ${iconBg} border-2 border-black rounded-xl flex items-center justify-center shadow-neo-sm`}>
              <Icon className={`w-6 h-6 ${iconColor}`} strokeWidth={2.5} />
            </div>
            {badgeText && (
              <span className={`${badgeBg} ${badgeColor} border-2 border-black px-2 py-0.5 rounded-lg text-[11px] font-black shadow-neo-sm`}>
                {badgeText}
              </span>
            )}
          </div>
          <h4 className="font-black text-lg mt-3 leading-snug group-hover:text-[#9D71FD] transition-colors">
            {title}
          </h4>
          <p className="text-xs font-bold text-gray-600 mt-1 line-clamp-2">
            {description}
          </p>
        </div>

        <div className="flex items-center justify-end text-xs font-black text-gray-500 group-hover:text-black transition-colors pt-2 border-t border-gray-100">
          <span>Edit & Pratinjau</span>
          <ChevronRight className="w-4 h-4 ml-0.5" strokeWidth={3} />
        </div>
      </div>
    </div>
  );
}
