import axios from "axios";

let accessToken = null;
let onUnauthenticated = () => {};

export function setAccessToken(token) {
  accessToken = token;
}

export function setUnauthenticatedHandler(handler) {
  onUnauthenticated = handler;
}

export const apiClient = axios.create({
  baseURL: "/api/v1",
  withCredentials: true, // sends the HttpOnly refresh cookie
});

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retried && !originalRequest.url?.includes("/auth/refresh")) {
      originalRequest._retried = true;

      try {
        // Coalesce concurrent 401s into a single refresh call rather
        // than firing one refresh request per failed request.
        if (!refreshPromise) {
          refreshPromise = apiClient
            .post("/auth/refresh")
            .then((res) => {
              setAccessToken(res.data.data.access_token);
              return res.data.data.access_token;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        setAccessToken(null);
        onUnauthenticated();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
