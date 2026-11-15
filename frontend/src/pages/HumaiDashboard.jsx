import { useState } from "react";
import { getCurrentUser } from "../auth";
import { getProfile, saveProfile, LEVELS } from "../experts";
import AvailabilityEditor from "../components/AvailabilityEditor";

export default function HumaiDashboard() {
  const user = getCurrentUser();
  const [profile, setProfile] = useState(() => getProfile(user.email));
  const [skillsText, setSkillsText] = useState(profile.skills.join(", "));
  const [message, setMessage] = useState("");

  // 常用时区的简单列表，加上浏览器检测到的那个
  const timezones = [...new Set([profile.timezone, "Europe/Paris", "Europe/London", "America/New_York", "Asia/Shanghai", "UTC"])];

  function handleSave(e) {
    e.preventDefault();
    const skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
    setProfile(saveProfile({ ...profile, skills }));
    setMessage("Profile saved.");
  }

  // 可用时间一改动就自动保存
  function handleAvailabilityChange(updated) {
    setProfile(saveProfile(updated));
  }

  return (
    <div style={{ maxWidth: 720, margin: "24px auto", padding: "0 16px" }}>
      <h1>My HumAI space</h1>
      <p>
        Verification status:{" "}
        <strong>{profile.verified ? "Verified ✅" : "Pending verification ⏳"}</strong>
      </p>

      <h2>Profile</h2>
      <form onSubmit={handleSave} style={{ display: "grid", gap: 12 }}>
        <input placeholder="Full name" value={profile.fullName}
          onChange={(e) => setProfile({ ...profile, fullName: e.target.value })} required />

        <select value={profile.level}
          onChange={(e) => setProfile({ ...profile, level: e.target.value })}>
          {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>

        <input placeholder="Skills, separated by commas (e.g. Python, Finance)" value={skillsText}
          onChange={(e) => setSkillsText(e.target.value)} />

        <select value={profile.timezone}
          onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}>
          {timezones.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        <button type="submit">Save profile</button>
        {message && <p style={{ color: "green" }}>{message}</p>}
      </form>

      <h2>Availability</h2>
      <AvailabilityEditor profile={profile} onChange={handleAvailabilityChange} />
    </div>
  );
}