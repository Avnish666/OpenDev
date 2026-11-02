
import { useEffect, useState } from "react";

import GitHubLogin from "./components/auth/GithubLogin";

export default function App() {
  return (
    <main style={{ padding: 40, fontFamily: "Arial" }}>
      <h1>Open Source Funding Platform</h1>

      <p>Fund open source. Reward backers. Prove progress.</p>

      <GitHubLogin />
    </main>
  );
}

