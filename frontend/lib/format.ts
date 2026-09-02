import { shopConfig } from "@/lib/config";

const { locale, timeZone, currency } = shopConfig;

const currencyFormatter = new Intl.NumberFormat(locale, {
  style: "currency",
  currency,
  maximumFractionDigits: 0,
});

// 24-hour clock: an "05:00 p. m." slot label reads as a typo next to
// opening hours written as 09:00-19:00.
const timeFormatter = new Intl.DateTimeFormat(locale, {
  timeZone,
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const dayFormatter = new Intl.DateTimeFormat(locale, {
  timeZone,
  weekday: "long",
  day: "numeric",
  month: "long",
});

const shortDayFormatter = new Intl.DateTimeFormat(locale, {
  timeZone,
  day: "2-digit",
  month: "2-digit",
});

const dateTimeFormatter = new Intl.DateTimeFormat(locale, {
  timeZone,
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** Format a price stored in cents. */
export function formatPrice(cents: number): string {
  return currencyFormatter.format(cents / 100);
}

/** Format an ISO instant as a shop-local time, e.g. `14:30`. */
export function formatTime(iso: string): string {
  return timeFormatter.format(new Date(iso));
}

/** Format an ISO instant as a full shop-local day. */
export function formatDay(iso: string): string {
  return dayFormatter.format(new Date(iso));
}

/** Format an ISO instant compactly, e.g. `12/09`. */
export function formatShortDay(iso: string): string {
  return shortDayFormatter.format(new Date(iso));
}

/** Format an ISO instant as day plus time. */
export function formatDateTime(iso: string): string {
  return dateTimeFormatter.format(new Date(iso));
}

/** Format a duration in minutes, e.g. `1 h 15 min`. */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

/** Return today's calendar date in the shop timezone as `YYYY-MM-DD`. */
export function shopToday(): string {
  return toShopDateString(new Date());
}

/** Convert a Date into a shop-local `YYYY-MM-DD` string. */
export function toShopDateString(value: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(value);
  return parts;
}

/** Return the `YYYY-MM-DD` string `days` after the given date string. */
export function addDays(dateString: string, days: number): string {
  const [year, month, day] = dateString.split("-").map(Number);
  const base = new Date(Date.UTC(year, month - 1, day));
  base.setUTCDate(base.getUTCDate() + days);
  return base.toISOString().slice(0, 10);
}

/** Format a `YYYY-MM-DD` string as a readable shop-local day. */
export function formatDateString(dateString: string): string {
  const [year, month, day] = dateString.split("-").map(Number);
  return dayFormatter.format(new Date(Date.UTC(year, month - 1, day, 12)));
}

/** Convert a major-unit amount typed by a person into cents. */
export function toCents(amount: string | number): number {
  const value = typeof amount === "number" ? amount : Number(amount);
  if (!Number.isFinite(value) || value < 0) {
    return 0;
  }
  return Math.round(value * 100);
}

/** Convert stored cents back into a major-unit value for an input. */
export function toMajorUnits(cents: number): string {
  return (cents / 100).toString();
}
