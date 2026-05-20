export function download(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const keys = Object.keys(rows[0]);
  const header = keys.join(",");
  const body = rows
    .map((r) =>
      keys
        .map((k) => {
          const v = r[k];
          const s = v == null ? "" : String(v);
          return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
        })
        .join(","),
    )
    .join("\n");
  return `${header}\n${body}`;
}

export function toMarkdownTable(rows: Record<string, unknown>[], title: string): string {
  if (rows.length === 0) return `# ${title}\n\nNo data.\n`;
  const keys = Object.keys(rows[0]);
  const header = `| ${keys.join(" | ")} |`;
  const sep = `| ${keys.map(() => "---").join(" | ")} |`;
  const body = rows
    .map((r) => {
      const vals = keys.map((k) => {
        const v = r[k];
        return v == null ? "—" : String(v);
      });
      return `| ${vals.join(" | ")} |`;
    })
    .join("\n");
  return `# ${title}\n\n${header}\n${sep}\n${body}\n`;
}
