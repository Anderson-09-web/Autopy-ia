import { useState, useEffect } from "react";
import { fetchAuthSession } from "./auth-utils"; // placeholder if needed

export const API_KEY_LOCAL_STORAGE_KEY = "autopy_api_key";
export const ADMIN_KEY_LOCAL_STORAGE_KEY = "autopy_admin_key";

export function useAuth() {
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem(API_KEY_LOCAL_STORAGE_KEY) || "");
  const [adminKey, setAdminKey] = useState<string>(() => localStorage.getItem(ADMIN_KEY_LOCAL_STORAGE_KEY) || "");

  useEffect(() => {
    localStorage.setItem(API_KEY_LOCAL_STORAGE_KEY, apiKey);
  }, [apiKey]);

  useEffect(() => {
    localStorage.setItem(ADMIN_KEY_LOCAL_STORAGE_KEY, adminKey);
  }, [adminKey]);

  return { apiKey, setApiKey, adminKey, setAdminKey };
}

export function getCustomFetchOptions(authParams: { apiKey?: string, adminKey?: string }): RequestInit {
  const headers: Record<string, string> = {};
  if (authParams.apiKey) {
    headers["Authorization"] = `Bearer ${authParams.apiKey}`;
  }
  if (authParams.adminKey) {
    headers["X-Admin-Key"] = authParams.adminKey;
  }
  
  return {
    headers
  };
}
