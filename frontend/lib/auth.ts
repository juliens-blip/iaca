const getRawAuthToken = (): string => {
  return process.env.NEXT_PUBLIC_API_AUTH_TOKEN?.trim() || "";
};

export const withAuthHeaders = (init: RequestInit = {}): RequestInit => {
  const token = getRawAuthToken();
  if (!token) {
    return init;
  }

  const headers = new Headers(init.headers || {});
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return { ...init, headers };
};

export const withAuthQuery = (url: string): string => {
  const token = getRawAuthToken();
  if (!token) {
    return url;
  }

  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}token=${encodeURIComponent(token)}`;
};
