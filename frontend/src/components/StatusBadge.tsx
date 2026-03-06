interface StatusBadgeProps {
  status: string;
}

const statusStyles: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  queued: 'bg-blue-100 text-blue-800',
  preparing: 'bg-purple-100 text-purple-800',
  running: 'bg-cyan-100 text-cyan-800',
  paused: 'bg-orange-100 text-orange-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800',
  retrying: 'bg-amber-100 text-amber-800',
  skipped: 'bg-slate-100 text-slate-800',
  healthy: 'bg-green-100 text-green-800',
  degraded: 'bg-yellow-100 text-yellow-800',
  unhealthy: 'bg-red-100 text-red-800',
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = statusStyles[status] || 'bg-gray-100 text-gray-800';
  
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${style}`}
    >
      {status}
    </span>
  );
}
