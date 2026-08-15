import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: async () => (await apiClient.get("/users")).data.data,
    staleTime: 5 * 60_000, // colleague list changes rarely — cache longer than the default
  });
}
