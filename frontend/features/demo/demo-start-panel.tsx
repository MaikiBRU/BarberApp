import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FormMessage, SkeletonRows } from "@/components/ui/states";
import { routes } from "@/lib/routes";
import type { DemoLimits } from "@/types/domain";

type DemoStartPanelProps = {
  limits?: DemoLimits;
  isLoadingLimits: boolean;
  isDisabled: boolean;
  isStarting: boolean;
  notice: string | null;
  error: string | null;
  onStart: () => void;
};

export function DemoStartPanel({
  limits,
  isLoadingLimits,
  isDisabled,
  isStarting,
  notice,
  error,
  onStart,
}: DemoStartPanelProps) {
  return (
    <>
      <h2 className="text-2xl font-semibold tracking-tight">Probar la demo</h2>
      <p className="mt-2 text-sm text-ink-muted">
        Sin registro, sin email y sin contraseña. Se crea una barbería
        temporal solo para vos, con servicios, barberos y turnos ya cargados,
        y podés recorrerla como cliente, barbero o administrador.
      </p>

      {notice ? <p className="mt-4 text-sm text-accent">{notice}</p> : null}
      {error ? (
        <div className="mt-4">
          <FormMessage tone="error">{error}</FormMessage>
        </div>
      ) : null}

      {isDisabled ? (
        <p className="mt-5 text-sm text-ink-muted">
          La demo pública está desactivada en este momento.
        </p>
      ) : (
        <Button
          className="mt-5 w-full py-3 text-base"
          isLoading={isStarting}
          onClick={onStart}
        >
          {isStarting ? "Preparando tu barbería..." : "Comenzar demo"}
        </Button>
      )}

      <div className="mt-5 rounded-md border border-line bg-surface-muted p-4 text-xs text-ink-muted">
        <p className="font-semibold">Límites de la sesión</p>
        {isLoadingLimits ? (
          <SkeletonRows rows={1} />
        ) : limits ? (
          <ul className="mt-2 grid gap-1.5">
            <li>Duración: {limits.session_ttl_minutes} minutos</li>
            <li>Inactividad: {limits.idle_timeout_minutes} minutos</li>
            <li>Turnos: hasta {limits.max_appointments}</li>
            <li>Cambios de configuración: hasta {limits.max_writes}</li>
          </ul>
        ) : (
          <p className="mt-2">
            No se pudo contactar el servidor. Reintentá en unos segundos.
          </p>
        )}
      </div>

      <p className="mt-4 text-xs text-ink-muted">
        La sesión es temporal y está aislada del resto. Todo lo que generes se
        borra al expirar, y podés borrarlo antes cuando quieras.
      </p>

      <div className="mt-5 border-t border-line pt-4">
        <p className="text-sm font-medium">¿Querés ver la aplicación real?</p>
        <p className="mt-1 text-xs text-ink-muted">
          La misma aplicación, con cuentas de verdad y datos que persisten.
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <Link className="flex-1" href={routes.login}>
            <Button className="w-full" size="sm" variant="secondary">
              Entrar con mi cuenta
            </Button>
          </Link>
          <Link className="flex-1" href={routes.register}>
            <Button className="w-full" size="sm" variant="secondary">
              Crear una cuenta
            </Button>
          </Link>
        </div>
      </div>
    </>
  );
}
