import { LinkButton } from "@/components/ui/button";
import { routes } from "@/lib/routes";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center sm:px-6">
      <h1 className="text-2xl font-semibold">Pagina no encontrada</h1>
      <p className="mt-2 text-sm text-ink-muted">
        El enlace que seguiste no existe o fue movido.
      </p>
      <LinkButton className="mt-6" href={routes.home}>
        Volver al inicio
      </LinkButton>
    </div>
  );
}
