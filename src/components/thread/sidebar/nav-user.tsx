"use client";

import { useState } from "react";
import { ChevronsUpDown, LogOut, Loader2 } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthContext } from "@/providers/Auth";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export function NavUser() {
  const { user: authUser, signOut, isAuthenticated } = useAuthContext();
  const router = useRouter();
  const [isSigningOut, setIsSigningOut] = useState(false);

  // Use auth user if available, otherwise use default user
  const displayUser = authUser
    ? {
        name: authUser.displayName || authUser.email?.split("@")[0] || "User",
        email: authUser.email || "",
        avatar: authUser.avatarUrl || undefined,
      }
    : {
        name: "Guest",
        email: "Not signed in",
        avatar: undefined,
      };

  const handleSignOut = async () => {
    try {
      setIsSigningOut(true);
      const { error } = await signOut();

      if (error) {
        console.error("Error signing out:", error);
        toast.error("Error signing out");
        return;
      }

      router.push("/signin");
    } catch (err) {
      console.error("Error during sign out:", err);
      toast.error("Error signing out");
    } finally {
      setIsSigningOut(false);
    }
  };

  const handleSignIn = () => {
    router.push("/signin");
  };

  return (
    <div className="border-sidebar-border border-t p-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="hover:bg-sidebar-accent h-auto w-full justify-start gap-3 p-3"
          >
            <Avatar className="h-8 w-8 rounded-lg">
              {displayUser.avatar && (
                <AvatarImage src={displayUser.avatar} alt={displayUser.name} />
              )}
              <AvatarFallback className="rounded-lg">
                {displayUser.name.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-1 flex-col items-start text-left text-sm">
              <span className="truncate font-semibold">{displayUser.name}</span>
              <span className="text-muted-foreground truncate text-xs">
                {displayUser.email}
              </span>
            </div>
            <ChevronsUpDown className="ml-auto size-4 shrink-0" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className="w-[--radix-dropdown-menu-trigger-width] min-w-56"
          side="right"
          align="end"
          sideOffset={4}
        >
          <DropdownMenuLabel className="p-0 font-normal">
            <div className="flex items-center gap-2 px-2 py-1.5">
              <Avatar className="h-8 w-8 rounded-lg">
                {displayUser.avatar && (
                  <AvatarImage src={displayUser.avatar} alt={displayUser.name} />
                )}
                <AvatarFallback className="rounded-lg">
                  {displayUser.name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-1 flex-col text-left text-sm">
                <span className="truncate font-semibold">
                  {displayUser.name}
                </span>
                <span className="text-muted-foreground truncate text-xs">
                  {displayUser.email}
                </span>
              </div>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {isAuthenticated ? (
            <DropdownMenuItem onClick={handleSignOut} disabled={isSigningOut}>
              {isSigningOut ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing out...
                </>
              ) : (
                <>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </>
              )}
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem onClick={handleSignIn}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign in
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
