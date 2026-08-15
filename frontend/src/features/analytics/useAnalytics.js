import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useHiringFunnel(jobId) {
  return useQuery({
    queryKey: ["hiring-funnel", jobId],
    queryFn: async () => (await apiClient.get(`/analytics/hiring-funnel?job_id=${jobId}`)).data.data,
    enabled: Boolean(jobId),
  });
}

export function useTimeToHire(jobId) {
  return useQuery({
    queryKey: ["time-to-hire", jobId],
    queryFn: async () => {
      const query = jobId ? `?job_id=${jobId}` : "";
      return (await apiClient.get(`/analytics/time-to-hire${query}`)).data.data;
    },
  });
}

export function useRecruiterPerformance() {
  return useQuery({
    queryKey: ["recruiter-performance"],
    queryFn: async () => (await apiClient.get("/analytics/recruiter-performance")).data.data,
  });
}

export function useHiringVelocity(days = 30) {
  return useQuery({
    queryKey: ["hiring-velocity", days],
    queryFn: async () => (await apiClient.get(`/analytics/velocity?days=${days}`)).data.data,
  });
}

export function usePipelineHealth() {
  return useQuery({
    queryKey: ["pipeline-health"],
    queryFn: async () => (await apiClient.get("/analytics/pipeline-health")).data.data,
  });
}

export function useOfferAcceptanceRate() {
  return useQuery({
    queryKey: ["offer-acceptance"],
    queryFn: async () => (await apiClient.get("/analytics/offer-acceptance")).data.data,
  });
}

export function useDepartmentHiring() {
  return useQuery({
    queryKey: ["department-hiring"],
    queryFn: async () => (await apiClient.get("/analytics/department-hiring")).data.data,
  });
}
