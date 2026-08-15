import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useOpenJobs() {
  return useQuery({
    queryKey: ["employee-portal-jobs"],
    queryFn: async () => (await apiClient.get("/employee-portal/jobs")).data.data,
  });
}

export function useMyReferrals() {
  return useQuery({
    queryKey: ["my-referrals"],
    queryFn: async () => (await apiClient.get("/employee-portal/referrals")).data.data,
  });
}

export function useSubmitReferral() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId, email, firstName, lastName, phone }) =>
      (
        await apiClient.post("/employee-portal/referrals", {
          job_id: jobId,
          email,
          first_name: firstName,
          last_name: lastName,
          phone: phone || undefined,
        })
      ).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-referrals"] }),
  });
}
