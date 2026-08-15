import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useBranding() {
  return useQuery({
    queryKey: ["branding"],
    queryFn: async () => (await apiClient.get("/companies/me/branding")).data.data,
  });
}

export function useUpdateBranding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fields) => (await apiClient.patch("/companies/me/branding", fields)).data.data,
    onSuccess: (data) => queryClient.setQueryData(["branding"], data),
  });
}

export function useUploadBrandingAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ assetType, file }) => {
      const formData = new FormData();
      formData.append("asset_type", assetType);
      formData.append("file", file);
      const res = await apiClient.post("/companies/me/branding/assets", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data.data;
    },
    onSuccess: (data) => queryClient.setQueryData(["branding"], data),
  });
}
