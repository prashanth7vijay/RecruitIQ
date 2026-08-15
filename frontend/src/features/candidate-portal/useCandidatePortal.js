import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { candidateApiClient } from "../../lib/candidateApiClient";

export function useMyApplications() {
  return useQuery({
    queryKey: ["my-applications"],
    queryFn: async () => (await candidateApiClient.get("/candidate-portal/applications")).data.data,
  });
}

export function useMyApplication(applicationId) {
  return useQuery({
    queryKey: ["my-application", applicationId],
    queryFn: async () =>
      (await candidateApiClient.get(`/candidate-portal/applications/${applicationId}`)).data.data,
    enabled: Boolean(applicationId),
  });
}

export function useMyInterviews(applicationId) {
  return useQuery({
    queryKey: ["my-interviews", applicationId],
    queryFn: async () =>
      (await candidateApiClient.get(`/candidate-portal/applications/${applicationId}/interviews`)).data
        .data,
    enabled: Boolean(applicationId),
  });
}

export function useMyOffers() {
  return useQuery({
    queryKey: ["my-offers"],
    queryFn: async () => (await candidateApiClient.get("/candidate-portal/offers")).data.data,
  });
}

export function useAcceptMyOffer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (offerId) =>
      (await candidateApiClient.post(`/candidate-portal/offers/${offerId}/accept`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-offers"] }),
  });
}

export function useDeclineMyOffer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (offerId) =>
      (await candidateApiClient.post(`/candidate-portal/offers/${offerId}/decline`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-offers"] }),
  });
}
