
function base(props) {
  return {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    ...props,
  };
}

export function CandidatesIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="9" cy="8" r="3.25" />
      <path d="M3.5 20c0-3.3 2.5-5.5 5.5-5.5s5.5 2.2 5.5 5.5" />
      <circle cx="17" cy="7.5" r="2.5" />
      <path d="M15.5 14.3c2.6.3 4.5 2.3 4.5 5.2" />
    </svg>
  );
}

export function JobsIcon(props) {
  return (
    <svg {...base(props)}>
      <rect x="3.5" y="7.5" width="17" height="12" rx="2" />
      <path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5" />
      <path d="M3.5 12.5h17" />
    </svg>
  );
}

export function TalentPoolIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M3.5 18.5c1.6-8 4.8-12 8.5-12s6.9 4 8.5 12" />
      <circle cx="12" cy="6.5" r="2.5" />
    </svg>
  );
}

export function AnalyticsIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M4 20V10" />
      <path d="M12 20V4" />
      <path d="M20 20v-7" />
    </svg>
  );
}

export function InterviewIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8A2.5 2.5 0 0 1 17.5 16H10l-4.5 4v-4H6.5A2.5 2.5 0 0 1 4 13.5z" />
    </svg>
  );
}

export function PipelineIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="5.5" cy="6" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="18.5" cy="18" r="2" />
      <path d="M7.3 7.3 10.2 10.2" />
      <path d="M13.8 13.8 16.7 16.7" />
    </svg>
  );
}

export function OrgIcon(props) {
  return (
    <svg {...base(props)}>
      <rect x="9.5" y="3.5" width="5" height="4" rx="1" />
      <rect x="3.5" y="16.5" width="5" height="4" rx="1" />
      <rect x="15.5" y="16.5" width="5" height="4" rx="1" />
      <path d="M12 7.5v4M6 16.5v-2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

export function SettingsIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3.5v2M12 18.5v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M3.5 12h2M18.5 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

export function BrandingIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M4 12c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M9 20.5c-2-1-3.5-2.8-4.3-5" />
    </svg>
  );
}

export function AdminIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 5 6.3v5.4c0 4.4 3 7.8 7 9.3 4-1.5 7-4.9 7-9.3V6.3z" />
      <path d="M9 12l2 2 4-4.2" />
    </svg>
  );
}

export function SearchIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M19.5 19.5 15 15" />
    </svg>
  );
}

export function CommandIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M8 6.5A1.75 1.75 0 1 1 9.75 8.25H6.5A1.75 1.75 0 1 1 8 6.5" />
      <path d="M8 17.5A1.75 1.75 0 1 0 9.75 15.75H6.5A1.75 1.75 0 1 0 8 17.5" />
      <path d="M17.5 17.5a1.75 1.75 0 1 1-1.75-1.75h3.25a1.75 1.75 0 1 1-1.5 1.75" />
      <path d="M17.5 6.5a1.75 1.75 0 1 0-1.75 1.75h3.25a1.75 1.75 0 1 0-1.5-1.75" />
      <path d="M8.25 8.25h7.5v7.5h-7.5z" />
    </svg>
  );
}

export function SunIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
    </svg>
  );
}

export function MoonIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />
    </svg>
  );
}

export function ChevronRightIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M9 5.5 15.5 12 9 18.5" />
    </svg>
  );
}

export function SignOutIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M9 4.5H6.5A2.5 2.5 0 0 0 4 7v10a2.5 2.5 0 0 0 2.5 2.5H9" />
      <path d="M14 15.5 19 12l-5-3.5" />
      <path d="M19 12H9" />
    </svg>
  );
}

export function UploadIcon(props) {
  return (
    <svg {...base(props)}>
      <path d="M12 15.5V4.5" />
      <path d="M7.5 9 12 4.5 16.5 9" />
      <path d="M4.5 15.5v3a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

export function ReferralIcon(props) {
  return (
    <svg {...base(props)}>
      <circle cx="8" cy="9" r="3" />
      <path d="M3.5 19c0-2.8 2-4.7 4.5-4.7s4.5 1.9 4.5 4.7" />
      <path d="M15 8.5h5.5M17.75 5.75v5.5" />
    </svg>
  );
}
