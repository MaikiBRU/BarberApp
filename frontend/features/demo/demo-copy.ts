export const CAPABILITIES = [
  "Reservar un turno contra disponibilidad real, no contra una lista fija.",
  "Ver cómo un turno tomado desaparece de la grilla al instante.",
  "Confirmar, completar o cancelar turnos como barbero.",
  "Administrar servicios, extras, barberos y horarios de atención.",
  "Mirar un panel con métricas calculadas sobre los turnos cargados.",
] as const;

export const STACK = [
  "Next.js",
  "React",
  "TypeScript",
  "TailwindCSS",
  "TanStack Query",
  "FastAPI",
  "SQLAlchemy",
  "PostgreSQL",
  "Alembic",
  "Docker",
] as const;

export const HIGHLIGHTS = [
  { value: "3", label: "roles con permisos distintos" },
  { value: "15 min", label: "grilla de horarios configurable" },
  { value: "143", label: "pruebas automatizadas" },
] as const;
