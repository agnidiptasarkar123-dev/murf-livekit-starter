import React from 'react';
import { cn } from '@/lib/shadcn/utils';

interface ArthashathiLogoProps extends React.SVGProps<SVGSVGElement> {
  className?: string;
  size?: number;
}

export function ArthashathiLogo({ className, size = 64, ...props }: ArthashathiLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("text-teal-900 dark:text-teal-400", className)}
      {...props}
    >
      {/* Outer Shield Outline */}
      <path
        d="M50 5L15 20V45C15 65.5 30 85.5 50 95C70 85.5 85 65.5 85 45V20L50 5Z"
        stroke="currentColor"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Inner Accent Path - Warm Gold */}
      <path
        d="M50 15L23 27V45C23 60.5 35 77 50 84C65 77 77 60.5 77 45V27L50 15Z"
        fill="none"
        stroke="#d97706" /* Tailwind amber-600 */
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Rupee Symbol */}
      <g stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M40 35H60" />
        <path d="M40 45H60" />
        <path d="M40 35C45 35 55 35 55 45C55 55 45 55 40 55" />
        <path d="M45 55L57 72" />
        <path d="M48 35V72" />
      </g>
    </svg>
  );
}
