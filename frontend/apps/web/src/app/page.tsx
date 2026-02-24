import { redirect } from "next/navigation";

// Root redirect — middleware will send to /dashboard or /login based on auth
export default function RootPage() {
  redirect("/dashboard");
}
