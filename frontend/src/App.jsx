import React, { useState, useEffect } from "react";
import { Container, Tabs, Tab, Box } from "@mui/material";
import Header from "./components/Header";
import RegisterPage from "./pages/RegisterPage";
import RecognizePage from "./pages/RecognizePage";
import AttendancePage from "./pages/AttendancePage";
import { getStats, getRegistry, getAttendance } from "./services/attendanceApi";

export default function App() {
  const [tab, setTab] = useState(0);
  const [stats, setStats] = useState(null);
  const [registry, setRegistry] = useState([]);
  const [attendance, setAttendance] = useState([]);

  const fetchAll = async () => {
    try {
      const [s, r, a] = await Promise.all([getStats(), getRegistry(), getAttendance()]);
      setStats(s.data); setRegistry(r.data.persons); setAttendance(a.data.records);
    } catch (_) {}
  };

  useEffect(() => { fetchAll(); }, []);

  return (
    <>
      <Header stats={stats} />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Register Person" />
          <Tab label="Mark Attendance" />
          <Tab label="Attendance Log" />
        </Tabs>
        <Box>
          {tab === 0 && <RegisterPage onUpdate={fetchAll} />}
          {tab === 1 && <RecognizePage onUpdate={fetchAll} />}
          {tab === 2 && <AttendancePage registry={registry} attendance={attendance} />}
        </Box>
      </Container>
    </>
  );
}
