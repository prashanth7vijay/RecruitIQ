import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await apiClient.get("/admin/users")).data.data,
  });
}

export function useUpdateUserStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, status }) =>
      (await apiClient.patch(`/admin/users/${userId}/status`, { status })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ email, firstName, lastName, roleId }) =>
      (
        await apiClient.post("/admin/users", {
          email,
          first_name: firstName,
          last_name: lastName,
          role_id: roleId,
        })
      ).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}

export function useAuditLogs() {
  return useQuery({
    queryKey: ["audit-logs"],
    queryFn: async () => (await apiClient.get("/admin/audit-logs")).data.data,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system-health"],
    queryFn: async () => (await apiClient.get("/admin/system-health")).data.data,
  });
}
