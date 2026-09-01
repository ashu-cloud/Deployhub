import { RequireAuth } from "@/components/RequireAuth";

export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
