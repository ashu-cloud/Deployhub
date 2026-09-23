/**
 * DeployHub API Integration Client
 * Connects Next.js frontend to FastAPI backend microservices
 */

export interface Project {
  id: string;
  user_id: string;
  repo_name: string;
  repo_url: string;
  status: "active" | "archived" | "building";
  created_at: string;
  framework?: string;
  live_url?: string;
  latest_deployment?: {
    id: string;
    git_commit: string;
    git_branch: string;
    status: string;
    deployed_at?: string;
  };
}

export interface Deployment {
  id: string;
  project_id: string;
  git_commit: string;
  git_branch: string;
  status: "queued" | "building" | "uploading" | "live" | "failed";
  s3_path?: string;
  deployment_number: number;
  deployed_at?: string;
  created_at: string;
}

export interface EnvVar {
  id: string;
  key: string;
  created_at: string;
}

// The access token lives in memory only for the lifetime of this module --
// never in localStorage/sessionStorage, which would leave it readable by any
// injected script (XSS) for as long as the browser keeps the storage around.
// It is intentionally lost on a full page reload; bootstrapSession() re-mints
// it from the HttpOnly refresh-token cookie.
let inMemoryAuthToken: string | null = null;

export function getAuthToken(): string | null {
  return inMemoryAuthToken;
}

export function setAuthToken(token: string): void {
  inMemoryAuthToken = token;
}

export function clearAuthToken(): void {
  inMemoryAuthToken = null;
}

export async function bootstrapSession(): Promise<boolean> {
  try {
    const res = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) {
      clearAuthToken();
      return false;
    }
    const data = await res.json();
    if (data?.access_token) {
      setAuthToken(data.access_token);
      return true;
    }
  } catch (err) {
    console.warn("Could not refresh session:", err);
  }
  clearAuthToken();
  return false;
}

export async function logout(): Promise<void> {
  try {
    await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
  } catch {
    // ignore -- local token is cleared either way
  }
  clearAuthToken();
}

async function fetchWithAuth(url: string, options: RequestInit = {}, retryOn401 = true): Promise<Response> {
  if (!inMemoryAuthToken) {
    await bootstrapSession();
  }

  const headers = new Headers(options.headers || {});
  if (!headers.has("Authorization") && inMemoryAuthToken) {
    headers.set("Authorization", `Bearer ${inMemoryAuthToken}`);
  }
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.status === 401 && retryOn401) {
      const refreshed = await bootstrapSession();
      if (refreshed && inMemoryAuthToken) {
        return fetchWithAuth(url, options, false);
      }
    }

    return res;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}


// ==========================================
// PROJECTS API
// ==========================================

export async function listProjects(): Promise<Project[]> {
  try {
    const res = await fetchWithAuth("/api/v1/projects/");
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    }
  } catch (err) {
    console.warn("Backend project service unreachable:", err);
  }
  return [];
}

export async function getProject(projectId: string): Promise<Project | null> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Could not fetch project ${projectId} from backend:`, err);
  }
  return null;
}


export async function createProject(data: {
  repo_name: string;
  repo_url: string;
  framework?: string;
  env_vars?: Record<string, string>;
}): Promise<Project> {
  const res = await fetchWithAuth("/api/v1/projects/", {
    method: "POST",
    body: JSON.stringify({
      repo_name: data.repo_name,
      repo_url: data.repo_url,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Create project failed (${res.status})`);
  }

  const created = await res.json();

  if (data.env_vars && Object.keys(data.env_vars).length > 0) {
    for (const [key, value] of Object.entries(data.env_vars)) {
      await addProjectEnvVar(created.id, key, value);
    }
  }

  await triggerDeployment(created.id, "main");
  return created;
}

export async function deleteProject(projectId: string): Promise<boolean> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ==========================================
// ENVIRONMENT VARIABLES API
// ==========================================

export async function getProjectEnvVars(projectId: string): Promise<EnvVar[]> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}/env-vars`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Could not list env vars:", e);
  }
  return [];
}

export async function addProjectEnvVar(projectId: string, key: string, value: string): Promise<boolean> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}/env-vars`, {
      method: "POST",
      body: JSON.stringify({ key, value }),
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

// ==========================================
// DEPLOYMENTS API
// ==========================================

export async function getDeployments(projectId: string): Promise<Deployment[]> {
  try {
    const res = await fetchWithAuth(`/api/v1/deployments/${projectId}`);
    if (res.ok) {
      const list = await res.json();
      return Array.isArray(list) ? list : [];
    }
  } catch (e) {
    console.warn("Could not list deployments:", e);
  }
  return [];
}

export async function triggerDeployment(
  projectId: string,
  branch: string = "main",
  commitSha: string = "HEAD"
): Promise<{ id: string; status: string }> {
  const params = new URLSearchParams({ branch, commit_sha: commitSha });
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/deploy?${params.toString()}`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Deploy failed (${res.status})`);
  }
  return await res.json();
}

export async function rollbackDeployment(deploymentId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetchWithAuth(`/api/v1/deployments/${deploymentId}/rollback`, {
    method: "POST",
  });
  if (!res.ok) {
    const detail = await res.text();
    return { success: false, message: detail || `Rollback failed (${res.status})` };
  }
  const data = await res.json();
  return { success: true, message: data.message || "Rollback successful" };
}

export async function getGithubRepos(): Promise<any[]> {
  try {
    const res = await fetchWithAuth("/api/v1/auth/github/repos");
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    }
  } catch (err) {
    console.warn("Could not fetch GitHub repos:", err);
  }
  return [];
}


// ==========================================
// CUSTOM DOMAINS API
// ==========================================

export interface CustomDomain {
  id: string;
  project_id: string;
  domain: string;
  verified: boolean;
  created_at: string;
}

export async function listCustomDomains(projectId: string): Promise<CustomDomain[]> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}/domains`);
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    }
  } catch (err) {
    console.warn(`Could not list custom domains for project ${projectId}:`, err);
  }
  return [];
}

export async function addCustomDomain(projectId: string, domain: string): Promise<CustomDomain | null> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}/domains`, {
      method: "POST",
      body: JSON.stringify({ domain }),
    });
    if (res.ok) {
      return await res.json();
    } else {
      const error = await res.text();
      throw new Error(error);
    }
  } catch (err) {
    console.error("Failed to add custom domain:", err);
    throw err;
  }
}

export async function deleteCustomDomain(projectId: string, domainId: string): Promise<boolean> {
  try {
    const res = await fetchWithAuth(`/api/v1/projects/${projectId}/domains/${domainId}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch (err) {
    console.warn(`Could not delete custom domain ${domainId}:`, err);
    return false;
  }
}
