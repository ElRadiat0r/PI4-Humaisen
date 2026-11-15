import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register, login, homeForRole } from "../auth";

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("client");
  const [error, setError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const result = register(email, password, role);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    const logged = login(email, password);
    navigate(homeForRole[logged.user.role]);
  }

  return (
    <div style={{ maxWidth: 360, margin: "40px auto" }}>
      <h1>Register</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <input type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password (min 6 characters)" value={password}
          onChange={(e) => setPassword(e.target.value)} minLength={6} required />
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="client">I am a Client</option>
          <option value="humai">I am a HumAI expert</option>
        </select>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit">Create account</button>
      </form>
      <p>Already registered? <Link to="/login">Log in</Link></p>
    </div>
  );
}