import { useState, useEffect } from "react";
import { apiClient, FileItem, AlertItem } from "../lib/api";

export function useFilesAndAlerts() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [filesData, alertsData] = await Promise.all([
        apiClient.getFiles(),
        apiClient.getAlerts(),
      ]);

      setFiles(filesData);
      setAlerts(alertsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Произошла ошибка");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  return { files, alerts, isLoading, error, loadData };
}
