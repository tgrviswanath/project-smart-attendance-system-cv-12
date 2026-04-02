import React, { useState, useRef } from "react";
import {
  Box, TextField, Button, CircularProgress, Alert,
  Typography, Paper, Chip, Avatar,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import PersonAddIcon from "@mui/icons-material/PersonAdd";
import { registerPerson } from "../services/attendanceApi";

export default function RegisterPage({ onUpdate }) {
  const [name, setName] = useState("");
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const fileRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null); setError("");
  };

  const handleRegister = async () => {
    if (!name.trim() || !file) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const fd = new FormData();
      fd.append("name", name.trim());
      fd.append("file", file);
      const r = await registerPerson(fd);
      setResult(r.data);
      setName(""); setFile(null); setPreview(null);
      await onUpdate();
    } catch (e) {
      setError(e.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>Register a new person by uploading their face photo.</Typography>

      <Paper
        variant="outlined"
        onClick={() => fileRef.current.click()}
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
        onDragOver={(e) => e.preventDefault()}
        sx={{ p: 2.5, mb: 2, textAlign: "center", cursor: "pointer", borderStyle: "dashed", "&:hover": { bgcolor: "action.hover" } }}
      >
        <input ref={fileRef} type="file" hidden accept=".jpg,.jpeg,.png,.bmp,.webp"
          onChange={(e) => handleFile(e.target.files[0])} />
        {preview
          ? <Avatar src={preview} sx={{ width: 100, height: 100, mx: "auto" }} />
          : <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
              <UploadFileIcon color="action" />
              <Typography color="text.secondary">Upload face photo</Typography>
            </Box>
        }
      </Paper>

      <TextField fullWidth label="Person Name" value={name}
        onChange={(e) => setName(e.target.value)} sx={{ mb: 2 }} size="small" />

      <Button variant="contained" onClick={handleRegister}
        disabled={!name.trim() || !file || loading}
        startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <PersonAddIcon />}>
        {loading ? "Registering…" : "Register"}
      </Button>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {result && (
        <Alert severity="success" sx={{ mt: 2 }}>
          ✅ {result.name} registered (ID: {result.person_id}). Total: {result.total_registered}
        </Alert>
      )}
    </Box>
  );
}
