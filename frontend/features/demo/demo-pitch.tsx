import {
  CAPABILITIES,
  HIGHLIGHTS,
  STACK,
} from "@/features/demo/demo-copy";

export function DemoPitch() {
  return (
    <>
      <p className="text-xs font-semibold uppercase tracking-wide text-accent">
        Demo de portafolio
      </p>
      <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
        BarberApp
      </h1>
      <p className="mt-4 text-base leading-relaxed text-ink-muted">
        Una barbería pierde turnos cuando dos personas escriben al mismo
        tiempo. BarberApp calcula la disponibilidad en el servidor, revalida
        el horario antes de guardar y deja que la base de datos rechace
        cualquier superposición que se le escape.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        {HIGHLIGHTS.map((item) => (
          <div
            className="rounded-md border border-line bg-surface-muted px-4 py-3"
            key={item.label}
          >
            <p className="text-xl font-semibold text-accent">{item.value}</p>
            <p className="mt-1 text-xs leading-snug text-ink-muted">
              {item.label}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-md border border-line bg-surface-muted p-4 sm:p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
          Qué vas a poder hacer
        </p>
        <ul className="mt-3 grid gap-2.5 text-sm text-ink-muted">
          {CAPABILITIES.map((line) => (
            <li className="flex gap-2.5" key={line}>
              <span
                aria-hidden="true"
                className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent"
              />
              <span>{line}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
          Stack
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {STACK.map((tech) => (
            <li
              className="rounded-md border border-line px-2.5 py-1 text-xs text-ink-muted"
              key={tech}
            >
              {tech}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
