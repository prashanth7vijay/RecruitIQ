import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useDepartments() {
  return useQuery({
    queryKey: ["departments"],
    queryFn: async () => (await apiClient.get("/departments")).data.data,
  });
}

export function useCreateDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, parentId }) =>
      (await apiClient.post("/departments", { name, parent_id: parentId || undefined })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["departments"] }),
  });
}

export function useDeleteDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (departmentId) => (await apiClient.delete(`/departments/${departmentId}`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["departments"] }),
  });
}

export function useTeams(departmentId) {
  return useQuery({
    queryKey: ["teams", departmentId],
    queryFn: async () => {
      const query = departmentId ? `?department_id=${departmentId}` : "";
      return (await apiClient.get(`/teams${query}`)).data.data;
    },
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, departmentId }) =>
      (await apiClient.post("/teams", { name, department_id: departmentId || undefined })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["teams"] }),
  });
}

export function useDeleteTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (teamId) => (await apiClient.delete(`/teams/${teamId}`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["teams"] }),
  });
}

export function useLocations() {
  return useQuery({
    queryKey: ["locations"],
    queryFn: async () => (await apiClient.get("/locations")).data.data,
  });
}

export function useCreateLocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, city, country, isRemote }) =>
      (
        await apiClient.post("/locations", {
          name,
          city: city || undefined,
          country: country || undefined,
          is_remote: isRemote,
        })
      ).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["locations"] }),
  });
}

export function useDeleteLocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (locationId) => (await apiClient.delete(`/locations/${locationId}`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["locations"] }),
  });
}

export function useUpdateUserOrgPlacement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, departmentId, teamId, managerId, locationId }) =>
      (
        await apiClient.patch(`/users/${userId}/org-placement`, {
          ...(departmentId !== undefined ? { department_id: departmentId || null } : {}),
          ...(teamId !== undefined ? { team_id: teamId || null } : {}),
          ...(managerId !== undefined ? { manager_id: managerId || null } : {}),
          ...(locationId !== undefined ? { location_id: locationId || null } : {}),
        })
      ).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
}
