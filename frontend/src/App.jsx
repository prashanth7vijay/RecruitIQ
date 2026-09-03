import { Routes, Route,Navigate } from "react-router-dom";
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { ChangePasswordPage } from "./features/auth/ChangePasswordPage";
import { AppLayout } from "./layouts/AppLayout";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { RequirePermission } from "./routes/RequirePermission";
import { HomeRedirect } from "./routes/HomeRedirect";
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
        <Route
          path="/candidates"
          element={
            <RequirePermission anyOf={["candidate.view_all"]}>
              <CandidatesPage />
            </RequirePermission>
          }
        />
        <Route
          path="/jobs"
          element={
            <RequirePermission anyOf={["candidate.view_all"]}>
              <JobsPage />
            </RequirePermission>
          }
        />
        <Route
          path="/jobs/:jobId"
          element={
            <RequirePermission anyOf={["candidate.view_all"]}>
              <JobPipelinePage />
            </RequirePermission>
          }
        />
        <Route path="/my-interviews" element={<MyInterviewsPage />} />
        <Route
          path="/onboarding/:applicationId"
          element={
            <RequirePermission anyOf={["onboarding.manage"]}>
              <OnboardingPage />
            </RequirePermission>
          }
        />
        <Route
          path="/organization"
          element={
            <RequirePermission anyOf={["org.manage_structure"]}>
              <OrgPage />
            </RequirePermission>
          }
        />
        <Route
          path="/pipeline-templates"
          element={
            <RequirePermission anyOf={["pipeline.manage"]}>
              <PipelineTemplatesPage />
            </RequirePermission>
          }
        />
        <Route
          path="/settings"
          element={
            <RequirePermission anyOf={["company.manage_settings"]}>
              <CompanySettingsPage />
            </RequirePermission>
          }
        />
        <Route
          path="/branding"
          element={
            <RequirePermission anyOf={["company.manage_settings"]}>
              <BrandingCenterPage />
            </RequirePermission>
          }
        />
        <Route
          path="/talent-pools"
          element={
            <RequirePermission anyOf={["candidate.view_all"]}>
              <TalentPoolsPage />
            </RequirePermission>
          }
        />
        <Route
          path="/analytics"
          element={
            <RequirePermission anyOf={["analytics.view_org"]}>
              <AnalyticsPage />
            </RequirePermission>
          }
        />
        <Route
          path="/admin"
          element={
            <RequirePermission anyOf={["admin.manage_users", "role.manage", "approval.manage_chains"]}>
              <AdminPage />
            </RequirePermission>
          }
        />
        <Route
          path="/refer"
          element={
            <RequirePermission anyOf={["referral.submit"]}>
              <EmployeePortalPage />
            </RequirePermission>
          }
        />
        <Route path="/" element={<HomeRedirect />} />
      </Route>
    </Routes>
  );
}