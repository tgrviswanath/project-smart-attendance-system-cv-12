import axios from "axios";
const api = axios.create({ baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000" });

export const registerPerson = (fd) =>
  api.post("/api/v1/register", fd, { headers: { "Content-Type": "multipart/form-data" } });
export const recognizeFaces = (fd) =>
  api.post("/api/v1/recognize", fd, { headers: { "Content-Type": "multipart/form-data" } });
export const getRegistry = () => api.get("/api/v1/registry");
export const getAttendance = () => api.get("/api/v1/attendance");
export const getStats = () => api.get("/api/v1/stats");
export const clearAll = () => api.delete("/api/v1/all");
