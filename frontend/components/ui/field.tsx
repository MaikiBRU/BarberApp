"use client";

import { useId } from "react";
import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/cn";

const control =
  "w-full rounded-md border bg-surface px-3 py-2.5 text-sm " +
  "placeholder:text-ink-muted/70 disabled:opacity-60 sm:py-2";

function controlClass(hasError: boolean): string {
  return cn(
    control,
    hasError ? "border-danger" : "border-line-strong",
  );
}

type FieldShellProps = {
  label: string;
  error?: string;
  hint?: string;
  children: (props: {
    id: string;
    describedBy: string | undefined;
    invalid: boolean;
  }) => ReactNode;
};

function FieldShell({ label, error, hint, children }: FieldShellProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy =
    [errorId, hintId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium" htmlFor={id}>
        {label}
      </label>
      {children({ id, describedBy, invalid: Boolean(error) })}
      {hint && !error ? (
        <p className="text-xs text-ink-muted" id={hintId}>
          {hint}
        </p>
      ) : null}
      {error ? (
        <p className="text-xs font-medium text-danger" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

type InputFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  hint?: string;
};

export function InputField({
  label,
  error,
  hint,
  className,
  ...props
}: InputFieldProps) {
  return (
    <FieldShell error={error} hint={hint} label={label}>
      {({ id, describedBy, invalid }) => (
        <input
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
          className={cn(controlClass(invalid), className)}
          id={id}
          {...props}
        />
      )}
    </FieldShell>
  );
}

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  error?: string;
  hint?: string;
};

export function SelectField({
  label,
  error,
  hint,
  className,
  children,
  ...props
}: SelectFieldProps) {
  return (
    <FieldShell error={error} hint={hint} label={label}>
      {({ id, describedBy, invalid }) => (
        <select
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
          className={cn(controlClass(invalid), className)}
          id={id}
          {...props}
        >
          {children}
        </select>
      )}
    </FieldShell>
  );
}

type TextareaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  error?: string;
  hint?: string;
};

export function TextareaField({
  label,
  error,
  hint,
  className,
  ...props
}: TextareaFieldProps) {
  return (
    <FieldShell error={error} hint={hint} label={label}>
      {({ id, describedBy, invalid }) => (
        <textarea
          aria-describedby={describedBy}
          aria-invalid={invalid || undefined}
          className={cn(controlClass(invalid), "min-h-24", className)}
          id={id}
          {...props}
        />
      )}
    </FieldShell>
  );
}
