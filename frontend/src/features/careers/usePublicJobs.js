import { useMutation, useQuery } from "@tanstack/react-query";
import { publicApiClient } from "../../lib/publicApiClient";

export function usePublicCompany(companySlug) {
  return useQuery({
    queryKey: ["public-company", companySlug],
    queryFn: async () => {
      const res = await publicApiClient.get(`/${companySlug}/company`);
      return res.data.data;
    },
    enabled: Boolean(companySlug),
  });
}

export function usePublicJobs(companySlug) {
  return useQuery({
    queryKey: ["public-jobs", companySlug],
    queryFn: async () => {
      const res = await publicApiClient.get(`/${companySlug}/jobs`);
      return res.data.data;
    },
    enabled: Boolean(companySlug),
  });
}

export function usePublicJob(companySlug, jobId) {
  return useQuery({
    queryKey: ["public-job", companySlug, jobId],
    queryFn: async () => {
      const res = await publicApiClient.get(`/${companySlug}/jobs/${jobId}`);
      return res.data.data;
    },
    enabled: Boolean(companySlug && jobId),
  });
}

export function useApplyToJob(companySlug, jobId) {
  return useMutation({
    mutationFn: async ({ email, firstName, lastName, phone, resumeFile }) => {
      const formData = new FormData();
      formData.append("email", email);
      formData.append("first_name", firstName);
      formData.append("last_name", lastName);
      if (phone) formData.append("phone", phone);
      if (resumeFile) formData.append("resume", resumeFile);

      const res = await publicApiClient.post(`/${companySlug}/jobs/${jobId}/apply`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data.data;
    },
  });
}
