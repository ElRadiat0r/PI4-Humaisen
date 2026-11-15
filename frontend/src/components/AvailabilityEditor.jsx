import { useState } from "react";
import { DAYS } from "../experts";

export default function AvailabilityEditor({ profile, onChange }) {
  const [day, setDay] = useState(DAYS[0]);
  const [start, setStart] = useState("09:00");
  const [end, setEnd] = useState("12:00");
  const [date, setDate] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  function addWeekly(e) {
    e.preventDefault();
    if (end <= start) {
      setError("End time must be after start time.");
      return;
    }
    setError("");
    const slot = { id: String(Date.now()), day, start, end };
    onChange({ ...profile, weekly: [...profile.weekly, slot] });
  }

  function removeWeekly(id) {
    onChange({ ...profile, weekly: profile.weekly.filter((s) => s.id !== id) });
  }

  function addUnavailable(e) {
    e.preventDefault();
    if (!date) return;
    const item = { id: String(Date.now()), date, note };
    onChange({ ...profile, unavailable: [...profile.unavailable, item] });
    setDate("");
    setNote("");
  }

  function removeUnavailable(id) {
    onChange({ ...profile, unavailable: profile.unavailable.filter((u) => u.id !== id) });
  }

  const sortedWeekly = [...profile.weekly].sort(
    (a, b) => DAYS.indexOf(a.day) - DAYS.indexOf(b.day) || a.start.localeCompare(b.start)
  );

  return (
    <div>
      <h3>Weekly availability</h3>
      <form onSubmit={addWeekly} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <select value={day} onChange={(e) => setDay(e.target.value)}>
          {DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <input type="time" value={start} onChange={(e) => setStart(e.target.value)} required />
        <input type="time" value={end} onChange={(e) => setEnd(e.target.value)} required />
        <button type="submit">Add slot</button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {sortedWeekly.length === 0 && <p>No weekly slot yet.</p>}
      <ul>
        {sortedWeekly.map((s) => (
          <li key={s.id}>
            {s.day} {s.start} – {s.end}{" "}
            <button onClick={() => removeWeekly(s.id)}>Remove</button>
          </li>
        ))}
      </ul>

      <h3>One-off unavailability</h3>
      <form onSubmit={addUnavailable} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        <input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <button type="submit">Add</button>
      </form>
      {profile.unavailable.length === 0 && <p>No unavailable date.</p>}
      <ul>
        {profile.unavailable.map((u) => (
          <li key={u.id}>
            {u.date} {u.note && `– ${u.note}`}{" "}
            <button onClick={() => removeUnavailable(u.id)}>Remove</button>
          </li>
        ))}
      </ul>
    </div>
  );
}