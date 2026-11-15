import { Navigate } from "react-router-dom";
import { getCurrentUser, homeForRole } from "../auth";

export default function ProtectedRoute({ role, children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homeForRole[user.role]} replace />;
  return children;
}