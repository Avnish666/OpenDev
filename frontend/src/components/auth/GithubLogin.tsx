
import { useAuth } from "../../context/AuthContext";

export default function GitHubLogin() {
  const { user, loading, error, login, logout } = useAuth();

  if (loading) {
    return <p>Checking authentication...</p>;
  }

  if (error) {
    return <p role="alert">Authentication error: {error}</p>;
  }

  if (!user) {
    return (
      <button onClick={login}>
        Sign in with GitHub
      </button>
    );
  }

  return (
    <section>
      <h2>Welcome, {user.username}</h2>

      {user.avatar_url && (
        <img
          src={user.avatar_url}
          alt={`${user.username}'s GitHub avatar`}
          width={64}
          height={64}
        />
      )}

      <p>GitHub ID: {user.github_id}</p>

      <button
        onClick={() => {
          void logout().catch(console.error);
        }}
      >
        Log out
      </button>
    </section>
  );
}
