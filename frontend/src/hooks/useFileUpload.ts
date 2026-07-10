import { useState } from "react";
import { apiClient } from "../lib/api";

export function useFileUpload(onSuccess: () => void) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = async (title: string, file: File) => {
    setIsSubmitting(true);
    setError(null);

    try {
      await apiClient.createFile(title, file);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Произошла ошибка");
    } finally {
      setIsSubmitting(false);
    }
  };

  return { isSubmitting, error, uploadFile, setError };
}
