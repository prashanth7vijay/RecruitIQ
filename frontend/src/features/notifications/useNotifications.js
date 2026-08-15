import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await apiClient.get("/notifications")).data.data,
    refetchInterval: 30_000, // simple polling — no websocket layer yet, per Phase 16.6's "future-ready" note
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId) =>
      (await apiClient.patch(`/notifications/${notificationId}/read`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
}
