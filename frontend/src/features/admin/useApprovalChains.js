import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useApprovalChain(entityType) {
  return useQuery({
    queryKey: ["approval-chain", entityType],
    queryFn: async () => (await apiClient.get(`/approval-chains/${entityType}`)).data.data,
  });
}

export function useSetApprovalChain(entityType) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (roleIds) =>
      (await apiClient.put(`/approval-chains/${entityType}`, { role_ids: roleIds })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approval-chain", entityType] }),
  });
}
