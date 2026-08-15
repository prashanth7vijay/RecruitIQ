import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useCandidateNotes(profileId) {
  return useQuery({
    queryKey: ["candidate-notes", profileId],
    queryFn: async () => (await apiClient.get(`/candidates/${profileId}/notes`)).data.data,
    enabled: Boolean(profileId),
  });
}

export function useAddCandidateNote(profileId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body) => (await apiClient.post(`/candidates/${profileId}/notes`, { body })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidate-notes", profileId] }),
  });
}

export function useCandidateTags(profileId) {
  return useQuery({
    queryKey: ["candidate-tags", profileId],
    queryFn: async () => (await apiClient.get(`/candidates/${profileId}/tags`)).data.data,
    enabled: Boolean(profileId),
  });
}

export function useAddCandidateTag(profileId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (label) => (await apiClient.post(`/candidates/${profileId}/tags`, { label })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidate-tags", profileId] }),
  });
}
