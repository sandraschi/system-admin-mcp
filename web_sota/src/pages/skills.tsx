import { BookOpen } from "lucide-react";
import { useEffect, useState } from "react";

interface Skill {
  name: string;
  description: string;
}

export function Skills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/skills")
      .then((r) => r.json())
      .then((d) => {
        if (d.skills?.length) setSkills(d.skills);
        else setError("No skills found");
      })
      .catch(() => setError("Failed to load skills"));
  }, []);

  return (
    <div data-testid="skills-page" className="space-y-6">
      <div className="flex items-center gap-3">
        <BookOpen className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Skills
          </h1>
          <p className="text-slate-400 text-sm">
            Agent instructions exposed by this server via skill:// resources
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {skills.map((skill) => (
          <div
            key={skill.name}
            className="rounded-2xl border border-slate-800 bg-slate-950/50 p-5"
          >
            <h2 className="text-lg font-bold text-white font-mono">
              {skill.name}
            </h2>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              {skill.description}
            </p>
          </div>
        ))}
      </div>

      {skills.length === 0 && !error && (
        <p className="text-sm text-slate-500 py-8 text-center">
          Loading skills...
        </p>
      )}
    </div>
  );
}
