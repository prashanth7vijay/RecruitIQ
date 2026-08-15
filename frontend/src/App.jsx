import { Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { ChangePasswordPage } from "./features/auth/ChangePasswordPage";
import { AppLayout } from "./layouts/AppLayout";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { CandidatesPage } from "./features/candidates/CandidatesPage";
import { JobsPage } from "./features/jobs/JobsPage";
import { JobPipelinePage } from "./features/jobs/JobPipelinePage";
import { CareersPage } from "./features/careers/CareersPage";
import { JobDetailPage } from "./features/careers/JobDetailPage";
import { MyInterviewsPage } from "./features/interviews/MyInterviewsPage";
import { OnboardingPage } from "./features/onboarding/OnboardingPage";
import { OrgPage } from "./features/org/OrgPage";
import { PipelineTemplatesPage } from "./features/org/PipelineTemplatesPage";
import { CompanySettingsPage } from "./features/settings/CompanySettingsPage";
import { BrandingCenterPage } from "./features/branding/BrandingCenterPage";
import { TalentPoolsPage } from "./features/talent-pools/TalentPoolsPage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { AdminPage } from "./features/admin/AdminPage";
import { EmployeePortalPage } from "./features/employee-portal/EmployeePortalPage";
import { CandidateLoginPage } from "./features/candidate-portal/CandidateLoginPage";
import { CandidateSignupPage } from "./features/candidate-portal/CandidateSignupPage";
import { CandidatePortalPage } from "./features/candidate-portal/CandidatePortalPage";
import { CandidateApplicationDetailPage } from "./features/candidate-portal/CandidateApplicationDetailPage";
import { CandidateProtectedRoute } from "./routes/CandidateProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* Public career portal — no auth shell, no login required */}
      <Route path="/careers/:companySlug" element={<CareersPage />} />
      <Route path="/careers/:companySlug/jobs/:jobId" element={<JobDetailPage />} />

      {/* Candidate Portal — a separate auth namespace from the staff app;
          see CandidateAuthContext/CandidateProtectedRoute. No AppLayout
          shell — candidates are not staff members of any company. */}
      <Route path="/portal/login" element={<CandidateLoginPage />} />
      <Route path="/portal/signup" element={<CandidateSignupPage />} />
      <Route
        path="/portal"
        element={
          <CandidateProtectedRoute>
            <CandidatePortalPage />
          </CandidateProtectedRoute>
        }
      />
      <Route
        path="/portal/applications/:applicationId"
        element={
          <CandidateProtectedRoute>
            <CandidateApplicationDetailPage />
          </CandidateProtectedRoute>
        }
      />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/candidates" element={<CandidatesPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/:jobId" element={<JobPipelinePage />} />
        <Route path="/my-interviews" element={<MyInterviewsPage />} />
        <Route path="/onboarding/:applicationId" element={<OnboardingPage />} />
        <Route path="/organization" element={<OrgPage />} />
        <Route path="/pipeline-templates" element={<PipelineTemplatesPage />} />
        <Route path="/settings" element={<CompanySettingsPage />} />
        <Route path="/branding" element={<BrandingCenterPage />} />
        <Route path="/talent-pools" element={<TalentPoolsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/refer" element={<EmployeePortalPage />} />
        <Route path="/" element={<Navigate to="/candidates" replace />} />
      </Route>
    </Routes>
  );
}
