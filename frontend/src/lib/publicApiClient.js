import axios from "axios";

export const publicApiClient = axios.create({
  baseURL: "/api/v1/public",
});
