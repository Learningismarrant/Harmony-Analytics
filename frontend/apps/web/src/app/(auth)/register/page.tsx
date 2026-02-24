"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@harmony/api";
import { useAuthStore } from "@/store/auth.store";
import type { UserRole, YachtPosition } from "@harmony/types";

const POSITIONS: YachtPosition[] = [
  "Captain",
  "First Mate",
  "Bosun",
  "Deckhand",
  "Chief Engineer",
  "2nd Engineer",
  "Chief Stewardess",
  "Stewardess",
  "Chef",
];

const INPUT_CLS =
  "w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 " +
  "text-sm text-text-primary placeholder:text-muted " +
  "focus:outline-none focus:border-brand-primary transition-colors";

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [role, setRole] = useState<"employer" | "crew">("employer");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [position, setPosition] = useState<YachtPosition | "">("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const token =
        role === "employer"
          ? await authApi.registerEmployer({
              email,
              password,
              name,
              company_name: companyName || undefined,
            })
          : await authApi.registerCrew({
              email,
              password,
              name,
              position_targeted: (position as YachtPosition) || undefined,
            });

      login({
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
        role: token.role as UserRole,
        userId: token.user_id,
        profileId: token.profile_id,
        name,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      const detail = (
        err as { response?: { data?: { detail?: string } } }
      ).response?.data?.detail;
      setError(detail ?? "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-ocean-gradient flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-brand-primary/20 border border-brand-primary/40 flex items-center justify-center">
              <span className="text-brand-primary font-bold text-sm">H</span>
            </div>
            <span className="text-xl font-semibold text-text-primary">Harmony</span>
          </div>
          <p className="text-muted text-sm">Create your account</p>
        </div>

        {/* Card */}
        <div className="card">
          <h1 className="text-lg font-semibold mb-4">Create account</h1>

          {/* Role selector */}
          <div className="flex rounded-lg bg-bg-elevated p-1 mb-6">
            <button
              type="button"
              onClick={() => setRole("employer")}
              className={`flex-1 text-sm py-1.5 rounded-md transition-colors ${
                role === "employer"
                  ? "bg-brand-primary text-white font-medium"
                  : "text-muted hover:text-text-primary"
              }`}
            >
              Employer
            </button>
            <button
              type="button"
              onClick={() => setRole("crew")}
              className={`flex-1 text-sm py-1.5 rounded-md transition-colors ${
                role === "crew"
                  ? "bg-brand-primary text-white font-medium"
                  : "text-muted hover:text-text-primary"
              }`}
            >
              Crew member
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full name */}
            <div>
              <label className="block text-sm text-muted mb-1.5" htmlFor="name">
                Full name
              </label>
              <input
                id="name"
                type="text"
                required
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={INPUT_CLS}
                placeholder="Jane Doe"
              />
            </div>

            {/* Employer-only: company */}
            {role === "employer" && (
              <div>
                <label className="block text-sm text-muted mb-1.5" htmlFor="company">
                  Company{" "}
                  <span className="text-xs opacity-60">(optional)</span>
                </label>
                <input
                  id="company"
                  type="text"
                  autoComplete="organization"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className={INPUT_CLS}
                  placeholder="Pacific Yachting"
                />
              </div>
            )}

            {/* Crew-only: position */}
            {role === "crew" && (
              <div>
                <label className="block text-sm text-muted mb-1.5" htmlFor="position">
                  Position{" "}
                  <span className="text-xs opacity-60">(optional)</span>
                </label>
                <select
                  id="position"
                  value={position}
                  onChange={(e) => setPosition(e.target.value as YachtPosition | "")}
                  className={INPUT_CLS}
                >
                  <option value="">Select a position</option>
                  {POSITIONS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm text-muted mb-1.5" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={INPUT_CLS}
                placeholder="captain@yachtco.com"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm text-muted mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={INPUT_CLS}
                placeholder="••••••••"
              />
              <p className="text-xs text-muted mt-1">Minimum 6 characters</p>
            </div>

            {error && (
              <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-4">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
