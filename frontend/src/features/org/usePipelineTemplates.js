import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";
import { usePipelineTemplates } from "../jobs/useJobMutations";

export { usePipelineTemplates };

export function useCreatePipelineTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, stages, isDefault }) => {
      const res = await apiClient.post("/pipeline-templates", {
        name,
        is_default: Boolean(isDefault),
        stages,
      });
      return res.data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pipeline-templates"] }),
  });
}

export function useUpdatePipelineTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ templateId, name, stages, isDefault }) => {
      const res = await apiClient.patch(`/pipeline-templates/${templateId}`, {
        ...(name !== undefined ? { name } : {}),
        ...(stages !== undefined ? { stages } : {}),
        ...(isDefault !== undefined ? { is_default: isDefault } : {}),
      });
      return res.data.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pipeline-templates"] }),
  });
}

export function useDeletePipelineTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (templateId) => (await apiClient.delete(`/pipeline-templates/${templateId}`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pipeline-templates"] }),
  });
}
