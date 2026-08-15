import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useOffersForApplication(applicationId) {
  return useQuery({
    queryKey: ["offers", applicationId],
    queryFn: async () => (await apiClient.get(`/offers?application_id=${applicationId}`)).data.data,
    enabled: Boolean(applicationId),
  });
}

export function useOfferApprovalSteps(offerId, enabled) {
  return useQuery({
    queryKey: ["offer-approval-steps", offerId],
    queryFn: async () => (await apiClient.get(`/offers/${offerId}/approval-steps`)).data.data,
    enabled: Boolean(offerId) && enabled,
  });
}

function useOfferMutation(applicationId, fn) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offers", applicationId] });
      queryClient.invalidateQueries({ queryKey: ["offer-approval-steps"] });
    },
  });
}

export function useCreateOffer(applicationId) {
  return useOfferMutation(applicationId, async ({ salaryOffered, joiningDate }) => {
    const res = await apiClient.post("/offers", {
      application_id: applicationId,
      salary_offered: salaryOffered,
      joining_date: joiningDate || undefined,
    });
    return res.data.data;
  });
}

export function useSubmitOfferForApproval(applicationId) {
  return useOfferMutation(applicationId, async ({ offerId }) => {
    const res = await apiClient.post(`/offers/${offerId}/submit`);
    return res.data.data;
  });
}

export function useApproveOfferStep(applicationId) {
  return useOfferMutation(applicationId, async ({ offerId, stepId }) => {
    const res = await apiClient.post(`/offers/${offerId}/approval-steps/${stepId}/approve`, {});
    return res.data.data;
  });
}

export function useAcceptOffer(applicationId) {
  return useOfferMutation(applicationId, async (offerId) => {
    const res = await apiClient.post(`/offers/${offerId}/accept`);
    return res.data.data;
  });
}

export function useDeclineOffer(applicationId) {
  return useOfferMutation(applicationId, async (offerId) => {
    const res = await apiClient.post(`/offers/${offerId}/decline`);
    return res.data.data;
  });
}
