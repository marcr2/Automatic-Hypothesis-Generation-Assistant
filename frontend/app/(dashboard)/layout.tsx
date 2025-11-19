"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/hooks/useSession";
import { Button } from "@/components/ui/button";
import { LogOut, Clock } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { session, isAuthenticated, logout, loading } = useSession();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, loading, router]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation Bar */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Research Processor</h1>
            <p className="text-sm text-muted-foreground">
              Hypothesis Generation Platform
            </p>
          </div>

          <div className="flex items-center gap-4">
            {session && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{session.time_remaining_minutes} min remaining</span>
              </div>
            )}
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}

