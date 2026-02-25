"use client";

import { useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { authApi } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import type { UserRole } from "@harmony/types";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const token = await authApi.login(email, password);
      login({
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
        role: token.role as UserRole,
        userId: token.user_id,
        profileId: token.profile_id,
        name: email,
      });
      const next = searchParams.get("next") ?? "/dashboard";
      router.push(next);
    } catch {
      setError("Invalid email or password.");
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
          <p className="text-muted text-sm">Employer dashboard</p>
        </div>

        {/* Card */}
        <div className="card">
          <h1 className="text-lg font-semibold mb-6">Sign in</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
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
                className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2
                           text-sm text-text-primary placeholder:text-muted
                           focus:outline-none focus:border-brand-primary transition-colors"
                placeholder="captain@yachtco.com"
              />
            </div>

            <div>
              <label className="block text-sm text-muted mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2
                           text-sm text-text-primary placeholder:text-muted
                           focus:outline-none focus:border-brand-primary transition-colors"
                placeholder="••••••••"
              />
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
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-4">
            New here?{" "}
            <Link href="/register" className="text-brand-primary hover:underline">
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
