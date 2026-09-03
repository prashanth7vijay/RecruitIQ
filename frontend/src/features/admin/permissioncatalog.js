export const PERMISSION_CATALOG = {
  "job.create": {
    category: "Jobs",
    label: "Create jobs",
    description: "Draft new job postings.",
  },
  "job.approve": {
    category: "Jobs",
    label: "Approve jobs",
    description: "Act on a step in a job's configured approval chain.",
  },
  "job.publish": {
    category: "Jobs",
    label: "Publish jobs",
    description: "Make a job publicly visible on the career page.",
  },
  "job.close": {
    category: "Jobs",
    label: "Close jobs",
    description: "Close or archive a job posting.",
  },
  "candidate.view_all": {
    category: "Candidates",
    label: "View all candidates",
    description: "See the full candidate list and profiles across the organization.",
  },
  "candidate.reject": {
    category: "Candidates",
    label: "Reject candidates",
    description: "Move a candidate out of an active pipeline.",
  },
  "candidate.manage": {
    category: "Candidates",
    label: "Manage candidates",
    description: "Add notes, tags, and edit candidate records.",
  },
  "application.manage": {
    category: "Applications",
    label: "Manage applications",
    description: "Move candidates between pipeline stages.",
  },
  "onboarding.manage": {
    category: "Applications",
    label: "Manage onboarding",
    description: "Assign buddies/managers and track onboarding tasks for new hires.",
  },
  "interview.schedule": {
    category: "Interviews",
    label: "Schedule interviews",
    description: "Book interviews and assign panelists.",
  },
  "interview.feedback.submit": {
    category: "Interviews",
    label: "Submit interview feedback",
    description: "Leave feedback on interviews you're a panelist for.",
  },
  "offer.create": {
    category: "Offers",
    label: "Create offers",
    description: "Draft an offer for a candidate.",
  },
  "offer.approve": {
    category: "Offers",
    label: "Approve offers",
    description: "Act on a step in an offer's configured approval chain.",
  },
  "referral.submit": {
    category: "Talent",
    label: "Refer candidates",
    description: "Refer someone for an open role from the Employee Portal.",
  },
  "analytics.view_org": {
    category: "Analytics",
    label: "View analytics",
    description: "See the organization-wide hiring dashboard.",
  },
  "company.manage_settings": {
    category: "Company",
    label: "Manage company settings",
    description: "Change the company name and branding (logo, colors, careers page).",
    sensitive: true,
  },
  "org.manage_structure": {
    category: "Configuration",
    label: "Manage org structure",
    description: "Create and edit departments, teams, and locations.",
    sensitive: true,
  },
  "pipeline.manage": {
    category: "Configuration",
    label: "Manage pipelines",
    description: "Design the hiring stages every job uses.",
    sensitive: true,
  },
  "approval.manage_chains": {
    category: "Configuration",
    label: "Manage approval chains",
    description: "Decide who must approve jobs and offers, and in what order.",
    sensitive: true,
  },
  "admin.manage_users": {
    category: "Administration",
    label: "Manage users",
    description: "Invite, deactivate, and reassign the role of any user in the company.",
    sensitive: true,
  },
  "role.manage": {
    category: "Administration",
    label: "Manage roles & permissions",
    description: "Create custom roles and decide what every role can do — including this one.",
    sensitive: true,
  },
};

export const CATEGORY_ORDER = [
  "Jobs",
  "Candidates",
  "Applications",
  "Interviews",
  "Offers",
  "Talent",
  "Analytics",
  "Company",
  "Configuration",
  "Administration",
];

export function describePermission(code) {
  return PERMISSION_CATALOG[code] ?? { category: "Other", label: code, description: "" };
}

export function groupPermissionsByCategory(permissions) {
  const groups = {};
  for (const permission of permissions) {
    const meta = describePermission(permission.code);
    (groups[meta.category] ??= []).push({ ...permission, ...meta });
  }
  return CATEGORY_ORDER.filter((c) => groups[c]).map((category) => ({
    category,
    permissions: groups[category],
  }));
}