import axios from "axios";

let candidateAccessToken = null;
let onCandidateUnauthenticated = () => {};

export function setCandidateAccessToken(token) {
  candidateAccessToken = token;
}

export function setCandidateUnauthenticatedHandler(handler) {
  onCandidateUnauthenticated = handler;
}

export const candidateApiClient = axios.create({
  baseURL: "/api/v1",
});

candidateApiClient.interceptors.request.use((config) => {
  if (candidateAccessToken) {
    config.headers.Authorization = `Bearer ${candidateAccessToken}`;
  }
  return config;
});

candidateApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      setCandidateAccessToken(null);
      onCandidateUnauthenticated();
    }
    return Promise.reject(error);
  }
);
