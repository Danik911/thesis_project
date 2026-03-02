import type { AuthUser } from '@/lib/auth';

interface UserBadgeProps {
  user: AuthUser;
  onSignOut: () => void;
}

export default function UserBadge({ user, onSignOut }: UserBadgeProps) {
  const isAdmin = user.role === 'Admin';

  return (
    <div className="flex items-center gap-2">
      {/* Role badge */}
      <span
        className={`px-2 py-0.5 text-xs font-medium rounded-full border ${
          isAdmin
            ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
            : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
        }`}
      >
        {user.role}
      </span>

      {/* Site label (Operators only) */}
      {!isAdmin && user.site && (
        <span className="text-xs text-slate-400">
          {user.site}
        </span>
      )}

      {/* Email (truncated) */}
      <span className="text-xs text-slate-400 max-w-[120px] truncate" title={user.email}>
        {user.email}
      </span>

      {/* Sign out */}
      <button
        type="button"
        onClick={onSignOut}
        className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-md hover:border-slate-600 transition-colors"
      >
        Sign Out
      </button>
    </div>
  );
}
