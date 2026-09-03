import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useCandidates(page = 1) {
  return useQuery({
    queryKey: ["candidates", page],
    queryFn: async () => {
      const res = await apiClient.get(`/candidates?page=${page}`);
      return { items: res.data.data, pagination: res.data.meta.pagination };
    },
  });
}

export function useResumeDownloadUrl(profileId) {
  return useQuery({
    queryKey: ["candidate-resume", profileId],
    queryFn: async () => (await apiClient.get(`/candidates/${profileId}/resume`)).data.data,
    enabled: false,
    retry: false,
  });
}