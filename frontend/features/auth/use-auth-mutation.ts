"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { toFieldErrors, toMessage } from "@/lib/error-messages";
import { routes } from "@/lib/routes";
import { useSessionStore } from "@/store/session-store";
import type { AuthResponse } from "@/types/domain";

type Submit = () => Promise<AuthResponse>;

/**
 * Shared submit handling for the login and register forms: one place
 * for the pending flag, the error mapping and the post-login redirect.
 */
export function useAuthSubmit() {
  const router = useRouter();
  const setSession = useSessionStore((state) => state.setSession);
  const [isSubmitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function submit(run: Submit) {
    setSubmitting(true);
    setMessage(null);
    setFieldErrors({});

    try {
      const response = await run();
      setSession(
        response.access_token,
        {
          id: response.user.id,
          email: response.user.email,
          role: response.user.role,
        },
        response.expires_in,
      );
      router.push(
        response.user.role === "customer"
          ? routes.booking
          : routes.dashboard,
      );
      router.refresh();
    } catch (error) {
      setMessage(toMessage(error));
      setFieldErrors(toFieldErrors(error));
      setSubmitting(false);
    }
  }

  return { submit, isSubmitting, message, fieldErrors };
}
