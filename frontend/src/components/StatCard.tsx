interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

export function StatCard({ title, value, subtitle, icon, trend }: StatCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className={`mt-1 text-sm ${trend ? trendColors[trend] : 'text-gray-500'}`}>
              {subtitle}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-primary-50 rounded-full">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
