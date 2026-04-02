import React from "react";
import {
  Box, Typography, Paper, Table, TableBody, TableCell,
  TableHead, TableRow, Avatar, Grid, Chip,
} from "@mui/material";

export default function AttendancePage({ registry, attendance }) {
  return (
    <Box>
      <Grid container spacing={3}>
        {/* Registered persons */}
        <Grid item xs={12} md={4}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Registered Persons ({registry.length})
          </Typography>
          {registry.length === 0
            ? <Typography color="text.secondary">No persons registered yet.</Typography>
            : registry.map((p) => (
              <Box key={p.person_id} sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1.5 }}>
                <Avatar src={`data:image/jpeg;base64,${p.thumbnail}`}
                  sx={{ width: 48, height: 48 }} />
                <Box>
                  <Typography variant="subtitle2">{p.name}</Typography>
                  <Typography variant="caption" color="text.secondary">ID: {p.person_id}</Typography>
                </Box>
              </Box>
            ))
          }
        </Grid>

        {/* Attendance log */}
        <Grid item xs={12} md={8}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Attendance Log ({attendance.length})
          </Typography>
          {attendance.length === 0
            ? <Typography color="text.secondary">No attendance records yet.</Typography>
            : (
              <Paper variant="outlined" sx={{ maxHeight: 400, overflow: "auto" }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow sx={{ bgcolor: "grey.50" }}>
                      <TableCell>Name</TableCell>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {attendance.map((a, i) => (
                      <TableRow key={i} hover>
                        <TableCell>{a.name}</TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {new Date(a.timestamp).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label="Present" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            )
          }
        </Grid>
      </Grid>
    </Box>
  );
}
