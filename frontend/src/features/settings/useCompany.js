import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useCompany() {
  return useQuery({
    queryKey: ["company"],
    queryFn: async () => (await apiClient.get("/companies/me")).data.data,
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name }) => (await apiClient.patch("/companies/me", { name })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["company"] }),
  });
}
