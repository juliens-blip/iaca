const DEFAULT_API_BASE_URL = "http://localhost:8000";

const trimTrailingSlash = (value: string): string => value.replace(/\/+$/, "");

const joinApiPath = (baseUrl: string, path: string): string => {
  const normalizedBaseUrl = trimTrailingSlash(baseUrl);
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (normalizedBaseUrl.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return `${normalizedBaseUrl}${normalizedPath.slice(4)}`;
  }

  return `${normalizedBaseUrl}${normalizedPath}`;
};

export const getPublicApiBaseUrl = (): string => {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (!configuredBaseUrl) {
    return DEFAULT_API_BASE_URL;
  }

  return trimTrailingSlash(configuredBaseUrl);
};

export const getApiWebSocketUrl = (path: string): string => {
  const socketUrl = new URL(joinApiPath(getPublicApiBaseUrl(), path));
  socketUrl.protocol = socketUrl.protocol === "https:" ? "wss:" : "ws:";
  return socketUrl.toString();
};
