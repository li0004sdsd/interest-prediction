"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";

export default function NavBar() {
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <nav className="bg-indigo-700 text-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <span className="font-bold text-lg tracking-tight">InterestAI</span>
        <Link href="/dashboard" className="text-sm hover:text-indigo-200 transition-colors">
          Dashboard
        </Link>
        <Link href="/behaviors" className="text-sm hover:text-indigo-200 transition-colors">
          Behaviors
        </Link>
      </div>
      <button
        onClick={handleLogout}
        className="text-sm bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 rounded transition-colors"
      >
        Logout
      </button>
    </nav>
  );
}
