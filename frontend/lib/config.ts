export const shopConfig = {
  name: process.env.NEXT_PUBLIC_SHOP_NAME ?? "BarberApp",
  timeZone:
    process.env.NEXT_PUBLIC_SHOP_TIMEZONE ??
    "America/Argentina/Buenos_Aires",
  currency: process.env.NEXT_PUBLIC_CURRENCY ?? "ARS",
  locale: process.env.NEXT_PUBLIC_LOCALE ?? "es-AR",
} as const;
