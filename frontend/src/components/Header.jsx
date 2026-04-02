import React from "react";
import { AppBar, Toolbar, Typography, Chip, Box } from "@mui/material";
import BadgeIcon from "@mui/icons-material/Badge";

export default function Header({ stats }) {
  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <BadgeIcon />
          <Typography variant="h6" fontWeight="bold">Smart Attendance System</Typography>
        </Box>
        {stats && (
          <Box sx={{ display: "flex", gap: 1 }}>
            <Chip label={`${stats.registered_persons} registered`} size="small"
              sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white" }} />
            <Chip label={`${stats.attendance_records} records`} size="small"
              sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white" }} />
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
