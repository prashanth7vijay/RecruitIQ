import { useState } from "react";
import { useNotifications, useMarkNotificationRead } from "../../features/notifications/useNotifications";

function renderNotification(notification) {
  const { type, payload } = notification;
  if (type === "application_stage_changed") {
    return `${payload.candidate_name ?? "A candidate"} moved to ${payload.stage_name} for ${payload.job_title}`;
  }
  return type.replace(/_/g, " ");
}

export function NotificationBell() {
  const { data: notifications } = useNotifications();
  const markRead = useMarkNotificationRead();
  const [open, setOpen] = useState(false);

  const unreadCount = notifications?.filter((n) => !n.read_at).length ?? 0;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-md p-2 text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
        aria-label="Notifications"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-signal-500 text-[10px] font-medium text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-10 mt-2 w-80 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] shadow-panel">
          <div className="max-h-96 overflow-y-auto">
            {(!notifications || notifications.length === 0) && (
              <p className="p-4 text-sm text-[var(--text-muted)]">No notifications yet.</p>
            )}
            {notifications?.map((notification) => (
              <button
                key={notification.id}
                onClick={() => !notification.read_at && markRead.mutate(notification.id)}
                className={`block w-full border-b border-[var(--border)] p-3 text-left text-sm last:border-0 hover:bg-[var(--surface-hover)] ${
                  notification.read_at ? "text-[var(--text-muted)]" : "font-medium text-[var(--text-primary)]"
                }`}
              >
                {renderNotification(notification)}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
