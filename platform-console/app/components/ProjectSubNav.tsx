import Link from "next/link";

const tabs = [
  { segment: "database", label: "Database" },
  { segment: "auth", label: "Auth" },
  { segment: "storage", label: "Storage" },
  { segment: "functions", label: "Functions" },
  { segment: "backups", label: "Backups" },
  { segment: "iac", label: "IaC" },
];

export default function ProjectSubNav({
  name,
  active,
}: {
  name: string;
  active: string;
}) {
  return (
    <div className="mb-6 flex items-center gap-1 border-b border-border">
      {tabs.map((t) => (
        <Link
          key={t.segment}
          href={`/projects/${name}/${t.segment}`}
          className={`border-b-2 px-3 py-2 text-sm ${
            active === t.segment
              ? "border-accent text-white"
              : "border-transparent text-gray-400 hover:text-white"
          }`}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}
