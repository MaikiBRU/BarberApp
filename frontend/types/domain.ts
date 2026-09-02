export type UserRole = "admin" | "barber" | "customer";

export type AppointmentStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show";

export type PaymentMethod = "cash" | "transfer" | "card" | "mercado_pago";

export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

export type UserRead = {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  shop_id: string | null;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserRead;
};

export type CustomerProfile = {
  user_id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
};

export type ServiceRead = {
  id: string;
  shop_id: string | null;
  name: string;
  description: string | null;
  duration_minutes: number;
  price_cents: number;
  is_active: boolean;
  created_at: string;
};

export type ProductExtraRead = {
  id: string;
  shop_id: string | null;
  name: string;
  description: string | null;
  price_cents: number;
  duration_minutes: number;
  is_active: boolean;
  created_at: string;
};

export type BarberRead = {
  id: string;
  user_id: string;
  display_name: string;
  bio: string | null;
  is_active: boolean;
  email: string | null;
  phone: string | null;
};

export type PartySummary = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
};

export type ServiceSummary = {
  id: string;
  name: string;
  duration_minutes: number;
  price_cents: number;
};

export type ExtraSummary = {
  id: string;
  name: string;
  price_cents: number;
};

export type AppointmentRead = {
  id: string;
  customer: PartySummary;
  barber: PartySummary;
  service: ServiceSummary;
  extras: ExtraSummary[];
  starts_at: string;
  ends_at: string;
  duration_minutes: number;
  status: AppointmentStatus;
  service_price_cents: number;
  extras_price_cents: number;
  tip_cents: number;
  total_price_cents: number;
  payment_method: PaymentMethod | null;
  payment_status: PaymentStatus;
  notes: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;
  created_at: string;
  can_cancel: boolean;
  allowed_transitions: AppointmentStatus[];
};

export type DaySlot = {
  starts_at: string;
  ends_at: string;
};

export type BarberSlots = {
  barber_id: string;
  barber_user_id: string;
  display_name: string;
  slots: DaySlot[];
};

export type AvailabilityResponse = {
  date: string;
  service_id: string;
  duration_minutes: number;
  slot_minutes: number;
  is_open: boolean;
  barbers: BarberSlots[];
};

export type AppointmentCounts = {
  pending: number;
  confirmed: number;
  completed: number;
  cancelled: number;
  no_show: number;
};

export type DashboardSummary = {
  date: string;
  today: AppointmentCounts;
  upcoming_count: number;
  today_revenue_cents: number;
  month_revenue_cents: number;
  active_barbers: number;
  active_services: number;
  currency: string;
  next_appointments: AppointmentRead[];
};

export type BusinessHours = {
  weekday: number;
  opens_at: string;
  closes_at: string;
  is_closed: boolean;
};

export type TimeOff = {
  id: string;
  barber_id: string;
  starts_at: string;
  ends_at: string;
  reason: string | null;
};

export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
