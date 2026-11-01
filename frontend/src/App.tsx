
import { useEffect, useState } from "react";
import {
  getHealth,
  getDatabaseHealth,
} from "./api/client";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [databaseStatus, setDatabaseStatus] = useState("Checking...");

  useEffect(() => {
    async function checkServices() {
      try {
        const [backend, database] = await Promise.all([
          getHealth(),
          getDatabaseHealth(),
        ]);

        setBackendStatus(backend.status);
        setDatabaseStatus(database.status);
      } catch (error) {
        console.error(error);

        setBackendStatus("Connection failed");
        setDatabaseStatus("Connection failed");
      }
    }

    checkServices();
  }, []);

  return (
    <main style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Open Source Funding Platform</h1>
      <p>Phase 0 — System Health Dashboard</p>

      <h3>Backend Status: {backendStatus}</h3>
      <h3>Database Status: {databaseStatus}</h3>
    </main>
  );
}

export default App;
