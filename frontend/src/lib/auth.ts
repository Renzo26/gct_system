export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
  workshop_id: string | null;
}

export interface AuthWorkshop {
  id: string;
  name: string;
}

export interface AuthSession {
  user: AuthUser;
  workshop: AuthWorkshop | null;
  access_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
  workshop: AuthWorkshop | null;
}

export function setAuth(data: TokenResponse) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("auth_user", JSON.stringify(data.user));
  if (data.workshop) {
    localStorage.setItem("auth_workshop", JSON.stringify(data.workshop));
  } else {
    localStorage.removeItem("auth_workshop");
  }
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("auth_user");
  localStorage.removeItem("auth_workshop");
}

export function clearWorkshop() {
  localStorage.removeItem("auth_workshop");
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("access_token");
  const userRaw = localStorage.getItem("auth_user");
  if (!token || !userRaw) return null;
  const workshopRaw = localStorage.getItem("auth_workshop");
  try {
    return {
      access_token: token,
      user: JSON.parse(userRaw) as AuthUser,
      workshop: workshopRaw ? (JSON.parse(workshopRaw) as AuthWorkshop) : null,
    };
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

export function hasWorkshop(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("auth_workshop");
}

export function isSuperadmin(): boolean {
  return getSession()?.user.role === "SUPERADMIN";
}
