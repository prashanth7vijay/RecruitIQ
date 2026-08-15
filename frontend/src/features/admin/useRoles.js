import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useRoles() {
  return useQuery({
    queryKey: ["roles"],
    queryFn: async () => (await apiClient.get("/roles")).data.data,
  });
}

export function usePermissionCatalog() {
  return useQuery({
    queryKey: ["permissions"],
    queryFn: async () => (await apiClient.get("/roles/permissions")).data.data,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, permissionCodes }) =>
      (await apiClient.post("/roles", { name, permission_codes: permissionCodes })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useUpdateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ roleId, name, permissionCodes }) =>
      (
        await apiClient.patch(`/roles/${roleId}`, {
          ...(name !== undefined ? { name } : {}),
          ...(permissionCodes !== undefined ? { permission_codes: permissionCodes } : {}),
        })
      ).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useDeleteRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (roleId) => (await apiClient.delete(`/roles/${roleId}`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, roleId }) =>
      (await apiClient.patch(`/admin/users/${userId}/role`, { role_id: roleId })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}
