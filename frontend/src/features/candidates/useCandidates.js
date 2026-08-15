import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export function useAddCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const res = await apiClient.post("/candidates", payload);
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
    },
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ profileId, file }) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiClient.post(`/candidates/${profileId}/resume`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
    },
  });
}
