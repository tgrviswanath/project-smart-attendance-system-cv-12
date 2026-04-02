import React, { useState, useRef } from "react";
import {
  Box, CircularProgress, Alert, Typography, Paper,
  Chip, Table, TableBody, TableCell, TableHead, TableRow, Divider,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import HelpIcon from "@mui/icons-material/Help";
import { recognizeFaces } from "../services/attendanceApi";

export default function RecognizePage({ onUpdate }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await recognizeFaces(fd);
      setResult(r.data);
      await onUpdate();
    } catch (e) {
      setError(e.response?.data?.detail || "Recognition failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>Upload a photo to mark attendance.</Typography>

      <Paper
        variant="outlined"
        onClick={() => fileRef.current.click()}
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
        onDragOver={(e) => e.preventDefault()}
        sx={{ p: 3, mb: 2, textAlign: "center", cursor: "pointer", borderStyle: "dashed", "&:hover": { bgcolor: "action.hover" } }}
      >
        <input ref={fileRef} type="file" hidden accept=".jpg,.jpeg,.png,.bmp,.webp"
          onChange={(e) => handleFile(e.target.files[0])} />
        {loading
          ? <Box><CircularProgress size={28} sx={{ mb: 1 }} /><Typography color="text.secondary">Recognizing…</Typography></Box>
          : <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
              <UploadFileIcon color="action" />
              <Typography color="text.secondary">Upload photo to mark attendance</Typography>
            </Box>
        }
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Box sx={{ display: "flex", gap: 1.5, mb: 2, flexWrap: "wrap" }}>
            <Chip label={`${result.face_count} face${result.face_count !== 1 ? "s" : ""} detected`} />
            <Chip icon={<CheckCircleIcon />}
              label={`${result.recognized.length} recognized`} color="success" />
            {result.unknown_count > 0 && (
              <Chip icon={<HelpIcon />}
                label={`${result.unknown_count} unknown`} color="warning" />
            )}
          </Box>

          <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
            <img src={`data:image/jpeg;base64,${result.annotated_image}`}
              alt="annotated" style={{ width: "100%", borderRadius: 4 }} />
          </Paper>

          {result.recognized.length > 0 && (
            <>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="subtitle2" gutterBottom>Attendance Marked</Typography>
              <Paper variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: "grey.50" }}>
                      <TableCell>Name</TableCell>
                      <TableCell>Person ID</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.recognized.map((r, i) => (
                      <TableRow key={i} hover>
                        <TableCell fontWeight="bold">{r.name}</TableCell>
                        <TableCell>{r.person_id}</TableCell>
                        <TableCell>
                          <Chip label="✅ Present" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
