import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useTalentPools() {
  return useQuery({
    queryKey: ["talent-pools"],
    queryFn: async () => (await apiClient.get("/talent-pools")).data.data,
  });
}

export function useCreateTalentPool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, description }) =>
      (await apiClient.post("/talent-pools", { name, description })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["talent-pools"] }),
  });
}

export function usePoolMembers(poolId) {
  return useQuery({
    queryKey: ["talent-pool-members", poolId],
    queryFn: async () => (await apiClient.get(`/talent-pools/${poolId}/members`)).data.data,
    enabled: Boolean(poolId),
  });
}

export function useAddToPool(poolId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (candidateProfileId) =>
      apiClient.post(`/talent-pools/${poolId}/members`, { candidate_profile_id: candidateProfileId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["talent-pool-members", poolId] }),
  });
}

export function useRemoveFromPool(poolId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (candidateProfileId) =>
      apiClient.delete(`/talent-pools/${poolId}/members/${candidateProfileId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["talent-pool-members", poolId] }),
  });
}
