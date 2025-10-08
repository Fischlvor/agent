'use client';

interface ContextProgressProps {
  currentTokens: number;
  maxTokens: number;
}

export default function ContextProgress({ currentTokens, maxTokens }: ContextProgressProps) {
  const percentage = (currentTokens / maxTokens) * 100;

  // 计算圆形进度条参数
  const size = 40; // 圆形大小
  const strokeWidth = 3; // 线条宽度
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  // 根据百分比确定颜色
  const getColor = () => {
    if (percentage > 90) return '#ef4444'; // red-500
    if (percentage > 70) return '#f59e0b'; // amber-500
    return '#6b7280'; // gray-500
  };

  const color = getColor();

  return (
    <div className="flex items-center space-x-2">
      {/* 圆形进度条 */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* 背景圆圈 */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* 进度圆圈 */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-300"
          />
        </svg>
        {/* 百分比文字 */}
        <div
          className="absolute inset-0 flex items-center justify-center text-xs font-medium"
          style={{ color }}
        >
          {percentage.toFixed(0)}%
        </div>
      </div>

      {/* Token信息 */}
      <div className="flex items-center space-x-1 text-sm text-gray-600">
        <span className={`font-medium ${
          percentage > 90
            ? 'text-red-600'
            : percentage > 70
            ? 'text-amber-600'
            : 'text-gray-700'
        }`}>
          {(currentTokens / 1000).toFixed(1)}K
        </span>
        <span className="text-gray-400">/</span>
        <span className="text-gray-600">
          {(maxTokens / 1000).toFixed(0)}K
        </span>
        <span className="text-gray-500">context used</span>
      </div>
    </div>
  );
}

