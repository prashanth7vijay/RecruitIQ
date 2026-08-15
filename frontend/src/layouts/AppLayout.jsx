import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../stores/AuthContext";
import { Button } from "../components/ui/Button";
import { NotificationBell } from "../components/layout/NotificationBell";
import { ThemeToggle } from "../components/layout/ThemeToggle";
import { CommandPalette } from "../components/layout/CommandPalette";
import { SearchBar } from "../features/search/SearchBar";
import {
  CandidatesIcon,
  JobsIcon,
  TalentPoolIcon,
  AnalyticsIcon,
  InterviewIcon,
  PipelineIcon,
  OrgIcon,
  SettingsIcon,
  BrandingIcon,
  AdminIcon,
  ReferralIcon,
  SignOutIcon,
} from "../components/icons";

const navGroups = [
  {
    label: "Recruiting",
    items: [
      { to: "/candidates", label: "Candidates", icon: CandidatesIcon },
      { to: "/jobs", label: "Jobs", icon: JobsIcon },
      { to: "/talent-pools", label: "Talent Pools", icon: TalentPoolIcon },
      { to: "/my-interviews", label: "My Interviews", icon: InterviewIcon },
    ],
  },
  {
    label: "For You",
    items: [
      { to: "/refer", label: "Refer a Candidate", icon: ReferralIcon, requiredPermission: "referral.submit" },
    ],
  },
  {
    label: "Insights",
    items: [
      {
        to: "/analytics",
        label: "Analytics",
        icon: AnalyticsIcon,
        requiredPermission: "analytics.view_org",
      },
    ],
  },
  {
    label: "Administration",
    items: [
      { to: "/pipeline-templates", label: "Pipelines", icon: PipelineIcon },
      { to: "/organization", label: "Organization", icon: OrgIcon },
      { to: "/branding", label: "Branding", icon: BrandingIcon },
      { to: "/settings", label: "Settings", icon: SettingsIcon },
      { to: "/admin", label: "Admin", icon: AdminIcon, requiredPermission: "admin.manage_users" },
    ],
  },
];

export function AppLayout() {
  const { logout, hasPermission } = useAuth();

  const visibleGroups = navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => !item.requiredPermission || hasPermission(item.requiredPermission)),
    }))
    .filter((group) => group.items.length > 0);

  const flatNavItems = visibleGroups.flatMap((g) => g.items);

  return (
    <div className="flex min-h-screen bg-[var(--surface)] text-[var(--text-primary)]">
      <aside className="flex w-60 flex-col justify-between border-r border-[var(--border)] bg-[var(--surface-raised)] p-5">
        <div>
          <div className="flex items-center gap-2 px-1">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--accent)] font-display text-sm text-white">
              R
            </div>
            <div className="font-display text-lg text-[var(--text-primary)]">RecruitIQ</div>
          </div>

          <nav className="mt-8 flex flex-col gap-5">
            {visibleGroups.map((group) => (
              <div key={group.label}>
                <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  {group.label}
                </p>
                <div className="mt-1.5 flex flex-col gap-0.5">
                  {group.items.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-[var(--accent-soft)] text-signal-700 dark:text-signal-300"
                            : "text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
                        }`
                      }
                    >
                      <item.icon className="h-[17px] w-[17px] shrink-0" />
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </div>

        <Button variant="ghost" onClick={logout} className="justify-start">
          <SignOutIcon className="h-4 w-4" />
          Sign out
        </Button>
      </aside>

      <div className="flex flex-1 flex-col">
        <div className="sticky top-0 z-40 flex items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--surface-raised)]/90 px-8 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <CommandPalette navItems={flatNavItems} onSignOut={logout} />
            <SearchBar />
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <NotificationBell />
          </div>
        </div>
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
